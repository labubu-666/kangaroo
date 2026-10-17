from uuid import UUID

from kangaroo.errors import (
    ConflictError,
    InvalidReferenceError,
    NotFoundError,
)
from kangaroo.filters import parse_filter
from kangaroo.repositories import (
    ProjectRepository,
    StatusRepository,
    StatusTransitionRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
)
from kangaroo.repositories.repositories import clean_search, matches_search
from kangaroo.schemas import (
    PaginatedResponse,
    ProjectStatus,
    WorkItem,
    WorkItemCreate,
    WorkItemDetail,
    WorkItemReplace,
    WorkItemType,
    WorkItemUpdate,
)
from kangaroo.services.helpers import (
    _detail,
    _ensure_project_exists,
    _filter_record,
    _in_position_order,
    _lookups,
    _project_names,
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
        work_items: WorkItemRepository,
        projects: ProjectRepository,
        statuses: StatusRepository,
        types: WorkItemTypeRepository,
        transitions: StatusTransitionRepository,
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
