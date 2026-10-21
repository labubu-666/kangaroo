from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.routes.dependencies import get_engine
from kangaroo.testing import status_id, type_id


def _create(client, project_id, title="Task", **extra):
    return client.post(
        "/api/v1/work-items",
        json={
            "title": title,
            "project_id": project_id,
            "type_id": type_id(client, project_id, "task"),
            **extra,
        },
    )


@pytest.fixture
def client(engine):
    """Provide a TestClient that uses fresh database for each test."""
    app.dependency_overrides[get_engine] = lambda: engine
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def project_id(client):
    """Create a project for the tests to put their work items in."""
    return client.post("/api/v1/projects", json={"name": "Test"}).json()["id"]


def test_create_work_item(client, project_id):
    """POST /api/v1/work-items creates a work item."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Fix bug",
            "description": "There's a bug in the UI",
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert isinstance(UUID(data["id"]), UUID)
    assert data["title"] == "Fix bug"
    assert data["description"] == "There's a bug in the UI"
    assert data["status_id"] == status_id(client, project_id, "open")
    assert "created_at" in data


def test_create_work_item_minimal(client, project_id):
    """POST /api/v1/work-items creates a work item with title only."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "New task",
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert isinstance(UUID(data["id"]), UUID)
    assert data["title"] == "New task"
    assert data["description"] is None
    assert data["status_id"] == status_id(client, project_id, "open")


def test_list_work_items_empty(client):
    """GET /api/v1/work-items returns empty paginated response initially."""
    response = client.get("/api/v1/work-items")
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["total"] == 0


def test_list_work_items(client, project_id):
    """GET /api/v1/work-items returns created items with pagination."""
    _create(client, project_id, title="Task 1")
    _create(client, project_id, title="Task 2")

    response = client.get("/api/v1/work-items")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["title"] == "Task 1"
    assert data["results"][1]["title"] == "Task 2"
    assert data["limit"] == 10
    assert data["offset"] == 0
    assert data["total"] == 2


def test_list_work_items_search(client, project_id):
    """GET /api/v1/work-items?search= matches title or description, ignoring case."""
    _create(client, project_id, title="Login bug")
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Other",
            "description": "LOGIN page",
            "project_id": project_id,
        },
    )
    _create(client, project_id, title="Unrelated")

    response = client.get("/api/v1/work-items?search=login")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert [item["title"] for item in data["results"]] == ["Login bug", "Other"]


def test_list_work_items_search_too_long(client):
    """GET /api/v1/work-items with a search over 200 characters returns 422."""
    response = client.get(f"/api/v1/work-items?search={'a' * 201}")
    assert response.status_code == 422


def test_list_work_items_filter(client, project_id):
    """GET /api/v1/work-items?filter= returns only the matching items."""
    _create(client, project_id, title="Open")
    in_progress = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Working",
            "project_id": project_id,
        },
    ).json()
    client.patch(
        f"/api/v1/work-items/{in_progress['id']}",
        json={"status_id": status_id(client, project_id, "in_progress")},
    )

    response = client.get("/api/v1/work-items?filter=status == 'in_progress'")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert [item["title"] for item in data["results"]] == ["Working"]


def test_list_work_items_filter_with_paging_and_search(client, project_id):
    """The filter, search and paging are applied together, with total after the filter."""
    for title in ["Login bug", "Login task", "Other bug"]:
        _create(client, project_id, title=title)

    response = client.get(
        "/api/v1/work-items?filter=title ~ 'bug'&search=login&limit=1&offset=0"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert [item["title"] for item in data["results"]] == ["Login bug"]


def test_list_work_items_invalid_filter(client):
    """An invalid filter is rejected with 422."""
    response = client.get("/api/v1/work-items?filter=status == open")
    assert response.status_code == 422


def test_get_work_item(client, project_id):
    """GET /api/v1/work-items/{id} returns a specific item."""
    create_response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )
    item_id = create_response.json()["id"]

    response = client.get(f"/api/v1/work-items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == item_id
    assert data["title"] == "Task"


def test_get_work_item_not_found(client):
    """GET /api/v1/work-items/{id} returns 404 for missing item."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.get(f"/api/v1/work-items/{fake_uuid}")
    assert response.status_code == 404


def test_update_work_item_title_null_returns_422(client, project_id):
    """PATCH /api/v1/work-items/{id} rejects an explicit null title."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Keep",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.patch(f"/api/v1/work-items/{item_id}", json={"title": None})
    assert response.status_code == 422
    assert client.get(f"/api/v1/work-items/{item_id}").json()["title"] == "Keep"


def test_update_work_item_title(client, project_id):
    """PATCH /api/v1/work-items/{id} updates title."""
    create_response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Old Title",
            "description": "Desc",
            "project_id": project_id,
        },
    )
    item_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/work-items/{item_id}",
        json={"type_id": type_id(client, project_id, "task"), "title": "New Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["description"] == "Desc"


def test_update_work_item_status(client, project_id):
    """PATCH /api/v1/work-items/{id} updates status."""
    create_response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )
    item_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/work-items/{item_id}",
        json={"status_id": status_id(client, project_id, "in_progress")},
    )
    assert response.status_code == 200
    assert response.json()["status_id"] == status_id(client, project_id, "in_progress")


def test_update_work_item_description(client, project_id):
    """PATCH /api/v1/work-items/{id} updates description."""
    create_response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )
    item_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/work-items/{item_id}", json={"description": "New description"}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "New description"


def test_update_work_item_not_found(client, project_id):
    """PATCH /api/v1/work-items/{id} returns 404 for missing item."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.patch(
        f"/api/v1/work-items/{fake_uuid}",
        json={"type_id": type_id(client, project_id, "task"), "title": "New"},
    )
    assert response.status_code == 404


def test_replace_work_item_full(client, project_id):
    """PUT /api/v1/work-items/{id} replaces entire item."""
    create_response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Old",
            "description": "Old desc",
            "project_id": project_id,
        },
    )
    item_id = create_response.json()["id"]
    original_created_at = create_response.json()["created_at"]

    response = client.put(
        f"/api/v1/work-items/{item_id}",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "New",
            "description": "New desc",
            "status_id": status_id(client, project_id, "in_progress"),
            "project_id": project_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New"
    assert data["description"] == "New desc"
    assert data["status_id"] == status_id(client, project_id, "in_progress")
    assert data["created_at"] == original_created_at  # preserved


def test_replace_work_item_minimal(client, project_id):
    """PUT /api/v1/work-items/{id} with title only, description defaults to None."""
    create_response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Original",
            "description": "Desc",
            "project_id": project_id,
        },
    )
    item_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/work-items/{item_id}",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Replaced",
            "project_id": project_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Replaced"
    assert data["description"] is None
    assert data["status_id"] == status_id(client, project_id, "open")


def test_replace_work_item_not_found(client, project_id):
    """PUT /api/v1/work-items/{id} returns 404 for missing item."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.put(
        f"/api/v1/work-items/{fake_uuid}",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "New",
            "project_id": project_id,
        },
    )
    assert response.status_code == 404


def test_delete_work_item(client, project_id):
    """DELETE /api/v1/work-items/{id} deletes an item."""
    create_response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )
    item_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/work-items/{item_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/v1/work-items/{item_id}")
    assert get_response.status_code == 404


def test_trash_and_restore_work_item(client, project_id):
    """PATCH /api/v1/work-items/{id} trashes and restores an item."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.patch(f"/api/v1/work-items/{item_id}", json={"trashed": True})
    assert response.status_code == 200
    assert response.json()["trashed"] is True

    response = client.patch(f"/api/v1/work-items/{item_id}", json={"trashed": False})
    assert response.status_code == 200
    assert response.json()["trashed"] is False


def test_new_work_item_is_not_trashed(client, project_id):
    """A new work item starts untrashed."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )
    assert response.json()["trashed"] is False


def test_replace_work_item_resets_trashed(client, project_id):
    """PUT without trashed restores the item, since it is a full replace."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    ).json()["id"]
    client.patch(f"/api/v1/work-items/{item_id}", json={"trashed": True})

    response = client.put(
        f"/api/v1/work-items/{item_id}",
        json={
            "title": "Task",
            "project_id": project_id,
            "type_id": type_id(client, project_id, "task"),
        },
    )
    assert response.json()["trashed"] is False


def test_list_work_items_filters_trashed(client, project_id):
    """Without a filter all items are listed; trashed == true/false selects one state."""
    live_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Live",
            "project_id": project_id,
        },
    ).json()["id"]
    trashed_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Trashed",
            "project_id": project_id,
        },
    ).json()["id"]
    client.patch(f"/api/v1/work-items/{trashed_id}", json={"trashed": True})

    everything = client.get("/api/v1/work-items").json()
    assert sorted(item["id"] for item in everything["results"]) == sorted(
        [live_id, trashed_id]
    )

    live = client.get("/api/v1/work-items?filter=trashed == false").json()
    assert [item["id"] for item in live["results"]] == [live_id]

    trashed = client.get("/api/v1/work-items?filter=trashed == true").json()
    assert [item["id"] for item in trashed["results"]] == [trashed_id]


def test_delete_work_item_not_found(client):
    """DELETE /api/v1/work-items/{id} returns 404 for missing item."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.delete(f"/api/v1/work-items/{fake_uuid}")
    assert response.status_code == 404


def test_list_work_items_with_limit(client, project_id):
    """GET /api/v1/work-items?limit=2 returns paginated results."""
    for i in range(1, 6):
        _create(client, project_id, title=f"Task {i}")

    response = client.get("/api/v1/work-items?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["title"] == "Task 1"
    assert data["results"][1]["title"] == "Task 2"
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert data["total"] == 5


def test_list_work_items_with_offset(client, project_id):
    """GET /api/v1/work-items?offset=2 skips items and returns from offset."""
    for i in range(1, 6):
        _create(client, project_id, title=f"Task {i}")

    response = client.get("/api/v1/work-items?offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 3  # 5 - 2 = 3
    assert data["results"][0]["title"] == "Task 3"
    assert data["results"][1]["title"] == "Task 4"
    assert data["results"][2]["title"] == "Task 5"
    assert data["limit"] == 10
    assert data["offset"] == 2
    assert data["total"] == 5


def test_list_work_items_with_limit_and_offset(client, project_id):
    """GET /api/v1/work-items?limit=2&offset=1 returns middle page."""
    for i in range(1, 6):
        _create(client, project_id, title=f"Task {i}")

    response = client.get("/api/v1/work-items?limit=2&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["title"] == "Task 2"
    assert data["results"][1]["title"] == "Task 3"
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert data["total"] == 5


def test_list_work_items_last_page(client, project_id):
    """GET /api/v1/work-items on last page."""
    for i in range(1, 6):
        _create(client, project_id, title=f"Task {i}")

    response = client.get("/api/v1/work-items?limit=2&offset=4")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Task 5"
    assert data["limit"] == 2
    assert data["offset"] == 4
    assert data["total"] == 5


def test_list_work_items_limit_validation_below_min(client):
    """GET /api/v1/work-items?limit=0 returns validation error."""
    response = client.get("/api/v1/work-items?limit=0")
    assert response.status_code == 422


def test_list_work_items_limit_validation_above_max(client):
    """GET /api/v1/work-items?limit=101 returns validation error."""
    response = client.get("/api/v1/work-items?limit=101")
    assert response.status_code == 422


def test_list_work_items_offset_validation_negative(client):
    """GET /api/v1/work-items?offset=-1 returns validation error."""
    response = client.get("/api/v1/work-items?offset=-1")
    assert response.status_code == 422


def test_list_work_items_beyond_total(client, project_id):
    """GET /api/v1/work-items?offset=100 returns empty results when offset exceeds total."""
    _create(client, project_id, title="Task 1")
    _create(client, project_id, title="Task 2")

    response = client.get("/api/v1/work-items?offset=100")
    assert response.status_code == 200
    data = response.json()
    assert data["results"] == []
    assert data["limit"] == 10
    assert data["offset"] == 100
    assert data["total"] == 2


def test_create_work_item_in_project(client, project_id):
    """POST /api/v1/work-items with an existing project_id uses that project."""
    project_id = client.post("/api/v1/projects", json={"name": "Alpha"}).json()["id"]

    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    assert response.json()["project_id"] == project_id


def test_create_work_item_unknown_project(client, project_id):
    """POST /api/v1/work-items returns 422 for a project that does not exist."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": fake_uuid,
        },
    )
    assert response.status_code == 422


def test_create_work_item_null_project_returns_422(client, project_id):
    """POST /api/v1/work-items requires a project, so null is rejected."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": None,
        },
    )
    assert response.status_code == 422


def test_update_work_item_trashed_null_returns_422(client, project_id):
    """PATCH /api/v1/work-items/{id} rejects an explicit null trashed flag."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Keep",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.patch(f"/api/v1/work-items/{item_id}", json={"trashed": None})
    assert response.status_code == 422
    assert client.get(f"/api/v1/work-items/{item_id}").json()["trashed"] is False


def test_update_work_item_null_project(client, project_id):
    """PATCH /api/v1/work-items/{id} with project_id null returns 422."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.patch(f"/api/v1/work-items/{item_id}", json={"project_id": None})
    assert response.status_code == 422


def test_update_work_item_project(client, project_id):
    """PATCH /api/v1/work-items/{id} moves an item to another project."""
    project_id = client.post("/api/v1/projects", json={"name": "Beta"}).json()["id"]
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.patch(
        f"/api/v1/work-items/{item_id}", json={"project_id": project_id}
    )
    assert response.status_code == 200
    assert response.json()["project_id"] == project_id


def test_update_work_item_unknown_project(client, project_id):
    """PATCH /api/v1/work-items/{id} returns 422 for an unknown project."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    ).json()["id"]
    fake_uuid = "11111111-1111-1111-1111-111111111111"

    response = client.patch(
        f"/api/v1/work-items/{item_id}", json={"project_id": fake_uuid}
    )
    assert response.status_code == 422


def test_replace_work_item_unknown_project(client, project_id):
    """PUT /api/v1/work-items/{id} returns 422 for an unknown project."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    ).json()["id"]
    fake_uuid = "11111111-1111-1111-1111-111111111111"

    response = client.put(
        f"/api/v1/work-items/{item_id}",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": fake_uuid,
        },
    )
    assert response.status_code == 422


def test_list_work_items_filtered_by_project(client, project_id):
    """GET /api/v1/work-items?project_id= returns only that project's items."""
    other_id = client.post("/api/v1/projects", json={"name": "Gamma"}).json()["id"]
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, other_id, "task"),
            "title": "In project",
            "project_id": other_id,
        },
    )
    _create(client, project_id, title="In default")

    response = client.get(f"/api/v1/work-items?project_id={other_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["title"] == "In project"


def test_create_task_has_no_parent_field(client, project_id):
    """A task response has a task type and a null parent_id."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type_id"] == type_id(client, project_id, "task")
    assert data["parent_id"] is None


def test_create_work_item_without_type_returns_422(client, project_id):
    """type is required on create."""
    response = client.post(
        "/api/v1/work-items",
        json={"title": "Task", "project_id": project_id},
    )
    assert response.status_code == 422


def test_create_work_item_with_unknown_type_returns_422(client, project_id):
    """The type must be one of the project's types."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": "11111111-1111-1111-1111-111111111111",
            "title": "Epic",
            "project_id": project_id,
        },
    )
    assert response.status_code == 422


def test_create_task_with_parent_id_returns_422(client, project_id):
    """A task rejects parent_id instead of silently dropping it."""
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Task",
            "parent_id": parent_id,
            "project_id": project_id,
        },
    )
    assert response.status_code == 422


def test_create_subtask(client, project_id):
    """POST /api/v1/work-items creates a subtask under a task."""
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type_id"] == type_id(client, project_id, "subtask")
    assert data["parent_id"] == parent_id


def test_create_subtask_without_parent_returns_422(client, project_id):
    """A subtask must reference a parent."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "project_id": project_id,
        },
    )
    assert response.status_code == 422


def test_create_task_with_parent_returns_422(client, project_id):
    """Only subtasks may reference a parent."""
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.post(
        "/api/v1/work-items",
        json={
            "title": "Task",
            "type_id": type_id(client, project_id, "task"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    )
    assert response.status_code == 422


def test_create_subtask_with_unknown_parent_returns_422(client, project_id):
    """A subtask's parent must exist."""
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    response = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": fake_uuid,
            "project_id": project_id,
        },
    )
    assert response.status_code == 422


def test_create_subtask_under_subtask_returns_422(client, project_id):
    """Subtasks cannot be nested under other subtasks."""
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]
    subtask_id = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.post(
        "/api/v1/work-items",
        json={
            "title": "Grandchild",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": subtask_id,
            "project_id": project_id,
        },
    )
    assert response.status_code == 422


def test_create_subtask_in_other_project_returns_422(client, project_id):
    """A subtask must be in the same project as its parent."""
    other_id = client.post("/api/v1/projects", json={"name": "Alpha"}).json()["id"]
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": other_id,
        },
    )
    assert response.status_code == 422


def test_list_subtasks_of_parent(client, project_id):
    """GET /api/v1/work-items?parent_id= returns only that task's subtasks."""
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]
    client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    )
    _create(client, project_id, title="Unrelated")

    response = client.get(f"/api/v1/work-items?parent_id={parent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["title"] == "Child"


def test_delete_task_also_deletes_subtasks(client, project_id):
    """Deleting a task deletes its subtasks too."""
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]
    subtask_id = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    ).json()["id"]

    assert client.delete(f"/api/v1/work-items/{parent_id}").status_code == 204
    assert client.get(f"/api/v1/work-items/{subtask_id}").status_code == 404


def test_bulk_delete_ids(client, project_id):
    """POST /api/v1/work-items/bulk-delete removes the listed items and their subtasks."""
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]
    subtask_id = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.post(
        "/api/v1/work-items/bulk-delete", json={"ids": [parent_id, subtask_id]}
    )
    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    assert client.get(f"/api/v1/work-items/{parent_id}").status_code == 404


def test_bulk_delete_all_matching(client, project_id):
    """all_matching with a filter deletes only the items the filter matches."""
    for title in ["Login bug", "Other bug", "Feature"]:
        _create(client, project_id, title=title)

    response = client.post(
        "/api/v1/work-items/bulk-delete",
        json={"all_matching": True, "filter": "title ~ 'bug'"},
    )
    assert response.status_code == 200
    assert response.json() == {"deleted": 2}
    titles = [
        item["title"] for item in client.get("/api/v1/work-items").json()["results"]
    ]
    assert titles == ["Feature"]


def test_bulk_delete_rejects_ambiguous_requests(client):
    """Ids and all_matching are mutually exclusive, and one of them is required."""
    assert client.post("/api/v1/work-items/bulk-delete", json={}).status_code == 422
    assert (
        client.post(
            "/api/v1/work-items/bulk-delete",
            json={"ids": [str(uuid4())], "all_matching": True},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/work-items/bulk-delete",
            json={"ids": [str(uuid4())], "filter": "title ~ 'a'"},
        ).status_code
        == 422
    )


def test_bulk_delete_invalid_filter_returns_422(client):
    """An invalid filter in bulk delete is rejected and deletes nothing."""
    response = client.post(
        "/api/v1/work-items/bulk-delete",
        json={"all_matching": True, "filter": "status == open"},
    )
    assert response.status_code == 422


def test_move_task_with_subtasks_returns_409(client, project_id):
    """A task with subtasks cannot be moved to another project."""
    other_id = client.post("/api/v1/projects", json={"name": "Beta"}).json()["id"]
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]
    client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    )

    response = client.patch(
        f"/api/v1/work-items/{parent_id}", json={"project_id": other_id}
    )
    assert response.status_code == 409


def test_move_subtask_returns_409(client, project_id):
    """A subtask cannot be moved to another project."""
    other_id = client.post("/api/v1/projects", json={"name": "Beta"}).json()["id"]
    parent_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Parent",
            "project_id": project_id,
        },
    ).json()["id"]
    subtask_id = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.patch(
        f"/api/v1/work-items/{subtask_id}", json={"project_id": other_id}
    )
    assert response.status_code == 409


def test_labels_are_trimmed_and_deduplicated(client, project_id):
    """Labels are trimmed, duplicates are dropped and the order is kept."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Labelled",
            "project_id": project_id,
            "labels": ["  derstandard:1 ", "news", "derstandard:1", "news "],
        },
    )
    assert response.status_code == 201
    assert response.json()["labels"] == ["derstandard:1", "news"]


def test_empty_label_is_rejected(client, project_id):
    """A label that is blank after trimming gives a 422 error."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Bad",
            "project_id": project_id,
            "labels": ["news", "   "],
        },
    )
    assert response.status_code == 422


def test_update_replaces_labels(client, project_id):
    """PATCH with labels replaces the list, and leaves it alone when omitted."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Editable",
            "project_id": project_id,
            "labels": ["a"],
        },
    ).json()["id"]

    updated = client.patch(
        f"/api/v1/work-items/{item_id}", json={"labels": ["b", "c"]}
    ).json()
    assert updated["labels"] == ["b", "c"]

    untouched = client.patch(
        f"/api/v1/work-items/{item_id}", json={"title": "Renamed"}
    ).json()
    assert untouched["labels"] == ["b", "c"]


def test_rendered_description_renders_markdown(client, project_id):
    """GET returns the description rendered as sanitized HTML."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Markdown",
            "description": "**bold** and `code`",
            "project_id": project_id,
        },
    ).json()["id"]

    data = client.get(f"/api/v1/work-items/{item_id}").json()
    assert data["rendered_description"] == (
        "<p><strong>bold</strong> and <code>code</code></p>"
    )


def test_rendered_description_opens_links_in_new_tab(client, project_id):
    """Links in rendered_description open in a new tab, with rel set safely."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Link",
            "description": "[docs](https://example.com)",
            "project_id": project_id,
        },
    ).json()["id"]

    rendered = client.get(f"/api/v1/work-items/{item_id}").json()[
        "rendered_description"
    ]
    assert 'target="_blank"' in rendered
    assert 'rel="noopener noreferrer"' in rendered


def test_rendered_description_linkifies_bare_urls(client, project_id):
    """Bare URLs become links without swallowing trailing punctuation."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Bare",
            "description": "see https://example.com. and www.example.org",
            "project_id": project_id,
        },
    ).json()["id"]

    rendered = client.get(f"/api/v1/work-items/{item_id}").json()[
        "rendered_description"
    ]
    assert (
        '<a href="https://example.com" target="_blank" rel="noopener noreferrer">'
        "https://example.com</a>."
    ) in rendered
    assert (
        '<a href="http://www.example.org" target="_blank" rel="noopener noreferrer">'
        "www.example.org</a>"
    ) in rendered


def test_rendered_description_does_not_linkify_code_or_existing_links(
    client, project_id
):
    """URLs in code spans or already-linked text are not wrapped again."""
    item_id = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Code",
            "description": "`https://example.com` and [docs](https://example.com)",
            "project_id": project_id,
        },
    ).json()["id"]

    rendered = client.get(f"/api/v1/work-items/{item_id}").json()[
        "rendered_description"
    ]
    assert rendered.count("<a ") == 1
    assert "<code>https://example.com</code>" in rendered


def test_rendered_description_is_null_without_description(client, project_id):
    """rendered_description is null when there is no description."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "No description",
            "project_id": project_id,
        },
    )
    assert response.json()["rendered_description"] is None


def test_rendered_description_strips_unsafe_html(client, project_id):
    """Scripts and javascript: links are removed from rendered_description."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Unsafe",
            "description": "<script>alert(1)</script>\n\n[bad](javascript:alert(1))",
            "project_id": project_id,
        },
    )
    rendered = response.json()["rendered_description"]
    assert "<script" not in rendered
    assert "javascript:" not in rendered


def test_rendered_description_is_read_only(client, project_id):
    """rendered_description cannot be set by clients."""
    response = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Read only",
            "project_id": project_id,
            "rendered_description": "<p>forged</p>",
        },
    )
    assert response.status_code == 422


def test_new_work_item_starts_in_first_todo_status(client, project_id):
    data = _create(client, project_id).json()
    assert data["status_id"] == status_id(client, project_id, "open")
    assert data["parent_id"] is None


def test_old_string_status_and_type_are_rejected(client, project_id):
    """The old string fields are gone; unknown fields are not silently dropped."""
    response = client.post(
        "/api/v1/work-items",
        json={"type": "task", "title": "Old", "project_id": project_id},
    )
    assert response.status_code == 422


def test_create_with_status_of_other_project_returns_422(client, project_id):
    other = client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    response = _create(client, project_id, status_id=status_id(client, other, "open"))
    assert response.status_code == 422


def test_create_with_type_of_other_project_returns_422(client, project_id):
    other = client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    response = client.post(
        "/api/v1/work-items",
        json={
            "title": "X",
            "project_id": project_id,
            "type_id": type_id(client, other, "task"),
        },
    )
    assert response.status_code == 422


def test_status_change_follows_transitions(client, project_id):
    """With transitions defined, only listed moves are allowed (409 otherwise)."""
    open_id = status_id(client, project_id, "open")
    in_progress_id = status_id(client, project_id, "in_progress")
    done_id = status_id(client, project_id, "done")
    client.post(
        "/api/v1/status-transitions/",
        json={
            "project_id": project_id,
            "from_status_id": open_id,
            "to_status_id": in_progress_id,
        },
    )
    item_id = _create(client, project_id).json()["id"]

    blocked = client.patch(f"/api/v1/work-items/{item_id}", json={"status_id": done_id})
    assert blocked.status_code == 409
    allowed = client.patch(
        f"/api/v1/work-items/{item_id}", json={"status_id": in_progress_id}
    )
    assert allowed.status_code == 200


def test_move_to_other_project_defaults_status_and_type(client, project_id):
    other = client.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
    item_id = _create(client, project_id).json()["id"]

    bare = client.patch(f"/api/v1/work-items/{item_id}", json={"project_id": other})
    assert bare.status_code == 200
    assert bare.json()["project_id"] == other
    assert bare.json()["type_id"] == type_id(client, other, "task")
    assert bare.json()["status_id"] == status_id(client, other, "open")

    moved = client.patch(
        f"/api/v1/work-items/{item_id}",
        json={
            "project_id": other,
            "type_id": type_id(client, other, "task"),
            "status_id": status_id(client, other, "in_progress"),
        },
    )
    assert moved.status_code == 200
    assert moved.json()["project_id"] == other


def test_work_item_type_level_cannot_change_on_item(client, project_id):
    item_id = _create(client, project_id).json()["id"]
    response = client.patch(
        f"/api/v1/work-items/{item_id}",
        json={"type_id": type_id(client, project_id, "subtask")},
    )
    assert response.status_code == 409


def test_filter_by_status_name_category_and_type_level(client, project_id):
    _create(client, project_id, "Waiting")
    _create(
        client,
        project_id,
        "Started",
        status_id=status_id(client, project_id, "in_progress"),
    )
    for text in (
        "status == 'In Progress'",
        "status == 'in-progress'",
        f"status == '{status_id(client, project_id, 'in_progress')}'",
        "statusCategory == 'in_progress'",
    ):
        data = client.get("/api/v1/work-items", params={"filter": text}).json()
        assert [i["title"] for i in data["results"]] == ["Started"], text
    data = client.get(
        "/api/v1/work-items", params={"filter": "typeLevel == 'standard'"}
    ).json()
    assert data["total"] == 2


def test_work_item_includes_status_and_type_names(client, project_id):
    """A work item carries its status and type, so clients need no extra lookup."""
    data = _create(client, project_id).json()
    assert data["status"] == {
        "id": status_id(client, project_id, "open"),
        "name": "Open",
        "category": "todo",
    }
    assert data["type"] == {
        "id": type_id(client, project_id, "task"),
        "name": "Task",
        "level": "standard",
    }
    assert data["status_id"] == data["status"]["id"]
    assert data["type_id"] == data["type"]["id"]


def test_names_are_present_on_every_read_and_write(client, project_id):
    """Get, list, filtered list, patch and put all return the embedded names."""
    item_id = _create(client, project_id).json()["id"]
    in_progress = status_id(client, project_id, "in_progress")

    patched = client.patch(
        f"/api/v1/work-items/{item_id}", json={"status_id": in_progress}
    ).json()
    assert patched["status"]["name"] == "In Progress"
    assert patched["status"]["category"] == "in_progress"

    fetched = client.get(f"/api/v1/work-items/{item_id}").json()
    assert fetched["status"]["name"] == "In Progress"

    listed = client.get("/api/v1/work-items").json()["results"][0]
    assert listed["type"]["name"] == "Task"

    filtered = client.get(
        "/api/v1/work-items", params={"filter": "status == 'in-progress'"}
    ).json()["results"][0]
    assert filtered["status"]["name"] == "In Progress"

    replaced = client.put(
        f"/api/v1/work-items/{item_id}",
        json={
            "title": "New",
            "project_id": project_id,
            "type_id": type_id(client, project_id, "task"),
        },
    ).json()
    assert replaced["status"]["name"] == "Open"


def test_renamed_status_shows_new_name_on_work_items(client, project_id):
    """Names are looked up when read, so a rename shows up on existing items."""
    item_id = _create(client, project_id).json()["id"]
    client.patch(
        f"/api/v1/statuses/{status_id(client, project_id, 'open')}",
        json={"name": "Backlog"},
    )
    assert (
        client.get(f"/api/v1/work-items/{item_id}").json()["status"]["name"]
        == "Backlog"
    )


def test_subtask_names_show_subtask_level(client, project_id):
    parent_id = _create(client, project_id, "Parent").json()["id"]
    child = client.post(
        "/api/v1/work-items",
        json={
            "title": "Child",
            "project_id": project_id,
            "type_id": type_id(client, project_id, "subtask"),
            "parent_id": parent_id,
        },
    ).json()
    assert child["type"]["level"] == "subtask"
    assert child["parent_id"] == parent_id
