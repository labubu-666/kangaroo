from uuid import uuid4

import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from kangaroo.errors import NotFoundError
from kangaroo.repositories import (
    ArticleRepository,
    BoardRepository,
    FunctionRepository,
    KnowledgeBaseRepository,
    ProjectRepository,
    create_engine_for,
)
from kangaroo.repositories.repositories import utc_now
from kangaroo.repositories.tables import (
    StatusRow,
    StatusTransitionRow,
    WorkItemRow,
    WorkItemTypeRow,
)
from kangaroo.schemas import (
    ArticleCreate,
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    FunctionCreate,
    KnowledgeBaseCreate,
    ProjectCreate,
    ProjectReplace,
    ProjectUpdate,
    WorkItemReplace,
    WorkItemUpdate,
)
from kangaroo.testing import new_subtask, new_task, seed_project


@pytest.fixture
def seeded(projects, statuses, types):
    """A project with the To Do List statuses and types."""
    return seed_project(projects, statuses, types)


@pytest.fixture
def project_id(seeded):
    return seeded.project_id


@pytest.mark.parametrize("url", ["sqlite://memo", "sqlite:///", "memory://", "sqlite:"])
def test_engine_rejects_urls_that_are_not_memory_or_a_file(url):
    """A typo such as sqlite://memo is refused instead of giving a lost database."""
    with pytest.raises(ValueError, match="Unsupported DATABASE_URL"):
        create_engine_for(url)


def test_engine_accepts_a_file_url(tmp_path):
    """sqlite:///path.db creates a file database at that path."""
    path = tmp_path / "kangaroo.db"
    engine = create_engine_for(f"sqlite:///{path}")
    engine.dispose()
    assert path.exists()


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
    assert updated.summary == "Task"

    replaced = work_items.replace(
        item.id,
        WorkItemReplace(
            summary="New",
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


def test_search_projects_and_boards_by_name(session, project_id):
    """Projects and boards are searched by name and description."""
    projects = ProjectRepository(session)
    boards = BoardRepository(session)
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


def test_board_crud(session, project_id):
    """Boards can be created, read, updated, replaced, listed and deleted."""
    boards = BoardRepository(session)
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


def test_count_by_groups_and_respects_filters(work_items, seeded):
    """count_by returns one count per value present, honouring the other filters."""
    first = work_items.create(new_task(seeded, "One"))
    work_items.create(new_task(seeded, "Two"))
    work_items.update(first.id, WorkItemUpdate(trashed=True))

    assert work_items.count_by("status_id", trashed=False) == {seeded.open_id: 1}
    assert work_items.count_by("status_id") == {seeded.open_id: 2}
    assert work_items.count_by("status_id", project_id=uuid4()) == {}


def test_count_by_unknown_field_raises(work_items):
    """Grouping by a name the entity does not have is a ValueError."""
    with pytest.raises(ValueError, match="Unknown filter field 'nope'"):
        work_items.count_by("nope")


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
                summary="Orphan",
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


def test_function_round_trip(session):
    """A saved function is stored and read back with its code and labels."""
    functions = FunctionRepository(session)
    created = functions.create(
        FunctionCreate(name="Hello", code="print(1)", labels=["demo"])
    )
    fetched = functions.get_by_id(created.id)
    assert fetched.code == "print(1)"
    assert fetched.labels == ["demo"]


def test_article_round_trip(session):
    """An article is stored in its knowledge base and read back with its body."""
    knowledge_base = KnowledgeBaseRepository(session).create(
        KnowledgeBaseCreate(name="Docs")
    )
    articles = ArticleRepository(session)
    created = articles.create(
        ArticleCreate(
            knowledge_base_id=knowledge_base.id,
            title="Setup",
            body="# Setup",
            labels=["howto"],
        )
    )
    fetched = articles.get_by_id(created.id)
    assert fetched.knowledge_base_id == knowledge_base.id
    assert fetched.body == "# Setup"
    assert fetched.labels == ["howto"]


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
