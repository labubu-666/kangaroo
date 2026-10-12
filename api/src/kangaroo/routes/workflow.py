from uuid import UUID

from fastapi import APIRouter, Depends, status

from kangaroo.routes.dependencies import get_workflow_service
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
)
from kangaroo.services import WorkflowService

statuses_router = APIRouter(prefix="/statuses", tags=["statuses"])


@statuses_router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=ProjectStatus
)
def create_status(
    item: StatusCreate, service: WorkflowService = Depends(get_workflow_service)
) -> ProjectStatus:
    """Create a status in a project. Without a position it is placed last."""
    return service.create_status(item)


@statuses_router.get("/", response_model=list[ProjectStatus])
def list_statuses(
    project_id: UUID, service: WorkflowService = Depends(get_workflow_service)
) -> list[ProjectStatus]:
    """List a project's statuses in position order."""
    return service.list_statuses(project_id)


@statuses_router.get("/{item_id}", response_model=ProjectStatus)
def get_status(
    item_id: UUID, service: WorkflowService = Depends(get_workflow_service)
) -> ProjectStatus:
    """Get a status by ID."""
    return service.get_status(item_id)


@statuses_router.put("/{item_id}", response_model=ProjectStatus)
def replace_status(
    item_id: UUID,
    replace: StatusReplace,
    service: WorkflowService = Depends(get_workflow_service),
) -> ProjectStatus:
    """Replace a status (full update)."""
    return service.replace_status(item_id, replace)


@statuses_router.patch("/{item_id}", response_model=ProjectStatus)
def update_status(
    item_id: UUID,
    update: StatusUpdate,
    service: WorkflowService = Depends(get_workflow_service),
) -> ProjectStatus:
    """Update a status (partial update). Changing a position reorders statuses."""
    return service.update_status(item_id, update)


@statuses_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_status(
    item_id: UUID,
    replacement_id: UUID | None = None,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """Delete a status and its transitions.

    If work items use the status, pass ``replacement_id`` (another status of the
    same project) and they move to it. Without it the delete returns 409. The last
    To Do status can't be deleted (409).
    """
    service.delete_status(item_id, replacement_id)


work_item_types_router = APIRouter(prefix="/work-item-types", tags=["work-item-types"])


@work_item_types_router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=WorkItemType
)
def create_work_item_type(
    item: WorkItemTypeCreate,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkItemType:
    """Create a work item type in a project. Without a position it is placed last."""
    return service.create_work_item_type(item)


@work_item_types_router.get("/", response_model=list[WorkItemType])
def list_work_item_types(
    project_id: UUID, service: WorkflowService = Depends(get_workflow_service)
) -> list[WorkItemType]:
    """List a project's work item types in position order."""
    return service.list_work_item_types(project_id)


@work_item_types_router.get("/{item_id}", response_model=WorkItemType)
def get_work_item_type(
    item_id: UUID, service: WorkflowService = Depends(get_workflow_service)
) -> WorkItemType:
    """Get a work item type by ID."""
    return service.get_work_item_type(item_id)


@work_item_types_router.put("/{item_id}", response_model=WorkItemType)
def replace_work_item_type(
    item_id: UUID,
    replace: WorkItemTypeReplace,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkItemType:
    """Replace a work item type (full update)."""
    return service.replace_work_item_type(item_id, replace)


@work_item_types_router.patch("/{item_id}", response_model=WorkItemType)
def update_work_item_type(
    item_id: UUID,
    update: WorkItemTypeUpdate,
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkItemType:
    """Update a work item type (partial update)."""
    return service.update_work_item_type(item_id, update)


@work_item_types_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_work_item_type(
    item_id: UUID,
    replacement_id: UUID | None = None,
    service: WorkflowService = Depends(get_workflow_service),
) -> None:
    """Delete a work item type.

    If work items use the type, pass ``replacement_id`` (another type of the same
    project and level) and they move to it. Without it the delete returns 409.
    """
    service.delete_work_item_type(item_id, replacement_id)


transitions_router = APIRouter(
    prefix="/status-transitions", tags=["status-transitions"]
)


@transitions_router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=StatusTransition
)
def create_transition(
    item: StatusTransitionCreate,
    service: WorkflowService = Depends(get_workflow_service),
) -> StatusTransition:
    """Allow a move from one status to another within a project."""
    return service.create_transition(item)


@transitions_router.get("/", response_model=list[StatusTransition])
def list_transitions(
    project_id: UUID, service: WorkflowService = Depends(get_workflow_service)
) -> list[StatusTransition]:
    """List a project's status transitions."""
    return service.list_transitions(project_id)


@transitions_router.get("/{item_id}", response_model=StatusTransition)
def get_transition(
    item_id: UUID, service: WorkflowService = Depends(get_workflow_service)
) -> StatusTransition:
    """Get a status transition by ID."""
    return service.get_transition(item_id)


@transitions_router.put("/{item_id}", response_model=StatusTransition)
def replace_transition(
    item_id: UUID,
    replace: StatusTransitionReplace,
    service: WorkflowService = Depends(get_workflow_service),
) -> StatusTransition:
    """Replace a status transition (full update)."""
    return service.replace_transition(item_id, replace)


@transitions_router.patch("/{item_id}", response_model=StatusTransition)
def update_transition(
    item_id: UUID,
    update: StatusTransitionUpdate,
    service: WorkflowService = Depends(get_workflow_service),
) -> StatusTransition:
    """Update a status transition (partial update)."""
    return service.update_transition(item_id, update)


@transitions_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transition(
    item_id: UUID, service: WorkflowService = Depends(get_workflow_service)
) -> None:
    """Delete a status transition."""
    service.delete_transition(item_id)
