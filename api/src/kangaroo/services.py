from typing import Any
from uuid import UUID

from kangaroo.backends import (
    BoardBackend,
    FunctionBackend,
    ProjectBackend,
    StatusBackend,
    StatusTransitionBackend,
    WorkItemBackend,
    WorkItemTypeBackend,
)
from kangaroo.backends.base import BaseBackend, clean_search, matches_search
from kangaroo.errors import (
    ConflictError,
    InvalidReferenceError,
    InvalidTemplateError,
    NotFoundError,
)
from kangaroo.filters import parse_filter
from kangaroo.runners import BaseRunner
from kangaroo.schemas import (
    Board,
    BoardColumn,
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    BoardView,
    Function,
    FunctionCreate,
    FunctionReplace,
    FunctionUpdate,
    PaginatedResponse,
    Project,
    ProjectCreate,
    ProjectReplace,
    ProjectStatus,
    ProjectUpdate,
    ReportSummary,
    RunRequest,
    RunResult,
    StatusCount,
    StatusCreate,
    StatusRef,
    StatusReplace,
    StatusTransition,
    StatusTransitionCreate,
    StatusTransitionReplace,
    StatusTransitionUpdate,
    StatusUpdate,
    TypeRef,
    WorkItem,
    WorkItemCounts,
    WorkItemCreate,
    WorkItemDetail,
    WorkItemReplace,
    WorkItemType,
    WorkItemTypeCreate,
    WorkItemTypeReplace,
    WorkItemTypeUpdate,
    WorkItemUpdate,
)
from kangaroo.templates import DEFAULT_TEMPLATE_NAME, TEMPLATES


def _ensure_project_exists(projects: ProjectBackend, project_id: UUID | None) -> None:
    """Raise InvalidReferenceError if the project is null or does not exist."""
    if project_id is None:
        raise InvalidReferenceError("project_id cannot be null")
    try:
        projects.get_by_id(project_id)
    except NotFoundError:
        raise InvalidReferenceError("Project not found") from None


def _project_names(projects: ProjectBackend) -> dict[UUID, str]:
    """Map each project ID to its name."""
    return {project.id: project.name for project in projects.list_all()}


def _filter_record(
    item: WorkItem,
    project_names: dict[UUID, str],
    statuses: dict[UUID, ProjectStatus],
    types: dict[UUID, WorkItemType],
) -> dict[str, Any]:
    """Flatten a work item into the record that filter predicates read."""
    status = statuses.get(item.status_id)
    work_item_type = types.get(item.type_id)
    return {
        "title": item.title,
        "description": item.description,
        "status": status.name if status else None,
        "status_id": str(item.status_id),
        "statusCategory": status.category if status else None,
        "type": work_item_type.name if work_item_type else None,
        "type_id": str(item.type_id),
        "typeLevel": work_item_type.level if work_item_type else None,
        "parent_id": str(item.parent_id) if item.parent_id else None,
        "project.id": str(item.project_id),
        "project.name": project_names.get(item.project_id),
        "labels": item.labels,
        "trashed": "true" if item.trashed else "false",
    }


def _board_record(board: Board, project_names: dict[UUID, str]) -> dict[str, Any]:
    """Flatten a board into the record that filter predicates read.

    A board's name is its ``title``. Work-item-only fields are None, so a filter
    on them never matches a board.
    """
    return {
        "title": board.name,
        "description": board.description,
        "status": None,
        "status_id": None,
        "statusCategory": None,
        "type": None,
        "type_id": None,
        "typeLevel": None,
        "parent_id": None,
        "project.id": str(board.project_id),
        "project.name": project_names.get(board.project_id),
        "labels": [],
        "trashed": None,
    }


def _lookups(
    statuses: StatusBackend, types: WorkItemTypeBackend
) -> tuple[dict[UUID, ProjectStatus], dict[UUID, WorkItemType]]:
    """Map every status ID and work item type ID to its row."""
    return (
        {status.id: status for status in statuses.list_all()},
        {work_item_type.id: work_item_type for work_item_type in types.list_all()},
    )


def _detail(
    item: WorkItem,
    statuses: dict[UUID, ProjectStatus],
    types: dict[UUID, WorkItemType],
) -> WorkItemDetail:
    """Add the item's status and type to the stored work item."""
    status = statuses[item.status_id]
    work_item_type = types[item.type_id]
    return WorkItemDetail(
        **item.model_dump(exclude={"rendered_description"}),
        status=StatusRef(id=status.id, name=status.name, category=status.category),
        type=TypeRef(
            id=work_item_type.id, name=work_item_type.name, level=work_item_type.level
        ),
    )


class WorkItemService:
    """Business rules for work items.

    Referenced projects, statuses, types and parents must exist and fit
    together, and the structure (tasks, subtasks) must stay consistent when
    items are changed. Whether an item is a subtask comes from the level of its
    type, not from the type's name.
    """

    def __init__(
        self,
        work_items: WorkItemBackend,
        projects: ProjectBackend,
        statuses: StatusBackend,
        types: WorkItemTypeBackend,
        transitions: StatusTransitionBackend,
    ) -> None:
        self._work_items = work_items
        self._projects = projects
        self._statuses = statuses
        self._types = types
        self._transitions = transitions

    def create(self, item: WorkItemCreate) -> WorkItemDetail:
        """Create a work item, checking its project, type, status and parent."""
        _ensure_project_exists(self._projects, item.project_id)
        work_item_type = self._project_type(item.project_id, item.type_id)
        status_id = self._project_status_or_default(item.project_id, item.status_id)
        if work_item_type.level == "subtask":
            if item.parent_id is None:
                raise InvalidReferenceError("A subtask needs a parent_id")
            self._ensure_valid_parent(item.project_id, item.parent_id)
        elif item.parent_id is not None:
            raise InvalidReferenceError("Only a subtask can have a parent_id")
        created = self._work_items.create(
            item.model_copy(update={"status_id": status_id})
        )
        return self._with_names(created)

    def list_paginated(
        self,
        limit: int,
        offset: int,
        project_id: UUID | None = None,
        parent_id: UUID | None = None,
        search: str | None = None,
        filter: str | None = None,
    ) -> PaginatedResponse[WorkItemDetail]:
        """List work items with pagination, including trashed ones.

        With a filter, the items are checked against it in Python first, then
        ``search`` and the page are applied to the matches.
        """
        if not filter or not filter.strip():
            page = self._work_items.list_paginated(
                limit,
                offset,
                search,
                project_id=project_id,
                parent_id=parent_id,
            )
            statuses, types = _lookups(self._statuses, self._types)
            return PaginatedResponse[WorkItemDetail](
                results=[_detail(item, statuses, types) for item in page.results],
                limit=page.limit,
                offset=page.offset,
                total=page.total,
            )
        matches = parse_filter(filter)
        project_names = _project_names(self._projects)
        statuses, types = _lookups(self._statuses, self._types)
        candidates = self._work_items.list_all(
            project_id=project_id, parent_id=parent_id
        )
        text = clean_search(search)
        fields = self._work_items.search_fields
        matched = [
            item
            for item in candidates
            if matches(_filter_record(item, project_names, statuses, types))
            and (text is None or matches_search(item, text, fields))
        ]
        return PaginatedResponse[WorkItemDetail](
            results=[
                _detail(item, statuses, types)
                for item in matched[offset : offset + limit]
            ],
            limit=limit,
            offset=offset,
            total=len(matched),
        )

    def get(self, item_id: UUID) -> WorkItemDetail:
        """Get a work item by ID."""
        return self._with_names(self._work_items.get_by_id(item_id))

    def update(self, item_id: UUID, update: WorkItemUpdate) -> WorkItemDetail:
        """Update a work item (partial update).

        Moving to another project without a status or type picks the new
        project's first To Do status and first type of the same level.
        """
        current = self._work_items.get_by_id(item_id)
        fields = update.model_fields_set
        project_id = current.project_id
        if "project_id" in fields:
            _ensure_project_exists(self._projects, update.project_id)
            project_id = update.project_id
        moved = project_id != current.project_id
        if moved:
            self._ensure_project_can_change(current)
            update = WorkItemUpdate(
                **{
                    **update.model_dump(exclude_unset=True),
                    "status_id": self._project_status_or_default(
                        project_id, update.status_id
                    ),
                    "type_id": update.type_id
                    or self._project_type_or_default(project_id, current),
                }
            )
        if update.type_id is not None:
            self._ensure_type_change(current, project_id, update.type_id)
        if update.status_id is not None:
            self._ensure_status_change(current, project_id, update.status_id, moved)
        return self._with_names(self._work_items.update(item_id, update))

    def replace(self, item_id: UUID, replace: WorkItemReplace) -> WorkItemDetail:
        """Replace a work item (full update).

        Without a ``status_id`` the item goes to the project's first To Do status.
        """
        current = self._work_items.get_by_id(item_id)
        _ensure_project_exists(self._projects, replace.project_id)
        moved = replace.project_id != current.project_id
        if moved:
            self._ensure_project_can_change(current)
        self._ensure_type_change(current, replace.project_id, replace.type_id)
        status_id = self._project_status_or_default(
            replace.project_id, replace.status_id
        )
        self._ensure_status_change(current, replace.project_id, status_id, moved)
        replaced = self._work_items.replace(
            item_id, replace.model_copy(update={"status_id": status_id})
        )
        return self._with_names(replaced)

    def delete(self, item_id: UUID) -> None:
        """Delete a work item. A task that still has subtasks cannot be deleted."""
        if self._work_items.count(parent_id=item_id) > 0:
            raise ConflictError(f"Work item {item_id} still has subtasks")
        self._work_items.delete(item_id)

    def _with_names(self, item: WorkItem) -> WorkItemDetail:
        """Add the status and type of a single stored item."""
        return _detail(
            item,
            {item.status_id: self._statuses.get_by_id(item.status_id)},
            {item.type_id: self._types.get_by_id(item.type_id)},
        )

    def _project_type(self, project_id: UUID, type_id: UUID) -> WorkItemType:
        """The type must exist and belong to the project."""
        try:
            work_item_type = self._types.get_by_id(type_id)
        except NotFoundError:
            raise InvalidReferenceError("Work item type not found") from None
        if work_item_type.project_id != project_id:
            raise InvalidReferenceError("Work item type is not in the project")
        return work_item_type

    def _project_status(self, project_id: UUID, status_id: UUID) -> ProjectStatus:
        """The status must exist and belong to the project."""
        try:
            status = self._statuses.get_by_id(status_id)
        except NotFoundError:
            raise InvalidReferenceError("Status not found") from None
        if status.project_id != project_id:
            raise InvalidReferenceError("Status is not in the project")
        return status

    def _project_status_or_default(
        self, project_id: UUID, status_id: UUID | None
    ) -> UUID:
        """Check the given status, or pick the project's first To Do status."""
        if status_id is not None:
            return self._project_status(project_id, status_id).id
        todo = [
            status
            for status in _in_position_order(
                self._statuses.list_all(project_id=project_id)
            )
            if status.category == "todo"
        ]
        if not todo:
            raise InvalidReferenceError("The project has no To Do status")
        return todo[0].id

    def _project_type_or_default(self, project_id: UUID, current: WorkItem) -> UUID:
        """Pick the project's first type with the same level as the item's type."""
        level = self._types.get_by_id(current.type_id).level
        for work_item_type in _in_position_order(
            self._types.list_all(project_id=project_id)
        ):
            if work_item_type.level == level:
                return work_item_type.id
        raise InvalidReferenceError(f"The project has no {level} type")

    def _ensure_valid_parent(self, project_id: UUID, parent_id: UUID) -> None:
        """A subtask's parent must be a standard-level item in the same project."""
        try:
            parent = self._work_items.get_by_id(parent_id)
        except NotFoundError:
            raise InvalidReferenceError("Parent work item not found") from None
        parent_type = self._types.get_by_id(parent.type_id)
        if parent_type.level != "standard":
            raise InvalidReferenceError("Parent work item must be a task")
        if parent.project_id != project_id:
            raise InvalidReferenceError(
                "Subtask must be in the same project as its parent"
            )

    def _ensure_type_change(
        self, current: WorkItem, project_id: UUID, type_id: UUID
    ) -> None:
        """The new type must be in the project and keep the item's level.

        The parent/subtask links depend on the level, so it cannot change.
        """
        new_type = self._project_type(project_id, type_id)
        old_type = self._types.get_by_id(current.type_id)
        if new_type.level != old_type.level:
            raise ConflictError("A work item cannot change type level")

    def _ensure_status_change(
        self, current: WorkItem, project_id: UUID, status_id: UUID, moved: bool
    ) -> None:
        """The status must be in the project and reachable by a transition.

        A project without transitions allows every change. A move to another
        project starts fresh, so no transition is needed.
        """
        self._project_status(project_id, status_id)
        if moved or status_id == current.status_id:
            return
        allowed = self._transitions.list_all(project_id=project_id)
        if allowed and not any(
            transition.from_status_id == current.status_id
            and transition.to_status_id == status_id
            for transition in allowed
        ):
            raise ConflictError("The workflow does not allow this status change")

    def _ensure_project_can_change(self, item: WorkItem) -> None:
        """Only tasks without subtasks can move between projects."""
        item_type = self._types.get_by_id(item.type_id)
        if (
            item_type.level == "subtask"
            or self._work_items.count(parent_id=item.id) > 0
        ):
            raise ConflictError(
                "Tasks with subtasks and subtasks cannot change project"
            )


class ProjectService:
    """Business rules for projects."""

    def __init__(
        self,
        projects: ProjectBackend,
        work_items: WorkItemBackend,
        boards: BoardBackend,
        statuses: StatusBackend,
        types: WorkItemTypeBackend,
        transitions: StatusTransitionBackend,
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


def _next_position(backend: BaseBackend, project_id: UUID) -> int:
    """Place a new item after the last position already used in the project."""
    positions = [item.position for item in backend.list_all(project_id=project_id)]
    return max(positions, default=-1) + 1


def _in_position_order[M: (ProjectStatus, WorkItemType)](items: list[M]) -> list[M]:
    """Sort by position. Items that share a position keep their creation order."""
    return sorted(items, key=lambda item: item.position)


class WorkflowService:
    """Business rules for a project's statuses, work item types and transitions.

    Statuses and types belong to one project and are kept in position order. A
    project always keeps at least one ``todo`` status, so new work items have a
    starting point. A transition must join two statuses of its own project.
    """

    def __init__(
        self,
        projects: ProjectBackend,
        statuses: StatusBackend,
        types: WorkItemTypeBackend,
        transitions: StatusTransitionBackend,
        work_items: WorkItemBackend,
    ) -> None:
        self._projects = projects
        self._statuses = statuses
        self._types = types
        self._transitions = transitions
        self._work_items = work_items

    def list_statuses(self, project_id: UUID) -> list[ProjectStatus]:
        """List a project's statuses in position order."""
        return _in_position_order(self._statuses.list_all(project_id=project_id))

    def create_status(self, item: StatusCreate) -> ProjectStatus:
        """Create a status. Without a position it is placed last."""
        _ensure_project_exists(self._projects, item.project_id)
        if item.position is None:
            item = item.model_copy(
                update={"position": _next_position(self._statuses, item.project_id)}
            )
        return self._statuses.create(item)

    def get_status(self, item_id: UUID) -> ProjectStatus:
        """Get a status by ID."""
        return self._statuses.get_by_id(item_id)

    def update_status(self, item_id: UUID, update: StatusUpdate) -> ProjectStatus:
        """Update a status (partial update)."""
        current = self._statuses.get_by_id(item_id)
        new_category = update.category or current.category
        if current.category == "todo" and new_category != "todo":
            self._ensure_other_todo_status(current)
        return self._statuses.update(item_id, update)

    def replace_status(self, item_id: UUID, replace: StatusReplace) -> ProjectStatus:
        """Replace a status (full update). Without a position it keeps its place."""
        current = self._statuses.get_by_id(item_id)
        if current.category == "todo" and replace.category != "todo":
            self._ensure_other_todo_status(current)
        position = current.position if replace.position is None else replace.position
        return self._statuses.replace(
            item_id, replace.model_copy(update={"position": position})
        )

    def delete_status(self, item_id: UUID, replacement_id: UUID | None = None) -> None:
        """Delete a status and the transitions that use it.

        If work items use the status, ``replacement_id`` must name another status of
        the same project. Those items move to it first. Without one the delete is
        refused with a 409 that says how many items would be affected.
        """
        status = self._statuses.get_by_id(item_id)
        affected = self._work_items.count(status_id=item_id)
        if affected:
            if replacement_id is None:
                raise ConflictError(
                    f"{affected} work items use this status; choose a replacement"
                )
            if replacement_id == item_id:
                raise InvalidReferenceError("The replacement must be another status")
            replacement = self._statuses.get_by_id(replacement_id)
            if replacement.project_id != status.project_id:
                raise InvalidReferenceError(
                    "The replacement must be in the same project"
                )
            self._move_items(status_id=item_id, to_status_id=replacement_id)
        if status.category == "todo":
            self._ensure_other_todo_status(status)
        for transition in self._transitions.list_all(project_id=status.project_id):
            if item_id in (transition.from_status_id, transition.to_status_id):
                self._transitions.delete(transition.id)
        self._statuses.delete(item_id)

    def _move_items(
        self,
        *,
        status_id: UUID | None = None,
        type_id: UUID | None = None,
        to_status_id: UUID | None = None,
        to_type_id: UUID | None = None,
    ) -> None:
        """Point every work item that uses a status or type at its replacement."""
        filters = {"status_id": status_id, "type_id": type_id}
        for item in self._work_items.list_all(
            **{k: v for k, v in filters.items() if v is not None}
        ):
            update = {}
            if to_status_id is not None and item.status_id == status_id:
                update["status_id"] = to_status_id
            if to_type_id is not None and item.type_id == type_id:
                update["type_id"] = to_type_id
            if update:
                self._work_items.update(item.id, WorkItemUpdate(**update))

    def _ensure_other_todo_status(self, status: ProjectStatus) -> None:
        """Raise ConflictError if ``status`` is the project's only To Do status."""
        others = [
            other
            for other in self._statuses.list_all(project_id=status.project_id)
            if other.id != status.id and other.category == "todo"
        ]
        if not others:
            raise ConflictError("A project needs at least one To Do status")

    def _ensure_statuses_in_project(self, project_id: UUID, *status_ids: UUID) -> None:
        """Each status must exist and belong to ``project_id``."""
        for status_id in status_ids:
            try:
                status = self._statuses.get_by_id(status_id)
            except NotFoundError:
                raise InvalidReferenceError("Status not found") from None
            if status.project_id != project_id:
                raise InvalidReferenceError(
                    "Status must be in the same project as its transition"
                )

    def list_work_item_types(self, project_id: UUID) -> list[WorkItemType]:
        """List a project's work item types in position order."""
        return _in_position_order(self._types.list_all(project_id=project_id))

    def create_work_item_type(self, item: WorkItemTypeCreate) -> WorkItemType:
        """Create a work item type. Without a position it is placed last."""
        _ensure_project_exists(self._projects, item.project_id)
        if item.position is None:
            item = item.model_copy(
                update={"position": _next_position(self._types, item.project_id)}
            )
        return self._types.create(item)

    def get_work_item_type(self, item_id: UUID) -> WorkItemType:
        """Get a work item type by ID."""
        return self._types.get_by_id(item_id)

    def update_work_item_type(
        self, item_id: UUID, update: WorkItemTypeUpdate
    ) -> WorkItemType:
        """Update a work item type (partial update)."""
        return self._types.update(item_id, update)

    def replace_work_item_type(
        self, item_id: UUID, replace: WorkItemTypeReplace
    ) -> WorkItemType:
        """Replace a work item type (full update). Without a position it keeps its place."""
        current = self._types.get_by_id(item_id)
        position = current.position if replace.position is None else replace.position
        return self._types.replace(
            item_id, replace.model_copy(update={"position": position})
        )

    def delete_work_item_type(
        self, item_id: UUID, replacement_id: UUID | None = None
    ) -> None:
        """Delete a work item type.

        If work items use the type, ``replacement_id`` must name another type of the
        same project and level. Those items move to it first. Without one the delete
        is refused with a 409 that says how many items would be affected.
        """
        work_item_type = self._types.get_by_id(item_id)
        affected = self._work_items.count(type_id=item_id)
        if affected:
            if replacement_id is None:
                raise ConflictError(
                    f"{affected} work items use this type; choose a replacement"
                )
            if replacement_id == item_id:
                raise InvalidReferenceError("The replacement must be another type")
            replacement = self._types.get_by_id(replacement_id)
            if replacement.project_id != work_item_type.project_id:
                raise InvalidReferenceError(
                    "The replacement must be in the same project"
                )
            if replacement.level != work_item_type.level:
                raise InvalidReferenceError("The replacement must have the same level")
            self._move_items(type_id=item_id, to_type_id=replacement_id)
        self._types.delete(item_id)

    def list_transitions(self, project_id: UUID) -> list[StatusTransition]:
        """List a project's status transitions."""
        return self._transitions.list_all(project_id=project_id)

    def create_transition(self, item: StatusTransitionCreate) -> StatusTransition:
        """Create a transition between two statuses of the same project."""
        _ensure_project_exists(self._projects, item.project_id)
        self._ensure_statuses_in_project(
            item.project_id, item.from_status_id, item.to_status_id
        )
        return self._transitions.create(item)

    def get_transition(self, item_id: UUID) -> StatusTransition:
        """Get a status transition by ID."""
        return self._transitions.get_by_id(item_id)

    def update_transition(
        self, item_id: UUID, update: StatusTransitionUpdate
    ) -> StatusTransition:
        """Update a transition (partial update), checking its statuses."""
        current = self._transitions.get_by_id(item_id)
        from_id = current.from_status_id
        if update.from_status_id is not None:
            from_id = update.from_status_id
        to_id = current.to_status_id
        if update.to_status_id is not None:
            to_id = update.to_status_id
        self._ensure_statuses_in_project(current.project_id, from_id, to_id)
        return self._transitions.update(item_id, update)

    def replace_transition(
        self, item_id: UUID, replace: StatusTransitionReplace
    ) -> StatusTransition:
        """Replace a transition (full update), checking its statuses."""
        current = self._transitions.get_by_id(item_id)
        self._ensure_statuses_in_project(
            current.project_id, replace.from_status_id, replace.to_status_id
        )
        return self._transitions.replace(item_id, replace)

    def delete_transition(self, item_id: UUID) -> None:
        """Delete a status transition."""
        self._transitions.delete(item_id)


class BoardService:
    """Business rules for boards.

    A board belongs to a project and must reference an existing one. Its filter
    is checked when it is saved, so a board never holds an invalid filter. Its
    view groups the matching work items of its project by status.
    """

    def __init__(
        self,
        boards: BoardBackend,
        work_items: WorkItemBackend,
        projects: ProjectBackend,
        statuses: StatusBackend,
        types: WorkItemTypeBackend,
    ) -> None:
        self._boards = boards
        self._work_items = work_items
        self._projects = projects
        self._statuses = statuses
        self._types = types

    def create(self, item: BoardCreate) -> Board:
        """Create a board after checking its project and filter."""
        _ensure_project_exists(self._projects, item.project_id)
        parse_filter(item.filter)
        return self._boards.create(item)

    def list_paginated(
        self,
        limit: int,
        offset: int,
        search: str | None = None,
        project_id: UUID | None = None,
        filter: str | None = None,
    ) -> PaginatedResponse[Board]:
        """List boards with pagination, optionally only those of one project.

        With a filter, the boards are checked against it in Python first, then
        ``search`` and the page are applied to the matches.
        """
        if not filter or not filter.strip():
            return self._boards.list_paginated(
                limit, offset, search, project_id=project_id
            )
        matches = parse_filter(filter)
        project_names = _project_names(self._projects)
        candidates = self._boards.list_all(project_id=project_id)
        text = clean_search(search)
        fields = self._boards.search_fields
        matched = [
            board
            for board in candidates
            if matches(_board_record(board, project_names))
            and (text is None or matches_search(board, text, fields))
        ]
        return PaginatedResponse[Board](
            results=matched[offset : offset + limit],
            limit=limit,
            offset=offset,
            total=len(matched),
        )

    def get(self, item_id: UUID) -> Board:
        """Get a board by ID."""
        return self._boards.get_by_id(item_id)

    def update(self, item_id: UUID, update: BoardUpdate) -> Board:
        """Update a board (partial update) after checking its project and filter."""
        if "project_id" in update.model_fields_set:
            _ensure_project_exists(self._projects, update.project_id)
        if "filter" in update.model_fields_set:
            parse_filter(update.filter)
        return self._boards.update(item_id, update)

    def replace(self, item_id: UUID, replace: BoardReplace) -> Board:
        """Replace a board (full update) after checking its project and filter."""
        _ensure_project_exists(self._projects, replace.project_id)
        parse_filter(replace.filter)
        return self._boards.replace(item_id, replace)

    def delete(self, item_id: UUID) -> None:
        """Delete a board."""
        self._boards.delete(item_id)

    def view(self, item_id: UUID) -> BoardView:
        """Return the board with its project's matching work items grouped by status.

        Every status of the project is a column, in position order, even when it
        has no work items.
        """
        board = self._boards.get_by_id(item_id)
        matches = parse_filter(board.filter)
        project_names = _project_names(self._projects)
        statuses, types = _lookups(self._statuses, self._types)
        project_statuses = _in_position_order(
            self._statuses.list_all(project_id=board.project_id)
        )
        columns: dict[UUID, list[WorkItemDetail]] = {
            status.id: [] for status in project_statuses
        }
        for item in self._work_items.list_all(
            project_id=board.project_id, trashed=False
        ):
            if matches(_filter_record(item, project_names, statuses, types)):
                columns[item.status_id].append(_detail(item, statuses, types))
        return BoardView(
            board=board,
            columns=[
                BoardColumn(status=status, items=columns[status.id])
                for status in project_statuses
            ],
        )


class FunctionService:
    """Stores saved scripts and runs them through a runner."""

    def __init__(self, functions: FunctionBackend, runner: BaseRunner) -> None:
        self._functions = functions
        self._runner = runner

    def create(self, item: FunctionCreate) -> Function:
        return self._functions.create(item)

    def get(self, item_id: UUID) -> Function:
        return self._functions.get_by_id(item_id)

    def list_paginated(
        self, limit: int, offset: int, search: str | None = None
    ) -> PaginatedResponse[Function]:
        return self._functions.list_paginated(limit, offset, search)

    def replace(self, item_id: UUID, replace: FunctionReplace) -> Function:
        return self._functions.replace(item_id, replace)

    def update(self, item_id: UUID, update: FunctionUpdate) -> Function:
        return self._functions.update(item_id, update)

    def delete(self, item_id: UUID) -> None:
        self._functions.delete(item_id)

    def run(self, item_id: UUID) -> RunResult:
        """Run a saved script through the configured runner."""
        function = self._functions.get_by_id(item_id)
        return self._runner.run(RunRequest(code=function.code))


class ReportService:
    """Headline counts across the whole store, for the dashboard."""

    def __init__(
        self,
        work_items: WorkItemBackend,
        projects: ProjectBackend,
        boards: BoardBackend,
        statuses: StatusBackend,
    ) -> None:
        self._work_items = work_items
        self._projects = projects
        self._boards = boards
        self._statuses = statuses

    def summary(self) -> ReportSummary:
        """Count projects, boards and work items, split by status and category."""
        by_status = [
            StatusCount(
                status=status,
                count=self._work_items.count(status_id=status.id, trashed=False),
            )
            for status in self._statuses.list_all()
        ]
        per_category = {"todo": 0, "in_progress": 0, "done": 0}
        for entry in by_status:
            per_category[entry.status.category] += entry.count
        return ReportSummary(
            projects=self._projects.count(),
            boards=self._boards.count(),
            work_items=WorkItemCounts(
                total=self._work_items.count(trashed=False),
                by_status=by_status,
                **per_category,
            ),
        )
