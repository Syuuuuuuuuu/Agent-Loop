"""Pydantic 请求/响应模型。"""
from typing import Any, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "demo"


class ChatResponse(BaseModel):
    reply: str
    handoff: bool = False          # 本次是否转了人工
    ticket_id: Optional[int] = None
    # 轨迹是灵活的调试结构(每步字段随类型不同),原样透传,便于扩展
    trace: list[dict[str, Any]] = []


class AnswerRequest(BaseModel):
    answer: str


class TeachRequest(BaseModel):
    """教学:一条示范样本 = 客户问题 + 标准答案 + 这么答的原因(套路)。"""
    question: str
    answer: str
    note: str = ""


class TicketTeachRequest(BaseModel):
    """针对某个工单补充答案+套路。"""
    answer: str
    note: str = ""


class SampleUpdate(BaseModel):
    question: str
    answer: str
    note: str = ""


class DirectiveUpdate(BaseModel):
    """更新 AI 业务设定(全局人设/语气/铁律)。"""
    text: str


class SummaryUpdate(BaseModel):
    """老师手动改写套路总纲。"""
    text: str


class RefineRequest(BaseModel):
    """实测纠偏:对某条 AI 回复给意见,让它据此重答。"""
    question: str
    reply: str
    feedback: str
    session_id: str = "demo"


class RefineCommitRequest(BaseModel):
    """把纠偏后的回复固化为套路样本。"""
    question: str
    answer: str
    feedback: str = ""


class Ticket(BaseModel):
    id: int
    question: str
    context: str
    status: str
    created_at: str


class Audit(BaseModel):
    id: int
    ticket_id: Optional[int]
    question: str
    answer: str
    status: str
    created_at: str


class Metrics(BaseModel):
    kb_count: int
    total_chats: int
    handoff_count: int
    handoff_rate: float
    kb_hit_count: int
    kb_hit_rate: float
