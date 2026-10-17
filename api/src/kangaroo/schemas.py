from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

from kangaroo.utils import render_markdown

StatusCategory = Literal["todo", "in_progress", "done"]
TypeLevel = Literal["standard", "subtask"]


def clean_labels(labels: list[str]) -> list[str]:
    """Trim each label, reject empty ones and drop duplicates, keeping order."""
    cleaned: list[str] = []
    for label in labels:
        text = label.strip()
        if not text:
            raise ValueError("Labels cannot be empty")
        if text not in cleaned:
            cleaned.append(text)
    return cleaned


Labels = Annotated[list[str], AfterValidator(clean_labels)]


class Timestamped(BaseModel):
    """Timestamps every stored entity carries."""

    created_at: datetime
    modified_at: datetime


class WorkItemCreate(BaseModel):
    """A work item creation request.

    The type decides whether the item is a subtask: a type with level ``subtask``
    needs a ``parent_id`` and any other type must not have one. Without a
    ``status_id`` the item starts in the project's first To Do status.
    """

    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    project_id: UUID
    type_id: UUID
    status_id: UUID | None = None
    parent_id: UUID | None = None
    labels: Labels = Field(default_factory=list)


def reject_null[T](value: T | None) -> T | None:
    """Reject an explicit null for a required field. Omitting it is still allowed."""
    if value is None:
        raise ValueError("Field cannot be null")
    return value


class WorkItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    project_id: UUID | None = None
    status_id: UUID | None = None
    type_id: UUID | None = None
    labels: Labels = Field(default_factory=list)
    trashed: bool | None = None

    _reject_null_title = field_validator("title")(reject_null)
    _reject_null_status = field_validator("status_id")(reject_null)
    _reject_null_type = field_validator("type_id")(reject_null)


class WorkItemReplace(BaseModel):
    """Full replacement. Without a ``status_id`` the item goes to the first To Do status."""

    title: str
    description: str | None = None
    project_id: UUID
    type_id: UUID
    status_id: UUID | None = None
    labels: Labels = Field(default_factory=list)
    trashed: bool = False


class WorkItem(Timestamped):
    """A stored work item. Its status and type belong to its project."""

    id: UUID
    title: str
    description: str | None = None
    project_id: UUID
    status_id: UUID
    type_id: UUID
    parent_id: UUID | None = None
    labels: list[str] = Field(default_factory=list)
    trashed: bool = False

    @computed_field
    @property
    def rendered_description(self) -> str | None:
        """The description rendered from Markdown to HTML and sanitized."""
        if not self.description:
            return None
        return render_markdown(self.description)


class ProjectStatus(Timestamped):
    """A status a project's work items can be in. Its category is fixed."""

    id: UUID
    project_id: UUID
    name: str
    category: StatusCategory
    position: int


class WorkItemType(Timestamped):
    """A work item type a project defines. Its level is fixed."""

    id: UUID
    project_id: UUID
    name: str
    level: TypeLevel
    position: int


class StatusRef(BaseModel):
    """A work item's status, with what clients need to show it."""

    id: UUID
    name: str
    category: StatusCategory


class TypeRef(BaseModel):
    """A work item's type, with what clients need to show it."""

    id: UUID
    name: str
    level: TypeLevel


class WorkItemDetail(WorkItem):
    """A work item as the API returns it: the stored fields plus its status and type."""

    status: StatusRef
    type: TypeRef


class StatusTransition(Timestamped):
    """An allowed move between two statuses of the same project."""

    id: UUID
    project_id: UUID
    from_status_id: UUID
    to_status_id: UUID


class StatusCreate(BaseModel):
    """A new status in a project. Without a position it is placed last."""

    project_id: UUID
    name: str
    category: StatusCategory
    position: int | None = None


class StatusUpdate(BaseModel):
    name: str | None = None
    category: StatusCategory | None = None
    position: int | None = None

    _reject_null_name = field_validator("name")(reject_null)
    _reject_null_category = field_validator("category")(reject_null)
    _reject_null_position = field_validator("position")(reject_null)


class StatusReplace(BaseModel):
    """Full replacement. Without a position the status keeps its current one."""

    name: str
    category: StatusCategory
    position: int | None = None


class WorkItemTypeCreate(BaseModel):
    """A new work item type in a project. Without a position it is placed last."""

    project_id: UUID
    name: str
    level: TypeLevel
    position: int | None = None


class WorkItemTypeUpdate(BaseModel):
    name: str | None = None
    level: TypeLevel | None = None
    position: int | None = None

    _reject_null_name = field_validator("name")(reject_null)
    _reject_null_level = field_validator("level")(reject_null)
    _reject_null_position = field_validator("position")(reject_null)


class WorkItemTypeReplace(BaseModel):
    """Full replacement. Without a position the type keeps its current one."""

    name: str
    level: TypeLevel
    position: int | None = None


class StatusTransitionCreate(BaseModel):
    project_id: UUID
    from_status_id: UUID
    to_status_id: UUID


class StatusTransitionUpdate(BaseModel):
    from_status_id: UUID | None = None
    to_status_id: UUID | None = None

    _reject_null_from = field_validator("from_status_id")(reject_null)
    _reject_null_to = field_validator("to_status_id")(reject_null)


class StatusTransitionReplace(BaseModel):
    from_status_id: UUID
    to_status_id: UUID


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    labels: Labels = Field(default_factory=list)


class ProjectCreateRequest(ProjectCreate):
    """Project creation request. The template is only used when the project is made."""

    template: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    labels: Labels = Field(default_factory=list)

    _reject_null_name = field_validator("name")(reject_null)


class ProjectReplace(BaseModel):
    name: str
    description: str | None = None
    labels: Labels = Field(default_factory=list)


class Project(ProjectCreate, Timestamped):
    id: UUID


class BoardCreate(BaseModel):
    """A kanban board in a project. Its filter narrows the project's work items."""

    name: str
    description: str | None = None
    project_id: UUID
    filter: str | None = None
    labels: Labels = Field(default_factory=list)


class BoardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    project_id: UUID | None = None
    filter: str | None = None
    labels: Labels = Field(default_factory=list)

    _reject_null_name = field_validator("name")(reject_null)


class BoardReplace(BaseModel):
    name: str
    description: str | None = None
    project_id: UUID
    filter: str | None = None
    labels: Labels = Field(default_factory=list)


class Board(BoardCreate, Timestamped):
    id: UUID


class BoardColumn(BaseModel):
    """One of the project's statuses and the board's work items in it."""

    status: ProjectStatus
    items: list[WorkItemDetail]


class BoardView(BaseModel):
    board: Board
    columns: list[BoardColumn]


class FunctionCreate(BaseModel):
    """A saved Python script. Its dependencies go in a PEP 723 inline header."""

    name: str
    description: str | None = None
    code: str
    labels: Labels = Field(default_factory=list)


class FunctionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    code: str | None = None
    labels: Labels = Field(default_factory=list)

    _reject_null_name = field_validator("name")(reject_null)
    _reject_null_code = field_validator("code")(reject_null)


class FunctionReplace(BaseModel):
    name: str
    description: str | None = None
    code: str
    labels: Labels = Field(default_factory=list)


class Function(FunctionCreate, Timestamped):
    id: UUID


class InvocationCreate(BaseModel):
    """The saved output of one run of a function."""

    function_id: UUID
    stdout: str
    stderr: str
    exit_code: int


class Invocation(Timestamped):
    """A stored run of a function: what it printed and how it exited."""

    id: UUID
    function_id: UUID
    stdout: str
    stderr: str
    exit_code: int


class RunRequest(BaseModel):
    """Input to any runner: a Python script and how long it may run."""

    code: str
    timeout_seconds: int = 120


class RunResult(BaseModel):
    """What a runner printed and how the script exited.

    A run that exceeds its timeout has ``exit_code`` -1.
    """

    stdout: str
    stderr: str
    exit_code: int


class PaginatedResponse[T](BaseModel):
    """Generic paginated response model."""

    results: list[T]
    limit: int
    offset: int
    total: int


class StatusCount(BaseModel):
    """Number of work items in one status."""

    status: ProjectStatus
    count: int


class WorkItemCounts(BaseModel):
    """Number of work items in total, in each status category and in each status."""

    total: int
    todo: int
    in_progress: int
    done: int
    by_status: list[StatusCount]


class ReportSummary(BaseModel):
    """Headline counts for the dashboard."""

    projects: int
    boards: int
    work_items: WorkItemCounts
