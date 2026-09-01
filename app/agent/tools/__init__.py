"""工具注册表。新增工具 → 在这里登记即可被 Agent Loop 使用。"""
from .recall_playbook import RecallPlaybookTool
from .course_search import CourseSearchTool
from .student_cases import StudentCasesTool
from .handoff import HandoffTool


def build_registry() -> dict:
    tools = [
        RecallPlaybookTool(),
        CourseSearchTool(),
        StudentCasesTool(),
        HandoffTool(),
    ]
    return {t.name: t for t in tools}
