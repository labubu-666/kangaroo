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


def task(seeded, summary="Task", **extra):
    return WorkItemCreate(
        summary=summary, project_id=seeded.project_id, type_id=seeded.task_id, **extra
    )


def child(seeded, parent_id, summary="Child", **extra):
    return WorkItemCreate(
        summary=summary,
        project_id=seeded.project_id,
        type_id=seeded.task_id,
        parent_id=parent_id,
        **extra,
    )


def test_create_work_item_with_missing_project_raises(work_item_service, seeded):
    with pytest.raises(InvalidReferenceError, match="Project not found"):
        work_item_service.create(
            WorkItemCreate(summary="Task", project_id=uuid4(), type_id=seeded.task_id)
        )


def test_new_work_item_starts_in_first_todo_status(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    assert item.status_id == seeded.open_id


def test_create_work_item_with_given_status(work_item_service, seeded):
    item = work_item_service.create(task(seeded, status_id=seeded.in_progress_id))
    assert item.status_id == seeded.in_progress_id


def test_duplicate_copies_fields_with_copy_summary(work_item_service, seeded):
    original = work_item_service.create(
        task(
            seeded,
            "Fix bug",
            description="Details",
            status_id=seeded.in_progress_id,
            labels=["urgent"],
        )
    )
    copy = work_item_service.duplicate(original.id)
    assert copy.id != original.id
    assert copy.summary == "Fix bug (copy)"
    assert copy.description == "Details"
    assert copy.project_id == original.project_id
    assert copy.type_id == original.type_id
    assert copy.status_id == seeded.in_progress_id
    assert copy.labels == ["urgent"]
    assert copy.trashed is False


def test_duplicate_trashed_item_gives_live_copy(work_item_service, seeded):
    original = work_item_service.create(task(seeded))
    work_item_service.update(original.id, WorkItemUpdate(trashed=True))
    assert work_item_service.duplicate(original.id).trashed is False


def test_duplicate_child_keeps_parent(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    kid = work_item_service.create(child(seeded, parent.id, "Child"))
    copy = work_item_service.duplicate(kid.id)
    assert copy.parent_id == parent.id
    assert copy.summary == "Child (copy)"


def test_duplicate_parent_does_not_copy_children(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    work_item_service.create(child(seeded, parent.id))
    copy = work_item_service.duplicate(parent.id)
    assert work_item_service.list_paginated(10, 0, parent_id=copy.id).total == 0


def test_duplicate_missing_item_raises(work_item_service):
    with pytest.raises(NotFoundError):
        work_item_service.duplicate(uuid4())


def test_create_with_type_of_other_project_raises(work_item_service, seeded, other):
    with pytest.raises(InvalidReferenceError, match="type is not in the project"):
        work_item_service.create(
            WorkItemCreate(
                summary="Task", project_id=seeded.project_id, type_id=other.task_id
            )
        )


def test_create_with_status_of_other_project_raises(work_item_service, seeded, other):
    with pytest.raises(InvalidReferenceError, match="Status is not in the project"):
        work_item_service.create(task(seeded, status_id=other.open_id))


def test_create_with_unknown_type_or_status_raises(work_item_service, seeded):
    with pytest.raises(InvalidReferenceError, match="type not found"):
        work_item_service.create(
            WorkItemCreate(
                summary="Task", project_id=seeded.project_id, type_id=uuid4()
            )
        )
    with pytest.raises(InvalidReferenceError, match="Status not found"):
        work_item_service.create(task(seeded, status_id=uuid4()))


def test_create_with_missing_parent_raises(work_item_service, seeded):
    with pytest.raises(InvalidReferenceError, match="Parent work item not found"):
        work_item_service.create(child(seeded, uuid4()))


def test_any_item_can_have_a_parent_in_another_project(
    work_item_service, seeded, other
):
    parent = work_item_service.create(task(seeded, "Parent"))
    created = work_item_service.create(
        WorkItemCreate(
            summary="Child",
            project_id=other.project_id,
            type_id=other.task_id,
            status_id=other.open_id,
            parent_id=parent.id,
        )
    )
    assert created.parent_id == parent.id


def test_parents_can_nest_several_levels(work_item_service, seeded):
    grandparent = work_item_service.create(task(seeded, "Top"))
    parent = work_item_service.create(child(seeded, grandparent.id, "Middle"))
    leaf = work_item_service.create(child(seeded, parent.id, "Leaf"))
    assert leaf.parent_id == parent.id
    assert parent.parent_id == grandparent.id


def test_update_sets_and_clears_parent(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    item = work_item_service.create(task(seeded, "Item"))
    attached = work_item_service.update(item.id, WorkItemUpdate(parent_id=parent.id))
    assert attached.parent_id == parent.id
    detached = work_item_service.update(item.id, WorkItemUpdate(parent_id=None))
    assert detached.parent_id is None


def test_update_parent_to_missing_item_raises(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    with pytest.raises(InvalidReferenceError, match="Parent work item not found"):
        work_item_service.update(item.id, WorkItemUpdate(parent_id=uuid4()))


def test_item_cannot_be_its_own_parent(work_item_service, seeded):
    item = work_item_service.create(task(seeded))
    with pytest.raises(InvalidReferenceError, match="own ancestor"):
        work_item_service.update(item.id, WorkItemUpdate(parent_id=item.id))


def test_cannot_move_parent_under_its_own_descendant(work_item_service, seeded):
    top = work_item_service.create(task(seeded, "Top"))
    middle = work_item_service.create(child(seeded, top.id, "Middle"))
    bottom = work_item_service.create(child(seeded, middle.id, "Bottom"))
    with pytest.raises(InvalidReferenceError, match="own ancestor"):
        work_item_service.update(top.id, WorkItemUpdate(parent_id=bottom.id))
    with pytest.raises(InvalidReferenceError, match="own ancestor"):
        work_item_service.replace(
            top.id,
            WorkItemReplace(
                summary="Top",
                project_id=seeded.project_id,
                type_id=seeded.task_id,
                parent_id=bottom.id,
            ),
        )
    assert work_item_service.get(top.id).parent_id is None


def test_moving_a_parent_keeps_its_children(work_item_service, seeded, other):
    parent = work_item_service.create(task(seeded, "Parent"))
    item_child = work_item_service.create(child(seeded, parent.id))
    moved = work_item_service.update(
        parent.id,
        WorkItemUpdate(
            project_id=other.project_id,
            type_id=other.task_id,
            status_id=other.open_id,
        ),
    )
    assert moved.project_id == other.project_id
    assert work_item_service.get(item_child.id).parent_id == parent.id


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
            WorkItemReplace(summary="Task", project_id=uuid4(), type_id=seeded.task_id),
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
            summary="Task", project_id=seeded.project_id, type_id=seeded.task_id
        ),
    )
    assert replaced.status_id == seeded.open_id


def test_delete_parent_also_deletes_children(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    kid = work_item_service.create(child(seeded, parent.id))
    work_item_service.delete(parent.id)
    with pytest.raises(NotFoundError):
        work_item_service.get(kid.id)


def test_delete_missing_work_item_raises(work_item_service):
    with pytest.raises(NotFoundError):
        work_item_service.delete(uuid4())


def test_bulk_delete_ids_removes_parent_with_its_children(work_item_service, seeded):
    parent = work_item_service.create(task(seeded, "Parent"))
    kid = work_item_service.create(child(seeded, parent.id))
    keep = work_item_service.create(task(seeded, "Keep"))
    deleted = work_item_service.bulk_delete(WorkItemBulkDelete(ids=[parent.id, kid.id]))
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
        WorkItemBulkDelete(all_matching=True, filter="summary ~ 'bug'")
    )
    assert deleted == 1
    summaries = [
        item.summary for item in work_item_service.list_paginated(10, 0).results
    ]
    assert summaries == ["Other"]


def test_bulk_delete_all_matching_without_filter_deletes_everything(
    work_item_service, seeded
):
    parent = work_item_service.create(task(seeded, "Parent"))
    work_item_service.create(child(seeded, parent.id))
    work_item_service.create(task(seeded, "Other"))
    assert work_item_service.bulk_delete(WorkItemBulkDelete(all_matching=True)) == 3
    assert work_item_service.list_paginated(10, 0).total == 0
