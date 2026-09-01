"""LLM 提供方抽象。

Agent Loop 只依赖这个接口;把 MockProvider 换成真实模型(OpenAI 兼容/国产/本地)
只需实现 chat() 返回相同结构即可,Loop 与工具代码无需改动。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolCall:
    """模型本步请求调用的单个工具。

    id:    本次调用的唯一标识,用于工具结果回填时与调用配对。
    name:  工具名。
    input: 工具入参。
    """
    id: str
    name: str
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMDecision:
    """一次模型决策的结果。

    type == "tool_call":  需要调用 tool_calls 中的工具(可一步并行多个)
    type == "final":      产出最终回复 content
    thought:              本步的思考(用于轨迹可视化)
    """
    type: str
    thought: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    content: Optional[str] = None


class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMDecision:
        """根据对话历史(含已执行的工具结果)与可用工具,决定下一步。"""
        raise NotImplementedError
