from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.backends import (
    InMemoryBoardBackend,
    InMemoryProjectBackend,
    InMemoryStatusBackend,
    InMemoryStatusTransitionBackend,
    InMemoryWorkItemBackend,
    InMemoryWorkItemTypeBackend,
)
from kangaroo.routes.dependencies import (
    get_board_backend,
    get_project_backend,
    get_status_backend,
    get_status_transition_backend,
    get_work_item_backend,
    get_work_item_type_backend,
)


@pytest.fixture
def client():
    """Provide a TestClient with fresh in-memory backends for each test."""
    boards = InMemoryBoardBackend()
    work_items = InMemoryWorkItemBackend()
    projects = InMemoryProjectBackend()
    statuses = InMemoryStatusBackend()
    types = InMemoryWorkItemTypeBackend()
    transitions = InMemoryStatusTransitionBackend()
    app.dependency_overrides[get_board_backend] = lambda: boards
    app.dependency_overrides[get_work_item_backend] = lambda: work_items
    app.dependency_overrides[get_project_backend] = lambda: projects
    app.dependency_overrides[get_status_backend] = lambda: statuses
    app.dependency_overrides[get_work_item_type_backend] = lambda: types
    app.dependency_overrides[get_status_transition_backend] = lambda: transitions
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def project_id(client):
    """Create a project from the default template."""
    return client.post("/api/v1/projects", json={"name": "Test"}).json()["id"]


def _statuses(client, project_id):
    return client.get(f"/api/v1/statuses/?project_id={project_id}").json()


def test_create_project_copies_default_template(client, project_id):
    """A new project gets the To Do List types and statuses in position order."""
    statuses = _statuses(client, project_id)
    assert [(s["name"], s["category"], s["position"]) for s in statuses] == [
        ("Open", "todo", 0),
        ("In Progress", "in_progress", 1),
        ("Done", "done", 2),
    ]
    types = client.get(f"/api/v1/work-item-types/?project_id={project_id}").json()
    assert [(t["name"], t["level"], t["position"]) for t in types] == [
        ("Task", "standard", 0),
        ("Subtask", "subtask", 1),
    ]


def test_create_project_with_named_template(client):
    """An explicit template name is accepted."""
    response = client.post(
        "/api/v1/projects", json={"name": "Named", "template": "To Do List"}
    )
    assert response.status_code == 201


def test_create_project_unknown_template_returns_400(client):
    response = client.post("/api/v1/projects", json={"name": "Bad", "template": "Nope"})
    assert response.status_code == 400
    assert "Unknown template" in response.json()["detail"]


def test_template_is_not_in_project_response(client, project_id):
    """The template is only used at creation and is not stored on the project."""
    project = client.get(f"/api/v1/projects/{project_id}").json()
    assert "template" not in project


def test_update_project_keeps_statuses(client, project_id):
    """PATCH does not change the project's statuses or types."""
    before = _statuses(client, project_id)
    client.patch(f"/api/v1/projects/{project_id}", json={"name": "Renamed"})
    assert _statuses(client, project_id) == before


def test_create_status_defaults_to_last_position(client, project_id):
    response = client.post(
        "/api/v1/statuses/",
        json={"project_id": project_id, "name": "Review", "category": "in_progress"},
    )
    assert response.status_code == 201
    assert response.json()["position"] == 3


def test_create_status_with_missing_project_returns_422(client):
    response = client.post(
        "/api/v1/statuses/",
        json={"project_id": str(uuid4()), "name": "X", "category": "todo"},
    )
    assert response.status_code == 422


def test_create_status_invalid_category_returns_422(client, project_id):
    response = client.post(
        "/api/v1/statuses/",
        json={"project_id": project_id, "name": "X", "category": "maybe"},
    )
    assert response.status_code == 422


def test_get_missing_status_returns_404(client):
    response = client.get(f"/api/v1/statuses/{uuid4()}")
    assert response.status_code == 404


def test_patch_status_position_changes_list_order(client, project_id):
    """Setting a status to a unique position moves it in the project's list."""
    done = next(s for s in _statuses(client, project_id) if s["name"] == "Done")
    client.patch(f"/api/v1/statuses/{done['id']}", json={"position": -1})
    assert _statuses(client, project_id)[0]["name"] == "Done"


def test_patch_status_null_name_returns_422(client, project_id):
    open_status = _statuses(client, project_id)[0]
    response = client.patch(
        f"/api/v1/statuses/{open_status['id']}", json={"name": None}
    )
    assert response.status_code == 422


def test_put_status_keeps_position_when_omitted(client, project_id):
    open_status = _statuses(client, project_id)[0]
    response = client.put(
        f"/api/v1/statuses/{open_status['id']}",
        json={"name": "Backlog", "category": "todo"},
    )
    assert response.status_code == 200
    assert response.json()["position"] == 0
