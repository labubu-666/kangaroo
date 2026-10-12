from uuid import uuid4

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from kangaroo.backends.base import utc_now
from kangaroo.backends.sqlite import (
    SQLiteBoardBackend,
    SQLiteFunctionBackend,
    SQLiteProjectBackend,
    SQLiteStatusBackend,
    SQLiteWorkItemBackend,
    SQLiteWorkItemTypeBackend,
    StatusRow,
    StatusTransitionRow,
    WorkItemRow,
    WorkItemTypeRow,
    create_sqlite_engine,
)
from kangaroo.errors import NotFoundError
from kangaroo.schemas import (
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    FunctionCreate,
    ProjectCreate,
    ProjectReplace,
    ProjectUpdate,
    WorkItemReplace,
    WorkItemUpdate,
)
from kangaroo.testing import new_subtask, new_task, seed_project


@pytest.fixture
def engine():
    """Provide a fresh in-memory SQLite engine for each test."""
    return create_sqlite_engine("sqlite://memory")


@pytest.fixture
def projects(engine):
    return SQLiteProjectBackend(engine)


@pytest.fixture
def work_items(engine):
    return SQLiteWorkItemBackend(engine)


@pytest.fixture
def statuses(engine):
    return SQLiteStatusBackend(engine)


@pytest.fixture
def types(engine):
    return SQLiteWorkItemTypeBackend(engine)


@pytest.fixture
def seeded(projects, statuses, types):
    """A project with the To Do List statuses and types."""
    return seed_project(projects, statuses, types)


@pytest.fixture
def project_id(seeded):
    return seeded.project_id


def test_foreign_keys_enabled(engine):
    """Every connection has foreign key enforcement turned on."""
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_create_and_get_project(projects):
    """A created project can be read back by ID."""
    created = projects.create(ProjectCreate(name="Alpha", description="First"))
    assert projects.get_by_id(created.id) == created


def test_project_update_and_replace(projects):
    """Projects can be partially updated and fully replaced."""
    created = projects.create(ProjectCreate(name="Alpha", description="First"))
    updated = projects.update(created.id, ProjectUpdate(name="Renamed"))
    assert updated.name == "Renamed"
    assert updated.description == "First"

    replaced = projects.replace(created.id, ProjectReplace(name="Final"))
    assert replaced.name == "Final"
    assert replaced.description is None


def test_project_not_found_raises(projects):
    with pytest.raises(ValueError):
        projects.get_by_id(uuid4())


def test_project_pagination(projects):
    """list_paginated returns the page and the total count."""
    for name in ["A", "B", "C"]:
        projects.create(ProjectCreate(name=name))
    page = projects.list_paginated(limit=2, offset=0)
    assert page.total == 3
    assert len(page.results) == 2


def test_update_and_replace_work_item(projects, statuses, types, work_items, seeded):
    """Work items can be partially updated and fully replaced."""
    other = seed_project(projects, statuses, types, name="Other")
    item = work_items.create(new_task(seeded, "Task", description="Desc"))

    updated = work_items.update(
        item.id, WorkItemUpdate(status_id=seeded.in_progress_id)
    )
    assert updated.status_id == seeded.in_progress_id
    assert updated.title == "Task"

    replaced = work_items.replace(
        item.id,
        WorkItemReplace(
            title="New",
            project_id=other.project_id,
            type_id=other.task_id,
            status_id=other.done_id,
        ),
    )
    assert replaced.id == item.id
    assert replaced.created_at == item.created_at
    assert replaced.project_id == other.project_id
    assert replaced.status_id == other.done_id
    assert replaced.description is None


def test_list_paginated_filters_by_project(
    projects, statuses, types, work_items, seeded
):
    """list_paginated filters by project and counts only matching items."""
    other = seed_project(projects, statuses, types, name="Other")
    work_items.create(new_task(seeded, "A"))
    work_items.create(new_task(other, "B"))
    work_items.create(new_task(other, "C"))

    everything = work_items.list_paginated(limit=10, offset=0)
    assert everything.total == 3
    assert len(work_items.list_all()) == 3
    assert work_items.count() == 3
    assert work_items.count(project_id=other.project_id) == 2

    filtered = work_items.list_paginated(limit=1, offset=0, project_id=other.project_id)
    assert filtered.total == 2
    assert len(filtered.results) == 1
    assert all(item.project_id == other.project_id for item in filtered.results)


def test_search_treats_like_wildcards_literally(work_items, project_id, seeded):
    """% and _ in the search text match only themselves, not any character."""
    work_items.create(new_task(seeded, "100% done"))
    work_items.create(new_task(seeded, "100 done"))
    work_items.create(new_task(seeded, "snake_case"))
    work_items.create(new_task(seeded, "snakeXcase"))

    assert work_items.list_paginated(limit=10, offset=0, search="100%").total == 1
    assert work_items.list_paginated(limit=10, offset=0, search="snake_case").total == 1


def test_search_projects_and_boards_by_name(engine, project_id):
    """Projects and boards are searched by name and description."""
    projects = SQLiteProjectBackend(engine)
    boards = SQLiteBoardBackend(engine)
    projects.create(ProjectCreate(name="Alpha", description="Shared"))
    boards.create(BoardCreate(name="Alpha board", project_id=project_id))
    boards.create(
        BoardCreate(name="Beta", description="alpha inside", project_id=project_id)
    )

    assert projects.list_paginated(limit=10, offset=0, search="shared").total == 1
    board_page = boards.list_paginated(limit=10, offset=0, search="ALPHA")
    assert board_page.total == 2


def test_trashed_is_stored_and_filtered(work_items, project_id, seeded):
    """The trashed flag persists and list_paginated filters on it."""
    item = work_items.create(new_task(seeded, "Task"))
    assert item.trashed is False

    work_items.update(item.id, WorkItemUpdate(trashed=True))
    assert work_items.get_by_id(item.id).trashed is True
    assert work_items.list_paginated(10, 0, trashed=True).total == 1
    assert work_items.list_paginated(10, 0, trashed=False).total == 0


def test_delete_work_item(work_items, project_id, seeded):
    item = work_items.create(new_task(seeded, "Task"))
    work_items.delete(item.id)
    with pytest.raises(ValueError):
        work_items.get_by_id(item.id)


def test_board_crud(engine, project_id):
    """Boards can be created, read, updated, replaced, listed and deleted."""
    boards = SQLiteBoardBackend(engine)
    board = boards.create(
        BoardCreate(name="Foo", filter="project.name == 'foo'", project_id=project_id)
    )
    assert boards.get_by_id(board.id) == board

    updated = boards.update(board.id, BoardUpdate(name="Renamed"))
    assert updated.name == "Renamed"
    assert updated.filter == "project.name == 'foo'"

    replaced = boards.replace(
        board.id, BoardReplace(name="Final", project_id=project_id)
    )
    assert replaced.filter is None

    page = boards.list_paginated(limit=10, offset=0)
    assert page.total == 1

    boards.delete(board.id)
    with pytest.raises(NotFoundError):
        boards.get_by_id(board.id)


def test_unknown_filter_field_raises(projects, work_items, project_id):
    """Filtering on a name the entity does not have is a ValueError."""
    with pytest.raises(ValueError, match="Unknown filter field 'projct_id'"):
        work_items.count(projct_id=project_id)
    with pytest.raises(ValueError, match="Unknown filter field 'nope'"):
        projects.list_paginated(limit=10, offset=0, nope="x")


def test_delete_project(projects):
    project = projects.create(ProjectCreate(name="Alpha"))
    projects.delete(project.id)
    with pytest.raises(NotFoundError):
        projects.get_by_id(project.id)


def test_create_subtask_and_list_by_parent(work_items, project_id, seeded):
    """Subtasks are stored with their parent and can be listed by it."""
    parent = work_items.create(new_task(seeded, "Parent"))
    child = work_items.create(new_subtask(seeded, parent.id, "Child"))
    work_items.create(new_task(seeded, "Unrelated"))

    assert child.type_id == seeded.subtask_id
    assert child.parent_id == parent.id
    page = work_items.list_paginated(limit=10, offset=0, parent_id=parent.id)
    assert page.total == 1
    assert page.results[0].id == child.id


def test_database_rejects_deleting_task_with_subtasks(work_items, project_id, seeded):
    """The foreign key blocks deleting a task that still has subtasks."""
    parent = work_items.create(new_task(seeded, "Parent"))
    work_items.create(new_subtask(seeded, parent.id, "Child"))
    with pytest.raises(IntegrityError):
        work_items.delete(parent.id)


def test_database_rejects_orphan_work_item(engine, seeded):
    """The foreign key itself rejects a work item pointing at no project."""
    with Session(engine) as session:
        session.add(
            WorkItemRow(
                id=uuid4(),
                title="Orphan",
                description=None,
                project_id=uuid4(),
                type_id=seeded.task_id,
                status_id=seeded.open_id,
                created_at=utc_now(),
                modified_at=utc_now(),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_startup_adds_missing_labels_column(tmp_path):
    """An existing database without labels columns gets them on startup."""
    url = f"sqlite:///{tmp_path / 'old.db'}"
    engine = create_sqlite_engine(url)
    with engine.begin() as conn:
        for table in ("projects", "boards", "work_items"):
            conn.exec_driver_sql(f"ALTER TABLE {table} DROP COLUMN labels")
    engine.dispose()

    engine = create_sqlite_engine(url)
    project = SQLiteProjectBackend(engine).create(ProjectCreate(name="Old"))
    assert project.labels == []
    board = SQLiteBoardBackend(engine).create(
        BoardCreate(name="Old", project_id=project.id)
    )
    assert board.labels == []
    seeded = seed_project(
        SQLiteProjectBackend(engine),
        SQLiteStatusBackend(engine),
        SQLiteWorkItemTypeBackend(engine),
    )
    work_items = SQLiteWorkItemBackend(engine)
    item = work_items.create(new_task(seeded, "Old"))
    assert item.labels == []


def test_status_and_type_tables_exist(engine):
    """The tables for project statuses and types are created on startup."""
    tables = set(inspect(engine).get_table_names())
    assert {"statuses", "work_item_types", "status_transitions"} <= tables


def test_status_rejects_missing_project(engine):
    """A status must belong to an existing project."""
    with Session(engine) as session:
        session.add(
            StatusRow(
                id=uuid4(),
                project_id=uuid4(),
                name="Open",
                category="todo",
                position=0,
                created_at=utc_now(),
                modified_at=utc_now(),
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()


def test_function_round_trip(engine):
    """A saved function is stored and read back with its code and labels."""
    functions = SQLiteFunctionBackend(engine)
    created = functions.create(
        FunctionCreate(name="Hello", code="print(1)", labels=["demo"])
    )
    fetched = functions.get_by_id(created.id)
    assert fetched.code == "print(1)"
    assert fetched.labels == ["demo"]


def test_deleting_project_removes_its_statuses_and_types(engine, projects):
    """Statuses and types go with their project, and transitions with their status."""
    project = projects.create(ProjectCreate(name="Alpha"))
    now = utc_now()
    status_a = StatusRow(
        id=uuid4(),
        project_id=project.id,
        name="A",
        category="todo",
        position=0,
        created_at=now,
        modified_at=now,
    )
    status_b = StatusRow(
        id=uuid4(),
        project_id=project.id,
        name="B",
        category="done",
        position=1,
        created_at=now,
        modified_at=now,
    )
    with Session(engine) as session:
        session.add_all(
            [
                status_a,
                status_b,
                WorkItemTypeRow(
                    id=uuid4(),
                    project_id=project.id,
                    name="Task",
                    level="standard",
                    position=0,
                    created_at=now,
                    modified_at=now,
                ),
                StatusTransitionRow(
                    id=uuid4(),
                    project_id=project.id,
                    from_status_id=status_a.id,
                    to_status_id=status_b.id,
                    created_at=now,
                    modified_at=now,
                ),
            ]
        )
        session.commit()

    projects.delete(project.id)

    with Session(engine) as session:
        assert session.scalar(select(func.count()).select_from(StatusRow)) == 0
        assert session.scalar(select(func.count()).select_from(WorkItemTypeRow)) == 0
        assert (
            session.scalar(select(func.count()).select_from(StatusTransitionRow)) == 0
        )
