"""规则桩 LLM(离线演示用)。

这是为了**离线、可重复**地演示课程咨询场景下的 Agent Loop 而写的"假大脑":
它读对话历史(含已执行的工具结果),用规则模拟真实模型的"决定调哪个工具 / 何时收尾"。

>>> 换成真实模型(ArkProvider)时,语义理解取代这里的规则即可,Loop 与工具都不用动。
"""
from __future__ import annotations
import re
from typing import Any

from .base import LLMProvider, LLMDecision, ToolCall

# 各类意图的关键词
_HANDOFF_RE = re.compile(r"(转人工|人工客服|真人|人工)")
_FACT_RE = re.compile(r"(价格|多少钱|学费|贵|便宜|周期|多久|大纲|课程内容|上课|方式|适合)")
_CASE_RE = re.compile(r"(案例|学员|谁学过|就业|找到工作|入职|薪资|offer)")

# 套路召回最低相似度:最高分样本低于此值视为"没教过这个问题",转人工。
# (本地 hash 向量:同一问句=1.0,相关变体≈0.1~0.3,无关≈0)
_MOCK_HIT_THRESHOLD = 0.1


def _call(name: str, tool_input: dict[str, Any], thought: str) -> LLMDecision:
    """构造单工具调用决策(桩场景一步只调一个工具)。"""
    return LLMDecision(
        type="tool_call",
        tool_calls=[ToolCall(id=f"call_{name}", name=name, input=tool_input)],
        thought=thought,
    )


def _last_user_message(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "") or ""
    return ""


def _tool_results_since_last_user(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """返回 {tool_name: result} —— 本轮用户提问后已执行过的工具及其结果。"""
    results: dict[str, Any] = {}
    collecting = False
    for m in messages:
        if m.get("role") == "user":
            results = {}          # 遇到新的用户提问,重置
            collecting = True
            continue
        if collecting and m.get("role") == "tool":
            results[m.get("name")] = m.get("result")
    return results


class MockLLMProvider(LLMProvider):
    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMDecision:
        question = _last_user_message(messages)
        done = _tool_results_since_last_user(messages)

        # 0) 用户明确要求转人工
        if _HANDOFF_RE.search(question):
            if "handoff" not in done:
                return _call("handoff", {"question": question, "context": "用户主动要求转人工"},
                             "用户明确要求转人工,直接转接。")
            return LLMDecision(type="final", thought="已转接。",
                               content="已为您转接人工客服,请稍候,顾问会尽快跟进。")

        # 1) 回答任何咨询前,先召回老师教过的示范问答与套路
        if "recall_playbook" not in done:
            return _call("recall_playbook", {"query": question},
                         "先召回老师教过的示范问答与套路。")

        pb = done.get("recall_playbook") or {}

        # 1.1 套路库为空,或召回到的样本与本次问题都不相关(没教过) —— 转人工
        top = (pb.get("samples") or [{}])[0]
        top_score = float(top.get("score") or 0.0)
        if not pb.get("count") or top_score < _MOCK_HIT_THRESHOLD:
            if "handoff" not in done:
                reason = "套路库为空,尚未教过任何内容。" if not pb.get("count") \
                    else f"召回最高相似度 {top_score:.2f} 低于阈值,没教过这个问题。"
                return _call("handoff",
                             {"question": question, "context": reason},
                             "这个问题没学过 / 没把握,转人工。")
            return LLMDecision(type="final", thought="已转人工。",
                               content="这个问题我还没学过,已为您转接人工客服处理。")

        # 2) 涉及课程客观事实(价格/周期/大纲等)—— 查课程库
        if _FACT_RE.search(question) and "course_search" not in done:
            return _call("course_search", {"query": question},
                         "问题涉及课程客观信息,检索课程库核对事实。")

        # 3) 需要用真实案例给客户信心 —— 查学员案例
        if _CASE_RE.search(question) and "student_cases" not in done:
            return _call("student_cases", {"query": question},
                         "需要真实学员案例作答,检索案例库。")

        # 4) 收尾:按召回到的套路样本 + 已查到的信息作答
        return LLMDecision(type="final", thought="按召回到的套路作答。",
                           content=_answer(pb, done))


def _answer(pb: dict[str, Any], done: dict[str, Any]) -> str:
    """把套路样本 + 课程信息 + 案例拼成回复(真实模型会语义精判并自然生成)。"""
    samples = pb.get("samples") or []
    course = (done.get("course_search") or {}).get("course")
    cases = (done.get("student_cases") or {}).get("cases")

    parts: list[str] = []
    if samples:
        parts.append(samples[0].get("answer", ""))
    if course:
        parts.append(f"(参考:{course['name']},{course.get('price', '')}、{course.get('duration', '')})")
    if cases:
        c = cases[0]
        parts.append(f"比如{c['name']}({c['city']})——{c['outcome']}。")
    return "".join(p for p in parts if p) or "您好,请问您具体想了解哪方面呢?"
