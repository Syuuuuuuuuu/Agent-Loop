"""豆包(火山引擎 ARK)真实 LLM 提供方。

ARK 提供 OpenAI 兼容接口,这里用 openai SDK 调用,并把 Agent Loop 内部的
消息/工具格式与 OpenAI 的 function calling 格式互相转换。

Loop 与工具代码完全不用改动:它只依赖 LLMProvider.chat() 返回 LLMDecision。
"""
from __future__ import annotations
import json
from typing import Any

from openai import OpenAI

from .base import LLMProvider, LLMDecision, ToolCall
from .. import config


class ArkLLMProvider(LLMProvider):
    def __init__(self) -> None:
        if not config.ARK_API_KEY:
            raise RuntimeError("未配置 ARK_API_KEY,请在 .env 中填写豆包密钥。")
        if not config.ARK_CHAT_MODEL:
            raise RuntimeError("未配置 ARK_CHAT_MODEL,请在 .env 中填写豆包模型/接入点 ID。")
        self.client = OpenAI(api_key=config.ARK_API_KEY, base_url=config.ARK_BASE_URL)
        self.model = config.ARK_CHAT_MODEL

    def chat(self, messages: list[dict[str, Any]],
             tools: list[dict[str, Any]]) -> LLMDecision:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": _to_openai_messages(messages),
            "temperature": 0.2,
        }
        if tools:  # 无工具时(如纯文本归纳总纲)不传 tools,避免部分接口报错
            kwargs["tools"] = _to_openai_tools(tools)
            kwargs["tool_choice"] = "auto"
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        thought = (msg.content or "").strip()

        if msg.tool_calls:
            calls: list[ToolCall] = []
            for call in msg.tool_calls:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except (json.JSONDecodeError, TypeError):
                    args = {}
                calls.append(ToolCall(id=call.id, name=call.function.name, input=args))
            names = "、".join(c.name for c in calls)
            return LLMDecision(
                type="tool_call",
                tool_calls=calls,
                thought=thought or f"调用工具 {names}。",
            )

        return LLMDecision(type="final", thought=thought, content=msg.content or "")


def _to_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {"type": "object", "properties": {}}),
            },
        }
        for t in tools
    ]


def _to_openai_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """把 Loop 内部消息映射为 OpenAI 兼容格式。

    Loop 内部已采用标准配对结构(assistant 带 tool_calls 发起、tool 带
    tool_call_id 回填),这里只做格式映射:工具入参/结果序列化为字符串,
    无需再伪造调用配对。
    """
    out: list[dict[str, Any]] = []
    for m in messages:
        role = m.get("role")
        if role in ("system", "user"):
            out.append({"role": role, "content": m.get("content") or ""})
        elif role == "assistant":
            tool_calls = m.get("tool_calls")
            if tool_calls:
                out.append({
                    "role": "assistant",
                    "content": m.get("content") or "",
                    "tool_calls": [{
                        "id": c["id"],
                        "type": "function",
                        "function": {
                            "name": c["name"],
                            "arguments": json.dumps(c.get("input") or {}, ensure_ascii=False),
                        },
                    } for c in tool_calls],
                })
            else:
                out.append({"role": "assistant", "content": m.get("content") or ""})
        elif role == "tool":
            out.append({
                "role": "tool",
                "tool_call_id": m.get("tool_call_id"),
                "content": json.dumps(m.get("result"), ensure_ascii=False),
            })
    return out
