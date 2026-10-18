from uuid import UUID

from kangaroo.errors import (
    ConflictError,
    InvalidReferenceError,
    NotFoundError,
)
from kangaroo.repositories import (
    ProjectRepository,
    StatusRepository,
    StatusTransitionRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
)
from kangaroo.schemas import (
    PaginatedResponse,
    WorkItem,
    WorkItemCreate,
    WorkItemDetail,
    WorkItemReplace,
    WorkItemUpdate,
)
from kangaroo.services.helpers import (
    detail,
    ensure_project_exists,
    filter_record,
    filtered_page,
    get_in_project,
    in_position_order,
    lookups,
    project_names,
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
        ensure_project_exists(self._projects, item.project_id)
        work_item_type = get_in_project(
            self._types, item.type_id, item.project_id, "Work item type"
        )
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
            statuses, types = lookups(self._statuses, self._types)
            return PaginatedResponse[WorkItemDetail](
                results=[detail(item, statuses, types) for item in page.results],
                limit=page.limit,
                offset=page.offset,
                total=page.total,
            )
        names = project_names(self._projects)
        statuses, types = lookups(self._statuses, self._types)
        page, total = filtered_page(
            self._work_items.list_all(project_id=project_id, parent_id=parent_id),
            filter,
            lambda item: filter_record(item, names, statuses, types),
            search,
            self._work_items.search_fields,
            limit,
            offset,
        )
        return PaginatedResponse[WorkItemDetail](
            results=[detail(item, statuses, types) for item in page],
            limit=limit,
            offset=offset,
            total=total,
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
            ensure_project_exists(self._projects, update.project_id)
            project_id = update.project_id or current.project_id
        moved = project_id != current.project_id
        if moved:
            self._ensure_project_can_change(current)
            update = update.model_copy(
                update={
                    "status_id": self._project_status_or_default(
                        project_id, update.status_id
                    ),
                    "type_id": update.type_id
                    or self._project_type_or_default(project_id, current),
                }
            )
        type_id = update.type_id
        if type_id is not None:
            self._ensure_type_change(current, project_id, type_id)
        status_id = update.status_id
        if status_id is not None:
            self._ensure_status_change(current, project_id, status_id, moved)
        return self._with_names(self._work_items.update(item_id, update))

    def replace(self, item_id: UUID, replace: WorkItemReplace) -> WorkItemDetail:
        """Replace a work item (full update).

        Without a ``status_id`` the item goes to the project's first To Do status.
        """
        current = self._work_items.get_by_id(item_id)
        ensure_project_exists(self._projects, replace.project_id)
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
        return detail(
            item,
            {item.status_id: self._statuses.get_by_id(item.status_id)},
            {item.type_id: self._types.get_by_id(item.type_id)},
        )

    def _project_status_or_default(
        self, project_id: UUID, status_id: UUID | None
    ) -> UUID:
        """Check the given status, or pick the project's first To Do status."""
        if status_id is not None:
            return get_in_project(self._statuses, status_id, project_id, "Status").id
        todo = next(
            (
                status
                for status in in_position_order(
                    self._statuses.list_all(project_id=project_id)
                )
                if status.category == "todo"
            ),
            None,
        )
        if todo is None:
            raise InvalidReferenceError("The project has no To Do status")
        return todo.id

    def _project_type_or_default(self, project_id: UUID, current: WorkItem) -> UUID:
        """Pick the project's first type with the same level as the item's type."""
        level = self._types.get_by_id(current.type_id).level
        for work_item_type in in_position_order(
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
        new_type = get_in_project(self._types, type_id, project_id, "Work item type")
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
        get_in_project(self._statuses, status_id, project_id, "Status")
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
