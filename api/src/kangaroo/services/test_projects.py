import pytest

from kangaroo.errors import ConflictError, InvalidTemplateError, NotFoundError
from kangaroo.schemas import (
    BoardCreate,
    ProjectCreate,
    ProjectReplace,
    ProjectUpdate,
    WorkItemCreate,
)


def test_delete_project_with_boards_raises(project_service, boards):
    project = project_service.create(ProjectCreate(name="Alpha"))
    board = boards.create(BoardCreate(name="Board", project_id=project.id))
    with pytest.raises(ConflictError, match="still has boards"):
        project_service.delete(project.id)

    boards.delete(board.id)
    project_service.delete(project.id)
    with pytest.raises(NotFoundError):
        project_service.get(project.id)


def test_delete_project_with_work_items_raises(project_service, work_item_service):
    project = project_service.create(ProjectCreate(name="Alpha"))
    work_types = work_item_service._types.list_all(project_id=project.id)
    task_type = next(t for t in work_types if t.name == "Task")
    item = work_item_service.create(
        WorkItemCreate(summary="Task", project_id=project.id, type_id=task_type.id)
    )
    with pytest.raises(ConflictError, match="still has work items"):
        project_service.delete(project.id)

    work_item_service.delete(item.id)
    project_service.delete(project.id)
    with pytest.raises(NotFoundError):
        project_service.get(project.id)


def test_project_update_and_replace(project_service):
    created = project_service.create(ProjectCreate(name="Alpha", description="First"))
    updated = project_service.update(created.id, ProjectUpdate(name="Renamed"))
    assert updated.name == "Renamed"
    assert updated.description == "First"

    replaced = project_service.replace(created.id, ProjectReplace(name="Final"))
    assert replaced.name == "Final"
    assert replaced.description is None


def test_create_project_with_unknown_template_creates_nothing(
    project_service, projects, statuses
):
    """An unknown template is rejected before the project is stored."""
    with pytest.raises(InvalidTemplateError):
        project_service.create(ProjectCreate(name="Bad"), template="Nope")
    assert projects.count() == 0
    assert statuses.count() == 0


def test_project_copy_is_independent_of_template(project_service, statuses, project_id):
    """Each project gets its own status rows, not shared ones."""
    created = project_service.create(ProjectCreate(name="Second"))
    own = statuses.list_all(project_id=created.id)
    assert len(own) == 3
    assert not {s.id for s in own} & {
        s.id for s in statuses.list_all(project_id=project_id)
    }
