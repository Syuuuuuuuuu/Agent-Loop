"""对话服务:维护会话上下文、驱动 Agent Loop、记录指标。"""
from __future__ import annotations
from typing import Any

from ..agent.loop import AgentLoop, LoopResult
from ..llm.mock_provider import MockLLMProvider
from ..llm.base import LLMProvider
from ..db import cursor
from .. import config

# 简单的进程内会话存储(演示用;生产可换 Redis/DB)
_SESSIONS: dict[str, list[dict[str, Any]]] = {}


def _build_provider() -> LLMProvider:
    if config.LLM_PROVIDER == "ark":
        from ..llm.ark_provider import ArkLLMProvider
        return ArkLLMProvider()
    return MockLLMProvider()


_LOOP = AgentLoop(_build_provider())


def effective_system_prompt() -> str:
    """完整生效的系统提示词(技术流程 + 业务设定 + 套路总纲),供后台查看与聊天使用。"""
    from . import settings_service
    parts = [_BASE_PROMPT]
    parts.append(
        "\n\n【业务设定(老师在后台可改,始终优先遵守,为最高铁律)】\n"
        + settings_service.get_directive()
    )
    summary = settings_service.get_summary().strip()
    if summary:
        parts.append(
            "\n\n【套路总纲(老师已确认的应答策略,按此执行;"
            "recall_playbook 取到的样本仅作具体话术参照,与本总纲冲突时以本总纲为准)】\n"
            + summary
        )
    return "".join(parts)


_BASE_PROMPT = (
            "你是一名 AI 课程咨询顾问。你的回答必须遵循老师教过的『套路』,而不是有问必直答"
            "(例如客户问价格,套路可能要求先了解需求、塑造价值再报价)。\n\n"
            "可用工具:\n"
            "- recall_playbook:取回老师教过的示范问答与套路(客户问题+标准答案+这么答的原因)。\n"
            "- course_search:检索课程的客观信息(价格、周期、适合人群、大纲等)。\n"
            "- student_cases:按城市/客户背景检索学员成功案例。当套路要求『用真实案例给客户信心』"
            "且已了解到客户情况时调用,不要笼统空谈案例。\n"
            "- handoff:遇到没学过、无法按套路可靠回答的问题时,转人工并生成工单。\n\n"
            "工作流程(务必遵守):\n"
            "1. 回答任何客户咨询前,【必须先调用 recall_playbook】拿到老师教过的全部示范样本。\n"
            "2. 【归纳 + 举一反三】把这些样本当成一个整体,归纳出老师背后的应答策略/套路"
            "(例如:面对价格、门槛、就业、优惠等敏感问题,不要直接正面回答,先挖掘需求、塑造价值,再顺势引导)。\n"
            "3. 判断客户当前这句话(哪怕换了问法)属于哪种情况,套用最匹配的示范;"
            "【即使没有完全对应的样本,也要遵循你归纳出的策略来应对,不要因为『这句没被专门教过』就轻易转人工】。\n"
            "4. 【结合完整对话上下文,不要把每句话当成孤立问题】先判断你已经了解到客户哪些信息"
            "(学历、预算/以前薪资、毕业多久、城市、学习目标等):套路所需信息不足时先追问挖掘、不急着下结论,"
            "信息足够时再按策略推进。回答要自然承接上下文。\n"
            "5. 【事实红线】课程的客观事实(具体价格数字、周期、能否包过/分期等承诺)必须来自 course_search 或"
            "老师教过的样本,【绝不可自己编造】;需要而查不到时才 handoff。\n"
            "6. 只有在下列情况才调用 handoff:套路库为空(还没教过任何东西)、问题明显超出你能归纳应对的范围、"
            "或需要你没有的客观事实。\n"
            "7. 用自然、口语化的中文回复,不要暴露上述内部流程和工具名。"
)


def handle_chat(message: str, session_id: str = "demo") -> LoopResult:
    # system 每轮由 Loop 注入最新的 effective_system_prompt(总纲/业务设定实时生效),
    # 会话存储只保留纯对话轮次。
    history = _SESSIONS.get(session_id, [])

    result = _LOOP.run(message, history=history, system=effective_system_prompt())

    # 只把用户与最终回复(不含中间的 tool_calls / tool 消息)落进会话上下文
    _SESSIONS[session_id] = [
        m for m in result.session_messages
        if m.get("role") == "user"
        or (m.get("role") == "assistant" and not m.get("tool_calls"))
    ]

    _log_metrics(session_id, message, result)
    return result


def _log_metrics(session_id: str, question: str, result: LoopResult) -> None:
    hit = 1 if (result.kb_hit and not result.handoff) else 0
    with cursor() as cur:
        cur.execute(
            "INSERT INTO metrics_log (session_id, question, hit_kb, handoff) VALUES (?, ?, ?, ?)",
            (session_id, question, hit, 1 if result.handoff else 0),
        )


def reset_session(session_id: str = "demo") -> None:
    _SESSIONS.pop(session_id, None)


def refine_reply(question: str, reply: str, feedback: str, session_id: str = "demo") -> str:
    """实测纠偏:老师对 AI 刚才这条回复提意见,AI 据此重答这一句(不写库,仅当场修正)。

    重答会遵守当前系统提示词(含总纲/铁律),并把会话里最后一条 assistant 替换为修正版,
    使后续对话从修正后的语境继续。
    """
    messages = [
        {"role": "system", "content": effective_system_prompt()},
        {"role": "user", "content": question},
        {"role": "assistant", "content": reply},
        {"role": "user", "content": (
            "以上是你刚才对客户说的话。下面是【教练点评】(是我这个培训你的人给的纠偏意见,"
            "不是客户说的,不要当成客户的话来回应):\n" + feedback
            + "\n\n请你据此,把刚才发给客户的这句话重新说一遍。只输出修正后、要直接发给客户的内容,不要解释。")},
    ]
    decision = _LOOP.llm.chat(messages, [])
    revised = (decision.content or "").strip() or reply

    hist = _SESSIONS.get(session_id)
    if hist and hist[-1].get("role") == "assistant":
        hist[-1]["content"] = revised
    return revised


def commit_refinement(question: str, answer: str, feedback: str) -> dict:
    """把纠偏结果固化为一条套路样本,并自动合并进总纲(状态合并)。"""
    from . import playbook_service
    note = "(实测纠偏)" + feedback if feedback else "(实测纠偏)"
    sample_id = playbook_service.add_sample(question, answer, note)
    summary = regenerate_summary()
    return {"ok": True, "sample_id": sample_id, "summary": summary}


_EMPTY_SUMMARY = "套路库还是空的。去『教学模式』教它几条,我就能帮你归纳出套路总纲了。"


def induce_playbook(existing: str = "") -> str:
    """从训练样本归纳『应答套路总纲』。

    existing 非空时执行【状态合并】:完整保留老师已改写的总纲规则,
    只把样本里体现出、但现有总纲还没覆盖的新套路补进去;冲突以老师现有总纲为准。
    """
    from . import playbook_service
    samples = playbook_service.recall_all()
    if not samples:
        return _EMPTY_SUMMARY
    body = "\n\n".join(
        f"{i + 1}. 客户问题:{s['question']}\n   标准答案:{s['answer']}\n   这么答的原因/套路:{s.get('note', '') or '(未填)'}"
        for i, s in enumerate(samples)
    )
    if existing.strip():
        messages = [
            {"role": "system", "content": (
                "你是资深销售培训师。老师已经有一份【现有套路总纲】,其中可能有老师手动修订或补充的规则,"
                "这些必须尊重并原样保留。现在给你一批教学样本。请在【完整保留老师现有总纲里的规则和措辞倾向】"
                "的前提下,把样本里体现出、但现有总纲还没覆盖的新套路补充进去;若样本与老师现有总纲有冲突,"
                "一律以老师现有总纲为准。输出更新后的完整总纲,条目化、简洁;不要删除老师已有的规则,不要复述原始样本。")},
            {"role": "user", "content": (
                "【现有套路总纲(老师已改写,须保留)】:\n" + existing.strip()
                + "\n\n【全部教学样本】:\n" + body)},
        ]
    else:
        messages = [
            {"role": "system", "content": (
                "你是资深销售培训师。下面是老师教给『AI 课程咨询顾问』的一批示范"
                "(客户问题 + 标准答案 + 这么答的原因)。请你从这些具体示范中,归纳提炼出老师的"
                "『应答套路总纲』:用简洁的条目列出通用的销售策略原则(面对哪类问题该怎么应对、"
                "先做什么后做什么、什么时候先挖需求、什么时候引导等)。只输出总纲本身,不要复述原始样本。")},
            {"role": "user", "content": "以下是全部示范样本:\n\n" + body},
        ]
    decision = _LOOP.llm.chat(messages, [])
    return (decision.content or "").strip() or "(暂未归纳出内容)"


def get_or_build_summary() -> str:
    """返回已保存的总纲;若从未生成过,则首次自动归纳并存下来(保留后续编辑)。"""
    from . import settings_service
    saved = settings_service.get_summary()
    if saved.strip():
        return saved
    fresh = induce_playbook()
    if fresh and fresh != _EMPTY_SUMMARY:
        settings_service.set_summary(fresh)
    return fresh


def regenerate_summary() -> str:
    """状态合并:以老师改写后的现有总纲为基底,融合全部样本,重新归纳并保存。"""
    from . import settings_service
    merged = induce_playbook(existing=settings_service.get_summary())
    if merged and merged != _EMPTY_SUMMARY:
        settings_service.set_summary(merged)
    return merged
