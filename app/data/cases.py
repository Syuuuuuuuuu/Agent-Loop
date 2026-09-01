"""学员成功案例库(mock,演示用)。

供 student_cases 工具按城市/背景检索,让顾问在"已了解客户情况"时能给出具体案例。
"""

CASES = [
    {"name": "张同学", "city": "北京", "background": "大专、非科班、原做运营",
     "outcome": "学习约 4 个月后入职北京某互联网公司 AI 应用岗,月薪 15k",
     "keywords": ["北京", "大专", "非科班", "转行", "运营"]},
    {"name": "李同学", "city": "北京", "background": "本科、有一点 Python 基础",
     "outcome": "学习 5 个月后拿到北京某公司算法岗 offer,月薪 22k",
     "keywords": ["北京", "本科", "python", "算法"]},
    {"name": "王同学", "city": "上海", "background": "零基础、宝妈",
     "outcome": "学习后成为上海某公司提示词工程师,月薪 14k,可远程",
     "keywords": ["上海", "零基础", "宝妈", "远程", "提示词"]},
    {"name": "赵同学", "city": "深圳", "background": "毕业 2 年、传统软件开发",
     "outcome": "转型大模型工程,入职深圳某 AI 创业公司,月薪 28k",
     "keywords": ["深圳", "开发", "转型", "大模型", "工程"]},
    {"name": "陈同学", "city": "杭州", "background": "应届毕业生、计算机相关",
     "outcome": "毕业即入职杭州某公司 AI 产品岗,月薪 13k",
     "keywords": ["杭州", "应届", "计算机", "产品"]},
]


def all_cases() -> list[dict]:
    return CASES
