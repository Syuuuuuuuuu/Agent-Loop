"""FastAPI 入口:课程咨询、教学(套路库)、工单、统计,以及前端静态页。"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .db import init_db
from .models import (ChatRequest, ChatResponse, TeachRequest,
                     TicketTeachRequest, SampleUpdate, DirectiveUpdate,
                     SummaryUpdate, RefineRequest, RefineCommitRequest)
from .services import (chat_service, review_service, playbook_service,
                       settings_service)

app = FastAPI(title="AI 课程咨询顾问 · Agent Loop + 教学自进化")


@app.on_event("startup")
def _startup() -> None:
    init_db()


# ---------- 咨询(客户视角) ----------

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    result = chat_service.handle_chat(req.message, req.session_id or "demo")
    return ChatResponse(
        reply=result.reply,
        handoff=result.handoff,
        ticket_id=result.ticket_id,
        trace=result.trace,
    )


@app.post("/api/session/reset")
def reset_session(session_id: str = "demo") -> dict:
    chat_service.reset_session(session_id)
    return {"ok": True}


# ---------- 实测纠偏(点评式教学) ----------

@app.post("/api/refine")
def refine(req: RefineRequest) -> dict:
    """据老师点评,把 AI 刚才这条回复当场重答一遍。"""
    revised = chat_service.refine_reply(req.question, req.reply, req.feedback, req.session_id)
    return {"reply": revised}


@app.post("/api/refine/commit")
def refine_commit(req: RefineCommitRequest) -> dict:
    """把纠偏结果固化为套路样本,并自动合并进总纲。"""
    return chat_service.commit_refinement(req.question, req.answer, req.feedback)


# ---------- 教学 / 套路库(训练样本) ----------

@app.post("/api/teach")
def teach(req: TeachRequest) -> dict:
    sample_id = playbook_service.add_sample(req.question, req.answer, req.note)
    return {"ok": True, "sample_id": sample_id}


@app.get("/api/playbook")
def get_playbook() -> list[dict]:
    return playbook_service.list_samples()


@app.get("/api/playbook/summary")
def playbook_summary() -> dict:
    """套路总纲:返回已保存版本(可被老师改写);首次访问自动归纳并保存。"""
    return {"summary": chat_service.get_or_build_summary()}


@app.put("/api/playbook/summary")
def save_playbook_summary(req: SummaryUpdate) -> dict:
    """老师手动改写总纲并保存。"""
    return settings_service.set_summary(req.text)


@app.post("/api/playbook/summary/regenerate")
def regenerate_playbook_summary() -> dict:
    """状态合并:保留老师改写,融合全部样本重新归纳。"""
    return {"summary": chat_service.regenerate_summary()}


@app.put("/api/playbook/{sample_id}")
def update_playbook(sample_id: int, req: SampleUpdate) -> dict:
    return playbook_service.update_sample(sample_id, req.question, req.answer, req.note)


@app.delete("/api/playbook/{sample_id}")
def delete_playbook(sample_id: int) -> dict:
    return playbook_service.delete_sample(sample_id)


# ---------- 工单(答不上的问题) → 教它 ----------

@app.get("/api/tickets")
def get_tickets(status: str | None = "open") -> list[dict]:
    return review_service.list_tickets(status)


@app.post("/api/tickets/{ticket_id}/teach")
def teach_ticket(ticket_id: int, req: TicketTeachRequest) -> dict:
    return review_service.teach_from_ticket(ticket_id, req.answer, req.note)


# ---------- AI 业务设定(全局人设/语气/铁律) ----------

@app.get("/api/settings/directive")
def get_directive() -> dict:
    return {"directive": settings_service.get_directive()}


@app.put("/api/settings/directive")
def put_directive(req: DirectiveUpdate) -> dict:
    return settings_service.set_directive(req.text)


@app.get("/api/settings/system-prompt")
def get_system_prompt() -> dict:
    """完整生效的系统提示词(技术流程 + 业务设定),供老师查看。"""
    return {"prompt": chat_service.effective_system_prompt()}


# ---------- 统计 ----------

@app.get("/api/metrics")
def get_metrics() -> dict:
    return review_service.metrics()


# ---------- 前端 ----------

@app.get("/")
def index() -> FileResponse:
    return FileResponse(config.STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
