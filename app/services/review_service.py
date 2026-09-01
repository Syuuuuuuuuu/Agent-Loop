"""自进化闭环服务:答不上 → 生成工单 → 老师补充(教) → 进套路库 → 下次答对。"""
from __future__ import annotations
from typing import Any

from ..db import cursor
from . import playbook_service


# ---------- 工单(答不上的问题) ----------

def list_tickets(status: str | None = "open") -> list[dict[str, Any]]:
    with cursor() as cur:
        if status:
            cur.execute("SELECT * FROM tickets WHERE status=? ORDER BY id DESC", (status,))
        else:
            cur.execute("SELECT * FROM tickets ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]


def teach_from_ticket(ticket_id: int, answer: str, note: str = "") -> dict[str, Any]:
    """针对工单补充"标准答案 + 套路" → 直接进套路库 → 关闭工单。"""
    with cursor() as cur:
        cur.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
        ticket = cur.fetchone()
        if not ticket:
            return {"ok": False, "error": "工单不存在"}
    sample_id = playbook_service.add_sample(ticket["question"], answer, note, source="ticket")
    with cursor() as cur:
        cur.execute("UPDATE tickets SET status='closed' WHERE id=?", (ticket_id,))
    return {"ok": True, "sample_id": sample_id}


# ---------- 统计看板 ----------

def metrics() -> dict[str, Any]:
    with cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM metrics_log")
        total = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM metrics_log WHERE handoff=1")
        handoff = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM metrics_log WHERE hit_kb=1")
        hit = cur.fetchone()["c"]
    kb_count = playbook_service.count()
    return {
        "kb_count": kb_count,
        "total_chats": total,
        "handoff_count": handoff,
        "handoff_rate": round(handoff / total, 3) if total else 0.0,
        "kb_hit_count": hit,
        "kb_hit_rate": round(hit / total, 3) if total else 0.0,
    }
