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
from kangaroo.schemas import (
    PaginatedResponse,
    WorkItem,
    WorkItemBulkDelete,
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
    together. A parent can be in any project, but an item can never be its own
    ancestor.
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
        get_in_project(self._types, item.type_id, item.project_id, "Work item type")
        status_id = self._project_status_or_default(item.project_id, item.status_id)
        self._ensure_parent(item.parent_id)
        created = self._work_items.create(
            item.model_copy(update={"status_id": status_id})
        )
        return self._with_names(created)

    def duplicate(self, item_id: UUID) -> WorkItemDetail:
        """Create a copy of a work item with ``<summary> (copy)`` as its summary.

        The copy keeps the original's project, type, status, parent and labels.
        It is never trashed, and the original's children are not copied.
        """
        original = self._work_items.get_by_id(item_id)
        return self.create(
            WorkItemCreate(
                summary=f"{original.summary} (copy)",
                description=original.description,
                project_id=original.project_id,
                type_id=original.type_id,
                status_id=original.status_id,
                parent_id=original.parent_id,
                labels=original.labels,
            )
        )

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
        project's first To Do status and first type.
        """
        current = self._work_items.get_by_id(item_id)
        fields = update.model_fields_set
        project_id = current.project_id
        if "project_id" in fields:
            ensure_project_exists(self._projects, update.project_id)
            project_id = update.project_id or current.project_id
        moved = project_id != current.project_id
        if moved:
            update = update.model_copy(
                update={
                    "status_id": self._project_status_or_default(
                        project_id, update.status_id
                    ),
                    "type_id": update.type_id
                    or self._project_type_or_default(project_id),
                }
            )
        type_id = update.type_id
        if type_id is not None:
            get_in_project(self._types, type_id, project_id, "Work item type")
        if "parent_id" in fields:
            self._ensure_parent(update.parent_id, item_id)
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
        get_in_project(
            self._types, replace.type_id, replace.project_id, "Work item type"
        )
        self._ensure_parent(replace.parent_id, item_id)
        status_id = self._project_status_or_default(
            replace.project_id, replace.status_id
        )
        self._ensure_status_change(current, replace.project_id, status_id, moved)
        replaced = self._work_items.replace(
            item_id, replace.model_copy(update={"status_id": status_id})
        )
        return self._with_names(replaced)

    def delete(self, item_id: UUID) -> None:
        """Delete a work item together with its children."""
        self._delete_tree(item_id)

    def bulk_delete(self, request: WorkItemBulkDelete) -> int:
        """Delete the listed work items, or every item the filter matches.

        Returns how many items were deleted, children included. Children removed
        along with a selected parent are not counted twice.
        """
        if request.all_matching:
            targets = self._matching_ids(request.filter)
        else:
            targets = request.ids or []
            for item_id in targets:
                self._work_items.get_by_id(item_id)
        removed: set[UUID] = set()
        for item_id in targets:
            if item_id not in removed:
                removed.update(self._delete_tree(item_id))
        return len(removed)

    def _delete_tree(self, item_id: UUID) -> list[UUID]:
        """Delete an item after its children, so the parent link never blocks it."""
        deleted: list[UUID] = []
        for child in self._work_items.list_all(parent_id=item_id):
            deleted += self._delete_tree(child.id)
        self._work_items.delete(item_id)
        return [*deleted, item_id]

    def _matching_ids(self, filter: str | None) -> list[UUID]:
        """Ids of every work item, trashed or not, that the filter matches."""
        matches = parse_filter(filter)
        names = project_names(self._projects)
        statuses, types = lookups(self._statuses, self._types)
        return [
            item.id
            for item in self._work_items.list_all()
            if matches(filter_record(item, names, statuses, types))
        ]

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

    def _project_type_or_default(self, project_id: UUID) -> UUID:
        """Pick the project's first type."""
        types = in_position_order(self._types.list_all(project_id=project_id))
        if not types:
            raise InvalidReferenceError("The project has no work item type")
        return types[0].id

    def _ensure_parent(
        self, parent_id: UUID | None, item_id: UUID | None = None
    ) -> None:
        """Check that the parent exists and that the item is not its own ancestor.

        Walking up from the parent reaches the item only when the item is one of
        its ancestors, which would make a cycle. ``None`` means no parent.
        """
        current_id = parent_id
        while current_id is not None:
            if current_id == item_id:
                raise InvalidReferenceError("A work item cannot be its own ancestor")
            try:
                current = self._work_items.get_by_id(current_id)
            except NotFoundError:
                raise InvalidReferenceError("Parent work item not found") from None
            current_id = current.parent_id

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
