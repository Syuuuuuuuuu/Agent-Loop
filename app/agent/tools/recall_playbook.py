"""套路召回工具:按客户当前问句做 embedding 语义检索,取回最相关的示范问答与套路,
供大模型模仿作答。

这是本系统的核心:回答任何咨询前先调它。以前是全量返回所有样本,现在改为
top-k 语义检索(只召回与本次问句最相关的几条),库变大也不会撑爆上下文。
"""
from __future__ import annotations
from typing import Any

from .base import Tool
from ...services import playbook_service
from ... import config


class RecallPlaybookTool(Tool):
    name = "recall_playbook"
    description = ("检索老师教过的、与客户当前问句最相关的示范问答与套路(客户问题+标准答案+"
                   "这么答的原因)。回答任何客户咨询前必须先调用它,然后用语义理解判断客户这句话"
                   "命中哪条示范的套路,严格模仿该套路的策略与话术风格来回答。")

    def run(self, query: str = "", **kwargs: Any) -> dict[str, Any]:
        samples = playbook_service.recall_topk(query, config.PLAYBOOK_TOP_K)
        return {"count": len(samples), "samples": samples}
