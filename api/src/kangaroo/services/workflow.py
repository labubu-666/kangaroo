from uuid import UUID

from kangaroo.errors import (
    ConflictError,
    InvalidReferenceError,
)
from kangaroo.repositories import (
    ProjectRepository,
    StatusRepository,
    StatusTransitionRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
)
from kangaroo.schemas import (
    ProjectStatus,
    StatusCreate,
    StatusReplace,
    StatusTransition,
    StatusTransitionCreate,
    StatusTransitionReplace,
    StatusTransitionUpdate,
    StatusUpdate,
    WorkItemType,
    WorkItemTypeCreate,
    WorkItemTypeReplace,
    WorkItemTypeUpdate,
    WorkItemUpdate,
)
from kangaroo.services.helpers import (
    ensure_project_exists,
    get_in_project,
    in_position_order,
    keep_position,
    with_default_position,
)


class WorkflowService:
    """Business rules for a project's statuses, work item types and transitions.

    Statuses and types belong to one project and are kept in position order. A
    project always keeps at least one ``todo`` status, so new work items have a
    starting point. A transition must join two statuses of its own project.
    """

    def __init__(
        self,
        projects: ProjectRepository,
        statuses: StatusRepository,
        types: WorkItemTypeRepository,
        transitions: StatusTransitionRepository,
        work_items: WorkItemRepository,
    ) -> None:
        self._projects = projects
        self._statuses = statuses
        self._types = types
        self._transitions = transitions
        self._work_items = work_items

    def list_statuses(self, project_id: UUID) -> list[ProjectStatus]:
        return in_position_order(self._statuses.list_all(project_id=project_id))

    def create_status(self, item: StatusCreate) -> ProjectStatus:
        """Create a status. Without a position it is placed last."""
        ensure_project_exists(self._projects, item.project_id)
        item = with_default_position(self._statuses, item, item.project_id)
        return self._statuses.create(item)

    def get_status(self, item_id: UUID) -> ProjectStatus:
        return self._statuses.get_by_id(item_id)

    def update_status(self, item_id: UUID, update: StatusUpdate) -> ProjectStatus:
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
        return self._statuses.replace(item_id, keep_position(current.position, replace))

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
            self._move_items("status_id", item_id, replacement_id)
        if status.category == "todo":
            self._ensure_other_todo_status(status)
        for transition in self._transitions.list_all(project_id=status.project_id):
            if item_id in (transition.from_status_id, transition.to_status_id):
                self._transitions.delete(transition.id)
        self._statuses.delete(item_id)

    def _move_items(self, field: str, old_id: UUID, new_id: UUID) -> None:
        """Point every work item whose ``field`` is ``old_id`` at ``new_id``."""
        for item in self._work_items.list_all(**{field: old_id}):
            self._work_items.update(
                item.id, WorkItemUpdate.model_validate({field: new_id})
            )

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
            get_in_project(self._statuses, status_id, project_id, "Status")

    def list_work_item_types(self, project_id: UUID) -> list[WorkItemType]:
        """List a project's work item types in position order."""
        return in_position_order(self._types.list_all(project_id=project_id))

    def create_work_item_type(self, item: WorkItemTypeCreate) -> WorkItemType:
        """Create a work item type. Without a position it is placed last."""
        ensure_project_exists(self._projects, item.project_id)
        item = with_default_position(self._types, item, item.project_id)
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
        return self._types.replace(item_id, keep_position(current.position, replace))

    def delete_work_item_type(
        self, item_id: UUID, replacement_id: UUID | None = None
    ) -> None:
        """Delete a work item type.

        If work items use the type, ``replacement_id`` must name another type of the
        same project. Those items move to it first. Without one the delete
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
            self._move_items("type_id", item_id, replacement_id)
        self._types.delete(item_id)

    def list_transitions(self, project_id: UUID) -> list[StatusTransition]:
        return self._transitions.list_all(project_id=project_id)

    def create_transition(self, item: StatusTransitionCreate) -> StatusTransition:
        """Create a transition between two statuses of the same project."""
        ensure_project_exists(self._projects, item.project_id)
        self._ensure_statuses_in_project(
            item.project_id, item.from_status_id, item.to_status_id
        )
        return self._transitions.create(item)

    def get_transition(self, item_id: UUID) -> StatusTransition:
        return self._transitions.get_by_id(item_id)

    def update_transition(
        self, item_id: UUID, update: StatusTransitionUpdate
    ) -> StatusTransition:
        """Update a transition (partial update), checking its statuses."""
        current = self._transitions.get_by_id(item_id)
        from_id = update.from_status_id or current.from_status_id
        to_id = update.to_status_id or current.to_status_id
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
        self._transitions.delete(item_id)
