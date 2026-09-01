"""AI 课程目录(演示用)。

课程咨询顾问用它回答课程的客观信息(适合谁、周期、大纲、价格等);
"怎么回答/话术套路"则由老师在对话中教出来,存进 playbook。
"""

COURSES = [
    {
        "id": "C001",
        "name": "AI 应用实战训练营",
        "category": "入门到就业",
        "price": "￥6980",
        "duration": "12 周(每周 2 次直播 + 作业)",
        "audience": "零基础转行、想用 AI 提效的职场人",
        "outline": "Prompt 工程、RAG 知识库、Agent 开发、项目实战与作品集",
        "highlight": "0 基础可学,含 4 个可写进简历的实战项目,配班主任督学",
        "keywords": ["实战", "训练营", "转行", "零基础", "就业", "agent", "rag"],
    },
    {
        "id": "C002",
        "name": "大模型微调与部署进阶课",
        "category": "进阶",
        "price": "￥9800",
        "duration": "8 周",
        "audience": "有 Python 基础、想深入大模型工程的开发者",
        "outline": "LoRA 微调、数据构造、推理优化、私有化部署与压测",
        "highlight": "偏工程实战,提供 GPU 云环境,结课可独立完成模型微调与上线",
        "keywords": ["微调", "部署", "进阶", "lora", "工程", "开发者"],
    },
    {
        "id": "C003",
        "name": "AI 少儿编程启蒙课",
        "category": "青少年",
        "price": "￥3980",
        "duration": "16 周",
        "audience": "8-14 岁青少年",
        "outline": "图形化编程、AI 绘画与对话、创意作品制作",
        "highlight": "寓教于乐,培养逻辑思维与 AI 素养,小班教学",
        "keywords": ["少儿", "青少年", "编程", "启蒙", "孩子"],
    },
]


def all_courses() -> list[dict]:
    return COURSES
