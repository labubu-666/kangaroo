from uuid import uuid4

import pytest

from kangaroo.errors import ConflictError, InvalidReferenceError, NotFoundError
from kangaroo.schemas import (
    ProjectCreate,
    StatusCreate,
    StatusReplace,
    StatusTransitionCreate,
    StatusUpdate,
    WorkItemCreate,
    WorkItemTypeCreate,
)


def test_replace_status_out_of_todo_keeps_one_todo(workflow, statuses, project_id):
    """Replacing the only To Do status with a non-To Do one is refused."""
    open_status = statuses.list_all(project_id=project_id)[0]
    with pytest.raises(ConflictError, match="To Do"):
        workflow.replace_status(
            open_status.id, StatusReplace(name="Open", category="done")
        )
    assert statuses.get_by_id(open_status.id).category == "todo"


def test_update_status_with_todo_category_unchanged_is_allowed(
    workflow, statuses, project_id
):
    """Renaming the only To Do status is fine; only leaving the category is blocked."""
    open_status = statuses.list_all(project_id=project_id)[0]
    updated = workflow.update_status(open_status.id, StatusUpdate(name="Backlog"))
    assert updated.name == "Backlog"
    assert updated.category == "todo"


def test_replace_status_keeps_position_when_omitted(workflow, statuses, project_id):
    done = next(s for s in statuses.list_all(project_id=project_id) if s.position == 2)
    replaced = workflow.replace_status(
        done.id, StatusReplace(name="Closed", category="done")
    )
    assert replaced.position == 2


def test_create_transition_to_status_of_other_project_raises(
    workflow, statuses, project_id, projects
):
    other = projects.create(ProjectCreate(name="Other")).id
    own = statuses.list_all(project_id=project_id)[0].id
    foreign = workflow.create_status(
        StatusCreate(project_id=other, name="X", category="todo")
    ).id
    with pytest.raises(InvalidReferenceError, match="not in the project"):
        workflow.create_transition(
            StatusTransitionCreate(
                project_id=project_id, from_status_id=own, to_status_id=foreign
            )
        )


def test_create_transition_to_missing_status_raises(workflow, statuses, project_id):
    own = statuses.list_all(project_id=project_id)[0].id
    with pytest.raises(InvalidReferenceError, match="Status not found"):
        workflow.create_transition(
            StatusTransitionCreate(
                project_id=project_id, from_status_id=own, to_status_id=uuid4()
            )
        )


def test_delete_status_removes_transitions_in_either_direction(
    workflow, statuses, transitions, project_id
):
    """A transition into or out of the deleted status is removed with it."""
    open_id, in_progress_id, done_id = (
        s.id for s in statuses.list_all(project_id=project_id)
    )
    workflow.create_transition(
        StatusTransitionCreate(
            project_id=project_id,
            from_status_id=open_id,
            to_status_id=in_progress_id,
        )
    )
    workflow.create_transition(
        StatusTransitionCreate(
            project_id=project_id,
            from_status_id=in_progress_id,
            to_status_id=done_id,
        )
    )
    workflow.delete_status(in_progress_id)
    assert transitions.list_all(project_id=project_id) == []


def test_delete_project_removes_its_workflow(
    project_service, projects, statuses, types, transitions
):
    created = project_service.create(ProjectCreate(name="Gone"))
    project_service.delete(created.id)
    assert statuses.list_all(project_id=created.id) == []
    assert types.list_all(project_id=created.id) == []
    assert transitions.list_all(project_id=created.id) == []


def test_delete_in_use_status_without_replacement_is_refused(
    workflow, statuses, project_id, work_items
):
    in_progress = next(
        s for s in statuses.list_all(project_id=project_id) if s.position == 1
    )
    work_items.create(
        WorkItemCreate(
            title="Busy",
            project_id=project_id,
            type_id=next(
                t.id
                for t in workflow._types.list_all(project_id=project_id)
                if t.level == "standard"
            ),
            status_id=in_progress.id,
        )
    )
    with pytest.raises(ConflictError, match="1 work items use this status"):
        workflow.delete_status(in_progress.id)
    assert statuses.get_by_id(in_progress.id) is not None


def test_delete_in_use_status_moves_items_to_replacement(
    workflow, statuses, project_id, work_items
):
    in_progress = next(
        s for s in statuses.list_all(project_id=project_id) if s.position == 1
    )
    done = next(s for s in statuses.list_all(project_id=project_id) if s.position == 2)
    task_type = next(
        t.id
        for t in workflow._types.list_all(project_id=project_id)
        if t.level == "standard"
    )
    item = work_items.create(
        WorkItemCreate(
            title="Busy",
            project_id=project_id,
            type_id=task_type,
            status_id=in_progress.id,
        )
    )
    workflow.delete_status(in_progress.id, replacement_id=done.id)
    assert work_items.get_by_id(item.id).status_id == done.id
    with pytest.raises(NotFoundError):
        statuses.get_by_id(in_progress.id)


def test_replacement_status_must_be_in_same_project(
    workflow, statuses, project_id, projects, work_items, types
):
    in_progress = next(
        s for s in statuses.list_all(project_id=project_id) if s.position == 1
    )
    other = projects.create(ProjectCreate(name="Other"))
    foreign = workflow.create_status(
        StatusCreate(project_id=other.id, name="Foreign", category="todo")
    )
    task_type = next(
        t.id for t in types.list_all(project_id=project_id) if t.level == "standard"
    )
    work_items.create(
        WorkItemCreate(
            title="Busy",
            project_id=project_id,
            type_id=task_type,
            status_id=in_progress.id,
        )
    )
    with pytest.raises(InvalidReferenceError, match="same project"):
        workflow.delete_status(in_progress.id, replacement_id=foreign.id)


def test_delete_in_use_type_moves_items_to_same_level_replacement(
    workflow, types, statuses, project_id, work_items
):
    task_type = next(
        t for t in types.list_all(project_id=project_id) if t.level == "standard"
    )
    open_status = next(
        s for s in statuses.list_all(project_id=project_id) if s.position == 0
    )
    item = work_items.create(
        WorkItemCreate(
            title="Busy",
            project_id=project_id,
            type_id=task_type.id,
            status_id=open_status.id,
        )
    )
    bug = workflow.create_work_item_type(
        WorkItemTypeCreate(project_id=project_id, name="Bug", level="standard")
    )
    workflow.delete_work_item_type(task_type.id, replacement_id=bug.id)
    assert work_items.get_by_id(item.id).type_id == bug.id


def test_replacement_type_must_have_same_level(
    workflow, types, statuses, project_id, work_items
):
    task_type = next(
        t for t in types.list_all(project_id=project_id) if t.level == "standard"
    )
    open_status = next(
        s for s in statuses.list_all(project_id=project_id) if s.position == 0
    )
    work_items.create(
        WorkItemCreate(
            title="Busy",
            project_id=project_id,
            type_id=task_type.id,
            status_id=open_status.id,
        )
    )
    subtask_type = next(
        t for t in types.list_all(project_id=project_id) if t.level == "subtask"
    )
    with pytest.raises(InvalidReferenceError, match="same level"):
        workflow.delete_work_item_type(task_type.id, replacement_id=subtask_type.id)


def test_moving_status_leaves_the_type_unchanged(
    workflow, statuses, project_id, work_items
):
    """Replacing a status must not touch the item's type."""
    in_progress = next(
        s for s in statuses.list_all(project_id=project_id) if s.position == 1
    )
    done = next(s for s in statuses.list_all(project_id=project_id) if s.position == 2)
    types = workflow._types.list_all(project_id=project_id)
    task_type = next(t for t in types if t.level == "standard")
    item = work_items.create(
        WorkItemCreate(
            title="Busy",
            project_id=project_id,
            type_id=task_type.id,
            status_id=in_progress.id,
        )
    )
    workflow.delete_status(in_progress.id, replacement_id=done.id)
    moved = work_items.get_by_id(item.id)
    assert moved.status_id == done.id
    assert moved.type_id == task_type.id


def test_moving_type_leaves_the_status_unchanged(
    workflow, statuses, project_id, work_items
):
    """Replacing a type must not touch the item's status."""
    types = workflow._types.list_all(project_id=project_id)
    old_type = next(t for t in types if t.level == "standard")
    new_type = workflow._types.create(
        WorkItemTypeCreate(
            project_id=project_id, name="Story", level="standard", position=5
        )
    )
    open_status = next(
        s for s in statuses.list_all(project_id=project_id) if s.position == 0
    )
    item = work_items.create(
        WorkItemCreate(
            title="Typed",
            project_id=project_id,
            type_id=old_type.id,
            status_id=open_status.id,
        )
    )
    workflow.delete_work_item_type(old_type.id, replacement_id=new_type.id)
    moved = work_items.get_by_id(item.id)
    assert moved.type_id == new_type.id
    assert moved.status_id == open_status.id
