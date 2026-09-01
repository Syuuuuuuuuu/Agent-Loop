"""课程检索工具:根据用户问题匹配最相关的课程及其客观信息。"""
from __future__ import annotations
from typing import Any

from .base import Tool
from ...data.courses import all_courses
from ...knowledge import embedding


class CourseSearchTool(Tool):
    name = "course_search"
    description = "检索课程目录,返回最相关课程的客观信息(名称、价格、周期、适合人群、大纲、亮点)。"

    def run(self, query: str = "", **kwargs: Any) -> dict[str, Any]:
        qvec = embedding.embed(query)
        best = None
        best_score = 0.0
        for c in all_courses():
            text = " ".join([c["name"], c["category"], c["audience"],
                             c["outline"], c["highlight"], " ".join(c.get("keywords", []))])
            score = embedding.cosine(qvec, embedding.embed(text))
            if score > best_score:
                best_score, best = score, c
        if best and best_score >= 0.06:
            return {"found": True, "score": round(best_score, 3),
                    "course": {k: best[k] for k in ("id", "name", "category", "price",
                                                    "duration", "audience", "outline", "highlight")}}
        return {"found": False, "score": round(best_score, 3),
                "courses": [{"name": c["name"], "price": c["price"],
                             "audience": c["audience"]} for c in all_courses()]}
