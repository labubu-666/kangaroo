from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.backends import (
    InMemoryProjectBackend,
    InMemoryStatusBackend,
    InMemoryStatusTransitionBackend,
    InMemoryWorkItemBackend,
    InMemoryWorkItemTypeBackend,
)
from kangaroo.routes.dependencies import (
    get_project_backend,
    get_status_backend,
    get_status_transition_backend,
    get_work_item_backend,
    get_work_item_type_backend,
)
from kangaroo.testing import type_id


@pytest.fixture
def fresh_project_backend():
    """Provide a fresh in-memory project backend for each test."""
    return InMemoryProjectBackend()


@pytest.fixture
def fresh_work_item_backend():
    """Provide a fresh in-memory work item backend for each test."""
    return InMemoryWorkItemBackend()


@pytest.fixture
def fresh_status_backend():
    return InMemoryStatusBackend()


@pytest.fixture
def fresh_work_item_type_backend():
    return InMemoryWorkItemTypeBackend()


@pytest.fixture
def fresh_status_transition_backend():
    return InMemoryStatusTransitionBackend()


@pytest.fixture
def client(
    fresh_project_backend,
    fresh_work_item_backend,
    fresh_status_backend,
    fresh_work_item_type_backend,
    fresh_status_transition_backend,
):
    """Provide a TestClient with overridden backend dependencies."""
    app.dependency_overrides[get_project_backend] = lambda: fresh_project_backend
    app.dependency_overrides[get_work_item_backend] = lambda: fresh_work_item_backend
    app.dependency_overrides[get_status_backend] = lambda: fresh_status_backend
    app.dependency_overrides[get_work_item_type_backend] = lambda: (
        fresh_work_item_type_backend
    )
    app.dependency_overrides[get_status_transition_backend] = lambda: (
        fresh_status_transition_backend
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_project(client):
    """POST /api/v1/projects creates a project."""
    response = client.post(
        "/api/v1/projects", json={"name": "Alpha", "description": "First"}
    )
    assert response.status_code == 201
    data = response.json()
    assert isinstance(UUID(data["id"]), UUID)
    assert data["name"] == "Alpha"
    assert data["description"] == "First"
    assert "created_at" in data


def test_create_project_minimal(client):
    """POST /api/v1/projects with name only leaves description empty."""
    response = client.post("/api/v1/projects", json={"name": "Beta"})
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_project_missing_name(client):
    """POST /api/v1/projects without a name returns validation error."""
    response = client.post("/api/v1/projects", json={"description": "No name"})
    assert response.status_code == 422


def test_list_projects(client):
    """GET /api/v1/projects returns the created projects."""
    client.post("/api/v1/projects", json={"name": "Alpha"})

    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["name"] == "Alpha"
    assert data["limit"] == 10
    assert data["offset"] == 0


def test_list_projects_with_limit_and_offset(client):
    """GET /api/v1/projects?limit=2&offset=1 returns the middle page."""
    for i in range(1, 4):
        client.post("/api/v1/projects", json={"name": f"Project {i}"})

    response = client.get("/api/v1/projects?limit=1&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Project 2"
    assert data["total"] == 3


def test_list_projects_search(client):
    """GET /api/v1/projects?search= matches name or description."""
    client.post("/api/v1/projects", json={"name": "Alpha"})
    client.post("/api/v1/projects", json={"name": "Beta", "description": "alpha"})
    client.post("/api/v1/projects", json={"name": "Gamma"})

    data = client.get("/api/v1/projects?search=ALPHA").json()
    assert data["total"] == 2
    assert [project["name"] for project in data["results"]] == ["Alpha", "Beta"]


def test_list_projects_limit_validation(client):
    """GET /api/v1/projects?limit=0 returns validation error."""
    response = client.get("/api/v1/projects?limit=0")
    assert response.status_code == 422


def test_get_project(client):
    """GET /api/v1/projects/{id} returns a specific project."""
    create_response = client.post("/api/v1/projects", json={"name": "Gamma"})
    project_id = create_response.json()["id"]

    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == project_id
    assert response.json()["name"] == "Gamma"


def test_get_project_not_found(client):
    """GET /api/v1/projects/{id} returns 404 for missing project."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/api/v1/projects/{fake_uuid}")
    assert response.status_code == 404


def test_update_project_name(client):
    """PATCH /api/v1/projects/{id} updates name only."""
    create_response = client.post(
        "/api/v1/projects", json={"name": "Old", "description": "Desc"}
    )
    project_id = create_response.json()["id"]

    response = client.patch(f"/api/v1/projects/{project_id}", json={"name": "New"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New"
    assert data["description"] == "Desc"


def test_update_project_name_null_returns_422(client):
    """PATCH /api/v1/projects/{id} rejects an explicit null name."""
    project_id = client.post("/api/v1/projects", json={"name": "Keep"}).json()["id"]

    response = client.patch(f"/api/v1/projects/{project_id}", json={"name": None})
    assert response.status_code == 422
    assert client.get(f"/api/v1/projects/{project_id}").json()["name"] == "Keep"


def test_update_project_not_found(client):
    """PATCH /api/v1/projects/{id} returns 404 for missing project."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.patch(f"/api/v1/projects/{fake_uuid}", json={"name": "New"})
    assert response.status_code == 404


def test_replace_project(client):
    """PUT /api/v1/projects/{id} replaces the project and keeps created_at."""
    create_response = client.post(
        "/api/v1/projects", json={"name": "Old", "description": "Old desc"}
    )
    project_id = create_response.json()["id"]
    original_created_at = create_response.json()["created_at"]

    response = client.put(f"/api/v1/projects/{project_id}", json={"name": "New"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New"
    assert data["description"] is None
    assert data["created_at"] == original_created_at


def test_replace_project_not_found(client):
    """PUT /api/v1/projects/{id} returns 404 for missing project."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.put(f"/api/v1/projects/{fake_uuid}", json={"name": "New"})
    assert response.status_code == 404


def test_delete_project(client):
    """DELETE /api/v1/projects/{id} deletes an empty project."""
    project_id = client.post("/api/v1/projects", json={"name": "Temp"}).json()["id"]

    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404


def test_delete_project_not_found(client):
    """DELETE /api/v1/projects/{id} returns 404 for missing project."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.delete(f"/api/v1/projects/{fake_uuid}")
    assert response.status_code == 404


def test_delete_project_with_work_items_forbidden(client):
    """DELETE /api/v1/projects/{id} returns 409 while it still has work items."""
    project_id = client.post("/api/v1/projects", json={"name": "Busy"}).json()["id"]
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )

    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 409

    assert client.get(f"/api/v1/projects/{project_id}").status_code == 200


def test_delete_project_after_work_items_removed(client):
    """DELETE /api/v1/projects/{id} succeeds once its work items are gone."""
    project_id = client.post("/api/v1/projects", json={"name": "Busy"}).json()["id"]
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    ).json()["id"]
    client.delete(f"/api/v1/work-items/{item_id}")

    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204


def test_project_labels_default_to_empty(client):
    """A project created without labels has an empty label list."""
    response = client.post("/api/v1/projects", json={"name": "Plain"})
    assert response.json()["labels"] == []


def test_create_project_with_labels(client):
    """POST /api/v1/projects stores labels, trimmed and without duplicates."""
    response = client.post(
        "/api/v1/projects",
        json={"name": "Tagged", "labels": [" news ", "sport", "news"]},
    )
    assert response.status_code == 201
    assert response.json()["labels"] == ["news", "sport"]


def test_create_project_empty_label_returns_422(client):
    """POST /api/v1/projects rejects a blank label."""
    response = client.post("/api/v1/projects", json={"name": "Bad", "labels": ["  "]})
    assert response.status_code == 422


def test_update_project_labels_keeps_other_fields(client):
    """PATCH /api/v1/projects/{id} changes labels and keeps the rest."""
    project_id = client.post(
        "/api/v1/projects", json={"name": "Keep", "labels": ["old"]}
    ).json()["id"]

    response = client.patch(f"/api/v1/projects/{project_id}", json={"labels": ["new"]})
    assert response.status_code == 200
    assert response.json()["labels"] == ["new"]
    assert response.json()["name"] == "Keep"


def test_patch_without_labels_keeps_labels(client):
    """PATCH without labels leaves the existing labels alone."""
    project_id = client.post(
        "/api/v1/projects", json={"name": "Keep", "labels": ["kept"]}
    ).json()["id"]

    response = client.patch(f"/api/v1/projects/{project_id}", json={"name": "New"})
    assert response.json()["labels"] == ["kept"]


def test_replace_project_labels(client):
    """PUT /api/v1/projects/{id} replaces labels; omitting them clears the list."""
    project_id = client.post(
        "/api/v1/projects", json={"name": "Old", "labels": ["old"]}
    ).json()["id"]

    replaced = client.put(
        f"/api/v1/projects/{project_id}", json={"name": "New", "labels": ["fresh"]}
    )
    assert replaced.json()["labels"] == ["fresh"]

    cleared = client.put(f"/api/v1/projects/{project_id}", json={"name": "New"})
    assert cleared.json()["labels"] == []
