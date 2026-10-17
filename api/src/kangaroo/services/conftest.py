import pytest

from kangaroo.schemas import (
    ProjectCreate,
)
from kangaroo.services import ProjectService, WorkflowService, WorkItemService
from kangaroo.testing import seed_project


@pytest.fixture
def seeded(projects, statuses, types):
    """A project with the To Do List statuses and types."""
    return seed_project(projects, statuses, types)


@pytest.fixture
def other(projects, statuses, types):
    """A second project, to test moves and cross-project checks."""
    return seed_project(projects, statuses, types, name="Other")


@pytest.fixture
def project_id(project_service):
    """A project created through the service, so it gets the default template."""
    return project_service.create(ProjectCreate(name="Test")).id


@pytest.fixture
def project_service(projects, work_items, boards, statuses, types, transitions):
    return ProjectService(projects, work_items, boards, statuses, types, transitions)


@pytest.fixture
def work_item_service(work_items, projects, statuses, types, transitions):
    return WorkItemService(work_items, projects, statuses, types, transitions)


@pytest.fixture
def workflow(projects, statuses, types, transitions, work_items):
    return WorkflowService(projects, statuses, types, transitions, work_items)
