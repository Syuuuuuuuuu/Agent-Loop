"""全局配置。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data.db"
STATIC_DIR = BASE_DIR / "static"

# 从 .env 读取密钥等敏感配置(文件不存在时静默跳过)
load_dotenv(BASE_DIR / ".env")

# Agent Loop 边界控制
MAX_LOOP_STEPS = 6          # 单次对话内最多循环步数,防死循环
LOOP_TIMEOUT_SECONDS = 30   # 单次对话超时

# 知识库检索:命中阈值(余弦相似度),低于此值视为"未命中"
KB_HIT_THRESHOLD = 0.45
KB_TOP_K = 3

# 套路库(playbook)语义检索:每次只召回最相关的 top-k 条样本,避免全量塞爆上下文
PLAYBOOK_TOP_K = int(os.getenv("PLAYBOOK_TOP_K", "5"))

# 选用的 LLM 提供方:mock(离线桩)| ark(真实豆包/火山引擎 ARK)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")

# 豆包(火山引擎 ARK)配置,OpenAI 兼容接口
ARK_API_KEY = os.getenv("ARK_API_KEY", "")
ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
ARK_CHAT_MODEL = os.getenv("ARK_CHAT_MODEL", "")
# 豆包 embedding 模型(multimodal 接口),用于套路库语义检索
ARK_EMBED_MODEL = os.getenv("ARK_EMBED_MODEL", "doubao-embedding-vision-251215")
