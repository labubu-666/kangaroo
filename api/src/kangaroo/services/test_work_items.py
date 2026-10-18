from uuid import uuid4

import pytest

from kangaroo.errors import ConflictError, InvalidReferenceError, NotFoundError
from kangaroo.schemas import (
    StatusTransitionCreate,
    WorkItemBulkDelete,
    WorkItemCreate,
    WorkItemReplace,
    WorkItemUpdate,
)


def task(seeded, title="Task", **extra):
    return WorkItemCreate(
        title=title, project_id=seeded.project_id, type_id=seeded.task_id, **extra
    )


def subtask(seeded, parent_id, title="Child", **extra):
    return WorkItemCreate(
        title=title,
        project_id=seeded.project_id,
        type_id=seeded.subtask_id,
        parent_id=parent_id,
        **extra,
    )


def test_create_work_item_with_missing_project_raises(work_item_service, seeded):
    with pytest.raises(InvalidReferenceError, match="Project not found"):
        work_item_service.create(
            WorkItemCreate(title="Task", project_id=uuid4(), type_id=seeded.task_id)
        )


def test_new_work_item_starts_in_first_todo_status(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    assert item.status_id == seeded.open_id


def test_create_work_item_with_given_status(work_item_service, seeded):
    item = work_item_service.create(task(seeded, status_id=seeded.in_progress_id))
    assert item.status_id == seeded.in_progress_id


def test_create_with_type_of_other_project_raises(work_item_service, seeded, other):
    with pytest.raises(InvalidReferenceError, match="type is not in the project"):
        work_item_service.create(
            WorkItemCreate(
                title="Task", project_id=seeded.project_id, type_id=other.task_id
            )
        )


def test_create_with_status_of_other_project_raises(work_item_service, seeded, other):
    with pytest.raises(InvalidReferenceError, match="Status is not in the project"):
        work_item_service.create(task(seeded, status_id=other.open_id))


def test_create_with_unknown_type_or_status_raises(work_item_service, seeded):
    with pytest.raises(InvalidReferenceError, match="type not found"):
        work_item_service.create(
            WorkItemCreate(title="Task", project_id=seeded.project_id, type_id=uuid4())
        )
    with pytest.raises(InvalidReferenceError, match="Status not found"):
        work_item_service.create(task(seeded, status_id=uuid4()))


def test_subtask_needs_parent_and_task_rejects_one(work_item_service, seeded):
    with pytest.raises(InvalidReferenceError, match="needs a parent_id"):
        work_item_service.create(
            WorkItemCreate(
                title="Child", project_id=seeded.project_id, type_id=seeded.subtask_id
            )
        )
    parent = work_item_service.create(task(seeded))
    with pytest.raises(InvalidReferenceError, match="Only a subtask"):
        work_item_service.create(task(seeded, parent_id=parent.id))


def test_create_subtask_with_missing_parent_raises(work_item_service, seeded):
    with pytest.raises(InvalidReferenceError, match="Parent work item not found"):
        work_item_service.create(subtask(seeded, uuid4()))


def test_create_subtask_parent_must_be_standard_level(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    child = work_item_service.create(subtask(seeded, parent.id))
    with pytest.raises(InvalidReferenceError, match="must be a task"):
        work_item_service.create(subtask(seeded, child.id, "Grandchild"))


def test_create_subtask_must_match_parent_project(work_item_service, seeded, other):
    parent = work_item_service.create(task(seeded, "Parent"))
    with pytest.raises(InvalidReferenceError, match="same project"):
        work_item_service.create(
            WorkItemCreate(
                title="Child",
                project_id=other.project_id,
                type_id=other.subtask_id,
                parent_id=parent.id,
            )
        )


def test_update_work_item_with_missing_project_raises(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    with pytest.raises(InvalidReferenceError):
        work_item_service.update(item.id, WorkItemUpdate(project_id=uuid4()))


def test_update_work_item_project_to_null_raises(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    with pytest.raises(InvalidReferenceError, match="cannot be null"):
        work_item_service.update(item.id, WorkItemUpdate(project_id=None))


def test_replace_work_item_with_missing_project_raises(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    with pytest.raises(InvalidReferenceError):
        work_item_service.replace(
            item.id,
            WorkItemReplace(title="Task", project_id=uuid4(), type_id=seeded.task_id),
        )


def test_move_task_with_subtasks_raises(work_item_service, seeded, other):
    parent = work_item_service.create(task(seeded, "Parent"))
    work_item_service.create(subtask(seeded, parent.id))
    move = WorkItemUpdate(
        project_id=other.project_id, type_id=other.task_id, status_id=other.open_id
    )
    with pytest.raises(ConflictError, match="cannot change project"):
        work_item_service.update(parent.id, move)
    with pytest.raises(ConflictError, match="cannot change project"):
        work_item_service.replace(
            parent.id,
            WorkItemReplace(
                title="Parent",
                project_id=other.project_id,
                type_id=other.task_id,
                status_id=other.open_id,
            ),
        )


def test_move_subtask_raises(work_item_service, seeded, other):
    parent = work_item_service.create(task(seeded, "Parent"))
    child = work_item_service.create(subtask(seeded, parent.id))
    with pytest.raises(ConflictError, match="cannot change project"):
        work_item_service.update(
            child.id,
            WorkItemUpdate(
                project_id=other.project_id,
                type_id=other.subtask_id,
                status_id=other.open_id,
            ),
        )


def test_move_task_defaults_status_and_type(work_item_service, seeded, other):
    item = work_item_service.create(task(seeded))
    moved = work_item_service.update(
        item.id, WorkItemUpdate(project_id=other.project_id)
    )
    assert moved.project_id == other.project_id
    assert moved.type_id == other.task_id
    assert moved.status_id == other.open_id


def test_move_task_rejects_type_of_other_project(work_item_service, seeded, other):
    item = work_item_service.create(task(seeded))
    with pytest.raises(InvalidReferenceError, match="type is not in the project"):
        work_item_service.update(
            item.id,
            WorkItemUpdate(
                project_id=other.project_id,
                type_id=seeded.task_id,
                status_id=other.open_id,
            ),
        )
    assert work_item_service.get(item.id).project_id == seeded.project_id


def test_move_task_without_subtasks_succeeds(work_item_service, seeded, other):
    item = work_item_service.create(task(seeded))
    moved = work_item_service.update(
        item.id,
        WorkItemUpdate(
            project_id=other.project_id,
            type_id=other.task_id,
            status_id=other.in_progress_id,
        ),
    )
    assert moved.project_id == other.project_id
    assert moved.type_id == other.task_id
    assert moved.status_id == other.in_progress_id


def test_same_project_update_skips_move_rules(work_item_service, seeded):
    """Keeping the same project is allowed even for a task with subtasks."""
    parent = work_item_service.create(task(seeded, "Parent"))
    work_item_service.create(subtask(seeded, parent.id))
    updated = work_item_service.update(
        parent.id, WorkItemUpdate(project_id=seeded.project_id, title="Renamed")
    )
    assert updated.title == "Renamed"


def test_type_change_must_keep_level(
    work_item_service, projects, types, statuses, seeded
):
    from kangaroo.schemas import WorkItemTypeCreate

    bug = types.create(
        WorkItemTypeCreate(
            project_id=seeded.project_id, name="Bug", level="standard", position=2
        )
    )
    item = work_item_service.create(task(seeded))
    changed = work_item_service.update(item.id, WorkItemUpdate(type_id=bug.id))
    assert changed.type_id == bug.id
    with pytest.raises(ConflictError, match="cannot change type level"):
        work_item_service.update(item.id, WorkItemUpdate(type_id=seeded.subtask_id))


def test_no_transitions_allows_every_status_change(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    moved = work_item_service.update(item.id, WorkItemUpdate(status_id=seeded.done_id))
    assert moved.status_id == seeded.done_id


def test_transitions_limit_status_changes(work_item_service, transitions, seeded):
    transitions.create(
        StatusTransitionCreate(
            project_id=seeded.project_id,
            from_status_id=seeded.open_id,
            to_status_id=seeded.in_progress_id,
        )
    )
    item = work_item_service.create(task(seeded))
    with pytest.raises(ConflictError, match="does not allow"):
        work_item_service.update(item.id, WorkItemUpdate(status_id=seeded.done_id))
    moved = work_item_service.update(
        item.id, WorkItemUpdate(status_id=seeded.in_progress_id)
    )
    assert moved.status_id == seeded.in_progress_id
    # Staying in the same status is not a change, so it needs no transition.
    same = work_item_service.update(
        item.id, WorkItemUpdate(status_id=seeded.in_progress_id)
    )
    assert same.status_id == seeded.in_progress_id


def test_replace_uses_first_todo_status_when_omitted(work_item_service, seeded):
    item = work_item_service.create(task(seeded, status_id=seeded.done_id))
    replaced = work_item_service.replace(
        item.id,
        WorkItemReplace(
            title="Task", project_id=seeded.project_id, type_id=seeded.task_id
        ),
    )
    assert replaced.status_id == seeded.open_id


def test_delete_task_also_deletes_subtasks(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    child = work_item_service.create(subtask(seeded, parent.id))
    work_item_service.delete(parent.id)
    with pytest.raises(NotFoundError):
        work_item_service.get(child.id)


def test_delete_missing_work_item_raises(work_item_service):
    with pytest.raises(NotFoundError):
        work_item_service.delete(uuid4())


def test_bulk_delete_ids_removes_task_with_its_subtasks(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    child = work_item_service.create(subtask(seeded, parent.id))
    keep = work_item_service.create(task(seeded, "Keep"))
    deleted = work_item_service.bulk_delete(
        WorkItemBulkDelete(ids=[parent.id, child.id])
    )
    assert deleted == 2
    assert work_item_service.list_paginated(10, 0).total == 1
    assert work_item_service.get(keep.id).id == keep.id


def test_bulk_delete_ids_missing_item_deletes_nothing(work_item_service, seeded):
    keep = work_item_service.create(task(seeded, "Keep"))
    with pytest.raises(NotFoundError):
        work_item_service.bulk_delete(WorkItemBulkDelete(ids=[keep.id, uuid4()]))
    assert work_item_service.get(keep.id).id == keep.id


def test_bulk_delete_all_matching_uses_filter(work_item_service, seeded):
    work_item_service.create(task(seeded, "Login bug"))
    work_item_service.create(task(seeded, "Other"))
    deleted = work_item_service.bulk_delete(
        WorkItemBulkDelete(all_matching=True, filter="title ~ 'bug'")
    )
    assert deleted == 1
    titles = [item.title for item in work_item_service.list_paginated(10, 0).results]
    assert titles == ["Other"]


def test_bulk_delete_all_matching_without_filter_deletes_everything(
    work_item_service, seeded
):
    parent = work_item_service.create(task(seeded, "Parent"))
    work_item_service.create(subtask(seeded, parent.id))
    work_item_service.create(task(seeded, "Other"))
    assert work_item_service.bulk_delete(WorkItemBulkDelete(all_matching=True)) == 3
    assert work_item_service.list_paginated(10, 0).total == 0
