"""Project templates. A new project copies one template's types and statuses once.

Nothing stored refers back to a template after the copy.
"""

from dataclasses import dataclass

from kangaroo.schemas import StatusCategory


@dataclass(frozen=True)
class TemplateType:
    name: str
    position: int


@dataclass(frozen=True)
class TemplateStatus:
    name: str
    category: StatusCategory
    position: int


@dataclass(frozen=True)
class ProjectTemplate:
    """A named set of types and statuses. Transitions are pairs of status names."""

    name: str
    types: tuple[TemplateType, ...]
    statuses: tuple[TemplateStatus, ...]
    transitions: tuple[tuple[str, str], ...] = ()


TO_DO_LIST = ProjectTemplate(
    name="To Do List",
    types=(TemplateType(name="Task", position=0),),
    statuses=(
        TemplateStatus(name="To do", category="todo", position=0),
        TemplateStatus(name="In Progress", category="in_progress", position=1),
        TemplateStatus(name="Done", category="done", position=2),
    ),
)

DEFAULT_TEMPLATE_NAME = TO_DO_LIST.name

SOFTWARE_PROJECT = ProjectTemplate(
    name="Software Project",
    types=(TemplateType(name="Task", position=0),),
    statuses=(
        TemplateStatus(name="Open", category="todo", position=0),
        TemplateStatus(name="To do", category="todo", position=1),
        TemplateStatus(name="In progress", category="in_progress", position=2),
        TemplateStatus(name="Review", category="in_progress", position=3),
        TemplateStatus(name="Done", category="done", position=4),
        TemplateStatus(name="Won't do", category="done", position=5),
    ),
)

TEMPLATES: dict[str, ProjectTemplate] = {
    TO_DO_LIST.name: TO_DO_LIST,
    SOFTWARE_PROJECT.name: SOFTWARE_PROJECT,
}
