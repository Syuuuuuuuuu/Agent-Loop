"""工具统一接口。"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    name: str = ""
    description: str = ""
    # 入参 JSON Schema,供真实 LLM 做 function calling;默认单一 query 参数
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "用户问题原文"},
        },
        "required": ["query"],
    }

    @abstractmethod
    def run(self, **kwargs: Any) -> dict[str, Any]:
        """执行工具,返回结构化结果(dict)。"""
        raise NotImplementedError

    def schema(self) -> dict[str, Any]:
        """暴露给(真实)LLM 的工具描述。"""
        return {"name": self.name, "description": self.description,
                "parameters": self.parameters}
