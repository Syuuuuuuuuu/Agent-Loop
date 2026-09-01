"""转人工工具:生成工单,作为自纠错闭环的起点。"""
from __future__ import annotations
from typing import Any

from .base import Tool
from ...db import cursor


class HandoffTool(Tool):
    name = "handoff"
    description = "当无法可靠回答用户问题时,转接人工客服并生成工单。"
    parameters = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "需要转人工的用户问题原文"},
            "context": {"type": "string", "description": "转人工的原因/上下文说明"},
        },
        "required": ["question"],
    }

    def run(self, question: str = "", context: str = "", **kwargs: Any) -> dict[str, Any]:
        with cursor() as cur:
            cur.execute(
                "INSERT INTO tickets (question, context, status) VALUES (?, ?, 'open')",
                (question, context),
            )
            ticket_id = cur.lastrowid
        return {"ticket_id": ticket_id, "status": "open"}
