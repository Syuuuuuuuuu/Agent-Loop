"""冒烟测试:跑一遍演示主线,验证 Agent Loop 多工具决策 + 教学自进化闭环。

运行前先启动服务:python run.py(另开一个终端执行本脚本)
通过标准:结尾打印 ALL PASSED。
"""
import json
import sys
import urllib.error
import urllib.request

# Windows 控制台默认 GBK,重配为 UTF-8 避免中文乱码
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

BASE = "http://127.0.0.1:8000"


def call(path, payload=None, method="POST"):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        sys.exit(f"❌ 连不上 {BASE},请先启动服务:python run.py\n   ({exc})")


def chat(msg):
    r = call("/api/chat", {"message": msg, "session_id": "test"})
    tools = [s["tool"] for s in r["trace"] if s["type"] == "tool_call"]
    print(f"\nQ: {msg}")
    print(f"   工具链: {tools}")
    print(f"   handoff={r['handoff']} ticket={r.get('ticket_id')}")
    print(f"   A: {r['reply']}")
    return r


def clean_playbook():
    """清空套路库,保证演示从零开始、可重复执行。"""
    for s in call("/api/playbook", method="GET"):
        call(f"/api/playbook/{s['id']}", method="DELETE")
    call("/api/session/reset?session_id=test")


print("====== 前置:清空套路库,从零开始演示 ======")
clean_playbook()

print("\n====== 第一幕:教学模式,老师教三条套路 ======")
call("/api/teach", {"question": "这个课多少钱?", "answer": "价格这块我想先了解一下你的学习目标和预算,再帮你看看哪个课程更合适。", "note": "先挖需求,不直接报价"})
call("/api/teach", {"question": "太贵了,能便宜点吗?", "answer": "课程价值主要看能不能帮你真正转型,优惠方面可以跟班主任一对一沟通。", "note": "先塑造价值,不自己谈价,引导对接班主任"})
call("/api/teach", {"question": "学完能找到工作吗?", "answer": "很多学员通过学习完成了转型,您可以看看真实的学员案例。", "note": "用真实案例给客户信心"})
print("   已教 3 条,套路库共", len(call("/api/playbook", method="GET")), "条")

print("\n====== 第二幕:Agent Loop —— 自主选工具 ======")
r1 = chat("这个课多少钱?")
tools1 = [s["tool"] for s in r1["trace"] if s["type"] == "tool_call"]
assert not r1["handoff"], "已教过价格套路,不应转人工"
assert "recall_playbook" in tools1 and "course_search" in tools1, \
    f"价格问题应召回套路并检索课程,实际: {tools1}"

r2 = chat("学完能找到工作吗?")
tools2 = [s["tool"] for s in r2["trace"] if s["type"] == "tool_call"]
assert not r2["handoff"], "已教过就业套路,不应转人工"
assert "recall_playbook" in tools2 and "student_cases" in tools2, \
    f"就业问题应召回套路并检索学员案例,实际: {tools2}"
assert "张同学" in r2["reply"], f"应给出真实学员案例,实际: {r2['reply']}"

print("\n====== 第三幕:教学自进化闭环 —— 没教过的问题 ======")
r3 = chat("扫地机器人 X1 能翻越多高的门槛?")
tid = r3["ticket_id"]
assert r3["handoff"] and tid, "没教过且召回不相关的问题应自动转人工并生成工单"

print("\n-- 后台:针对工单补充标准答案,教会它并入库 --")
print("   teach:", call(f"/api/tickets/{tid}/teach",
                       {"answer": "扫地机器人 X1 可自动翻越最高约 2cm 的门槛。",
                        "note": "产品能力参数,直接回答"}))

print("\n-- 回放验证:同一问题这次应直接答对(自纠错生效) --")
r4 = chat("扫地机器人 X1 能翻越多高的门槛?")
assert not r4["handoff"], "补充后不应再转人工"
assert "2cm" in r4["reply"], "应答出 2cm"

print("\n====== 第四幕:实测纠偏(老师提意见,AI 当场重答) ======")
ref = call("/api/refine", {"question": "这个课多少钱?",
                           "reply": r1["reply"],
                           "feedback": "别急着反问预算,先问候一句并表明愿意帮忙",
                           "session_id": "test"})
print("   纠偏后:", ref["reply"])
assert ref["reply"], "纠偏应返回重答内容"

print("\n====== 第五幕:统计看板(量化自进化) ======")
m = call("/api/metrics", method="GET")
print("   metrics:", m)
assert m["kb_count"] == 4, f"套路库应有 4 条(3 教 + 1 工单补充),实际 {m['kb_count']}"

print("\nALL PASSED")
