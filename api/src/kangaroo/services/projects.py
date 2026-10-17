from uuid import UUID

from kangaroo.errors import (
    ConflictError,
    InvalidTemplateError,
)
from kangaroo.repositories import (
    BoardRepository,
    ProjectRepository,
    StatusRepository,
    StatusTransitionRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
)
from kangaroo.schemas import (
    PaginatedResponse,
    Project,
    ProjectCreate,
    ProjectReplace,
    ProjectUpdate,
    StatusCreate,
    StatusTransitionCreate,
    WorkItemTypeCreate,
)
from kangaroo.templates import DEFAULT_TEMPLATE_NAME, TEMPLATES


class ProjectService:
    """Business rules for projects."""

    def __init__(
        self,
        projects: ProjectRepository,
        work_items: WorkItemRepository,
        boards: BoardRepository,
        statuses: StatusRepository,
        types: WorkItemTypeRepository,
        transitions: StatusTransitionRepository,
    ) -> None:
        self._projects = projects
        self._work_items = work_items
        self._boards = boards
        self._statuses = statuses
        self._types = types
        self._transitions = transitions

    def create(self, item: ProjectCreate, template: str | None = None) -> Project:
        """Create a project and copy a template's types and statuses into it.

        The template defaults to "To Do List". The copy is independent: nothing
        stored refers back to the template. An unknown template raises
        InvalidTemplateError before anything is created.
        """
        chosen = TEMPLATES.get(DEFAULT_TEMPLATE_NAME if template is None else template)
        if chosen is None:
            raise InvalidTemplateError(f"Unknown template {template!r}")
        project = self._projects.create(item)
        for template_type in chosen.types:
            self._types.create(
                WorkItemTypeCreate(
                    project_id=project.id,
                    name=template_type.name,
                    level=template_type.level,
                    position=template_type.position,
                )
            )
        status_ids: dict[str, UUID] = {}
        for template_status in chosen.statuses:
            status = self._statuses.create(
                StatusCreate(
                    project_id=project.id,
                    name=template_status.name,
                    category=template_status.category,
                    position=template_status.position,
                )
            )
            status_ids[template_status.name] = status.id
        for from_name, to_name in chosen.transitions:
            self._transitions.create(
                StatusTransitionCreate(
                    project_id=project.id,
                    from_status_id=status_ids[from_name],
                    to_status_id=status_ids[to_name],
                )
            )
        return project

    def list_paginated(
        self, limit: int, offset: int, search: str | None = None
    ) -> PaginatedResponse[Project]:
        """List projects with pagination."""
        return self._projects.list_paginated(limit, offset, search)

    def get(self, item_id: UUID) -> Project:
        """Get a project by ID."""
        return self._projects.get_by_id(item_id)

    def update(self, item_id: UUID, update: ProjectUpdate) -> Project:
        """Update a project (partial update)."""
        return self._projects.update(item_id, update)

    def replace(self, item_id: UUID, replace: ProjectReplace) -> Project:
        """Replace a project (full update)."""
        return self._projects.replace(item_id, replace)

    def delete(self, item_id: UUID) -> None:
        """Delete a project. Projects with work items or boards are protected."""
        if self._work_items.count(project_id=item_id) > 0:
            raise ConflictError("Project still has work items")
        if self._boards.count(project_id=item_id) > 0:
            raise ConflictError("Project still has boards")
        for transition in self._transitions.list_all(project_id=item_id):
            self._transitions.delete(transition.id)
        for status in self._statuses.list_all(project_id=item_id):
            self._statuses.delete(status.id)
        for work_item_type in self._types.list_all(project_id=item_id):
            self._types.delete(work_item_type.id)
        self._projects.delete(item_id)
