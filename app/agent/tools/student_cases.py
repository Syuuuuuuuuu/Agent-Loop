"""学员案例查询工具:按城市/背景检索成功案例(mock 数据)。

当套路要求"已了解客户情况后给出具体案例"时,由 Agent 调用它拿到真实案例数据,
避免笼统地空谈"我们有很多案例"。
"""
from __future__ import annotations
from typing import Any

from .base import Tool
from ...data.cases import all_cases


class StudentCasesTool(Tool):
    name = "student_cases"
    description = ("按城市或客户背景(学历/基础/目标等)检索学员成功案例,返回具体案例"
                   "(姓名、城市、背景、结果)。当需要用真实案例给客户信心时调用。")

    def run(self, query: str = "", **kwargs: Any) -> dict[str, Any]:
        q = (query or "").lower()
        hits = [c for c in all_cases()
                if any(k.lower() in q for k in c.get("keywords", []))]
        if not hits:
            hits = all_cases()[:3]
        cases = [{"name": c["name"], "city": c["city"],
                  "background": c["background"], "outcome": c["outcome"]} for c in hits[:4]]
        return {"count": len(cases), "cases": cases}
