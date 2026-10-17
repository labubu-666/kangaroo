import pytest

from kangaroo.schemas import WorkItemReplace, WorkItemUpdate
from kangaroo.testing import new_task, seed_project


@pytest.fixture
def seeded(projects, statuses, types):
    """A project with the To Do List statuses and types."""
    return seed_project(projects, statuses, types)


@pytest.fixture
def project_id(seeded):
    return seeded.project_id


def test_search_matches_title_and_description(work_items, project_id, seeded):
    """Search is a case-insensitive match on title or description."""
    work_items.create(new_task(seeded, "Fix Login bug"))
    work_items.create(new_task(seeded, "Other", description="login page copy"))
    work_items.create(new_task(seeded, "Unrelated"))

    page = work_items.list_paginated(limit=10, offset=0, search="LOGIN")
    assert page.total == 2
    assert sorted(item.title for item in page.results) == ["Fix Login bug", "Other"]


def test_blank_search_matches_everything(work_items, project_id, seeded):
    """A blank or whitespace-only search is ignored."""
    work_items.create(new_task(seeded, "A"))
    work_items.create(new_task(seeded, "B"))

    assert work_items.list_paginated(limit=10, offset=0, search="  ").total == 2
    assert work_items.list_paginated(limit=10, offset=0, search=None).total == 2


def test_search_combines_with_exact_filters(work_items, project_id, seeded):
    """Search and exact-match filters both apply, and total counts both."""
    done = work_items.create(new_task(seeded, "Login done"))
    work_items.update(done.id, WorkItemUpdate(status_id=seeded.done_id))
    work_items.create(new_task(seeded, "Login open"))

    page = work_items.list_paginated(
        limit=10, offset=0, search="login", status_id=seeded.done_id
    )
    assert page.total == 1
    assert page.results[0].id == done.id


def test_modified_at_tracks_changes(work_items, project_id, seeded):
    """A new item has modified_at equal to created_at; edits move it forward."""
    item = work_items.create(new_task(seeded, "A"))
    assert item.modified_at == item.created_at

    updated = work_items.update(item.id, WorkItemUpdate(title="B"))
    assert updated.created_at == item.created_at
    assert updated.modified_at > item.modified_at

    replaced = work_items.replace(
        item.id,
        WorkItemReplace(
            title="C",
            project_id=project_id,
            type_id=seeded.task_id,
            status_id=seeded.open_id,
        ),
    )
    assert replaced.created_at == item.created_at
    assert replaced.modified_at > updated.modified_at


def test_labels_round_trip(work_items, project_id, seeded):
    """Labels are stored on create, changed by update and replaced by replace."""
    item = work_items.create(new_task(seeded, "A", labels=["news", "urgent"]))
    assert item.labels == ["news", "urgent"]
    assert work_items.get_by_id(item.id).labels == ["news", "urgent"]

    updated = work_items.update(item.id, WorkItemUpdate(labels=["news"]))
    assert updated.labels == ["news"]

    replaced = work_items.replace(
        item.id,
        WorkItemReplace(
            title="A",
            project_id=project_id,
            type_id=seeded.task_id,
            status_id=seeded.open_id,
        ),
    )
    assert replaced.labels == []


def test_unknown_filter_field_raises(work_items, project_id):
    """Filtering on a name the entity does not have is a ValueError."""
    with pytest.raises(ValueError, match="Unknown filter field 'projct_id'"):
        work_items.count(projct_id=project_id)
    with pytest.raises(ValueError, match="Unknown filter field 'projct_id'"):
        work_items.list_paginated(limit=10, offset=0, projct_id=project_id)
