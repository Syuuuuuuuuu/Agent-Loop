"""文本向量化(embedding)与相似度,供套路库 top-k 语义检索使用。

两种后端,按 config 自动选择,契约统一(都返回 list[float] 稠密向量):
- ark:调用火山引擎豆包 multimodal embedding 模型(真实语义向量)。
- local:零依赖的本地 hash 向量(离线/降级用,基于中文二元组特征哈希)。

设计原则:ark 调用失败(欠费/断网等)时自动降级到 local,绝不因向量化失败
中断整个对话;调用方只需 embed()/cosine(),无需关心用了哪个后端。
"""
from __future__ import annotations
import hashlib
import json
import math
import urllib.request
import urllib.error

from .embedding import _tokens  # 复用已有的中文二元组分词
from .. import config

_LOCAL_DIM = 1024
_LOCAL_SIG = "local:hash-v1"


def _local_embed(text: str) -> list[float]:
    """本地特征哈希稠密向量(离线可跑,零依赖)。"""
    vec = [0.0] * _LOCAL_DIM
    for tok in _tokens(text):
        # 用稳定哈希(而非内置 hash),保证跨进程重启可复现,存库向量重启后仍可比对
        idx = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16) % _LOCAL_DIM
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def _ark_embed(text: str) -> list[float]:
    """调用火山引擎 multimodal embedding 接口,对纯文本返回稠密向量。"""
    url = config.ARK_BASE_URL.rstrip("/") + "/embeddings/multimodal"
    payload = json.dumps({
        "model": config.ARK_EMBED_MODEL,
        "input": [{"type": "text", "text": text or ""}],
        "encoding_format": "float",
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.ARK_API_KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    data = body.get("data")
    # 该接口 data 可能是对象也可能是数组,两种都兼容
    if isinstance(data, list):
        data = data[0] if data else {}
    embedding = (data or {}).get("embedding")
    if not embedding:
        raise ValueError(f"embedding 响应缺少向量:{body}")
    return [float(x) for x in embedding]


def _use_ark() -> bool:
    return config.LLM_PROVIDER == "ark" and bool(config.ARK_API_KEY)


def signature() -> str:
    """当前向量后端签名(存库标记,后端切换时据此判断是否需重算)。"""
    return f"ark:{config.ARK_EMBED_MODEL}" if _use_ark() else _LOCAL_SIG


def embed(text: str) -> tuple[list[float], str]:
    """返回 (向量, 后端签名)。ark 失败时自动降级到 local。"""
    if _use_ark():
        try:
            return _ark_embed(text), f"ark:{config.ARK_EMBED_MODEL}"
        except (urllib.error.URLError, ValueError, KeyError, TimeoutError, OSError):
            # 欠费/断网/格式异常等:降级本地向量,保证对话不中断
            return _local_embed(text), _LOCAL_SIG
    return _local_embed(text), _LOCAL_SIG


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
