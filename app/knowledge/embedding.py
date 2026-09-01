"""轻量本地 embedding(零外部依赖,离线可跑)。

做法:中文按"字符二元组(bigram)"+ 英文/数字按词,构造稀疏 TF 向量,
检索时用余弦相似度。这不是 SOTA,但足以演示 RAG 的"语义匹配 → 命中/未命中"。

>>> 生产环境可替换为 sentence-transformers / OpenAI embeddings + Chroma/pgvector,
    只要保持 embed()/cosine() 的契约即可。
"""
from __future__ import annotations
import math
import re

_ASCII_RE = re.compile(r"[a-z0-9]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def _tokens(text: str) -> list[str]:
    text = (text or "").lower().strip()
    tokens: list[str] = []
    # 英文/数字整词
    tokens.extend(_ASCII_RE.findall(text))
    # 中文字符二元组
    cjk = "".join(_CJK_RE.findall(text))
    if len(cjk) == 1:
        tokens.append(cjk)
    else:
        tokens.extend(cjk[i:i + 2] for i in range(len(cjk) - 1))
    return tokens


def embed(text: str) -> dict[str, float]:
    """返回稀疏 TF 向量 {token: 频次}。"""
    vec: dict[str, float] = {}
    for t in _tokens(text):
        vec[t] = vec.get(t, 0.0) + 1.0
    return vec


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    dot = sum(a[t] * b[t] for t in common)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
