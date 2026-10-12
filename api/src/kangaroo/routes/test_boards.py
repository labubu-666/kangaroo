from uuid import UUID

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
from kangaroo.testing import status_id, type_id


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
    """Create a project for the tests to put their work items in."""
    return client.post("/api/v1/projects", json={"name": "Test"}).json()["id"]


def test_create_board(client, project_id):
    """POST /api/v1/boards creates a board."""
    response = client.post(
        "/api/v1/boards",
        json={
            "name": "Foo",
            "description": "Board",
            "filter": "project.name == 'foo'",
            "project_id": project_id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert isinstance(UUID(data["id"]), UUID)
    assert data["name"] == "Foo"
    assert data["filter"] == "project.name == 'foo'"
    assert "created_at" in data


def test_create_board_invalid_filter(client, project_id):
    """POST /api/v1/boards with a bad filter returns 422."""
    response = client.post(
        "/api/v1/boards",
        json={
            "name": "Bad",
            "filter": "project.name = 'foo'",
            "project_id": project_id,
        },
    )
    assert response.status_code == 422


def test_create_board_missing_name(client):
    response = client.post("/api/v1/boards", json={"filter": None})
    assert response.status_code == 422


def test_list_boards(client, project_id):
    client.post("/api/v1/boards", json={"name": "Alpha", "project_id": project_id})
    response = client.get("/api/v1/boards?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["results"][0]["name"] == "Alpha"


def test_list_boards_search(client, project_id):
    """GET /api/v1/boards?search= matches name or description."""
    client.post(
        "/api/v1/boards",
        json={"name": "Sprint board", "project_id": project_id},
    )
    client.post(
        "/api/v1/boards",
        json={
            "name": "Other",
            "description": "sprint",
            "project_id": project_id,
        },
    )
    client.post(
        "/api/v1/boards",
        json={"name": "Unrelated", "project_id": project_id},
    )

    data = client.get("/api/v1/boards?search=sprint").json()
    assert data["total"] == 2
    assert [board["name"] for board in data["results"]] == ["Sprint board", "Other"]


def test_get_board_not_found(client):
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    assert client.get(f"/api/v1/boards/{fake_uuid}").status_code == 404


def test_update_board_filter(client, project_id):
    board_id = client.post(
        "/api/v1/boards", json={"name": "Alpha", "project_id": project_id}
    ).json()["id"]
    response = client.patch(
        f"/api/v1/boards/{board_id}", json={"filter": "status == 'done'"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Alpha"
    assert response.json()["filter"] == "status == 'done'"

    bad = client.patch(f"/api/v1/boards/{board_id}", json={"filter": "status ="})
    assert bad.status_code == 422


def test_update_board_name_null_returns_422(client, project_id):
    board_id = client.post(
        "/api/v1/boards", json={"name": "Keep", "project_id": project_id}
    ).json()["id"]

    response = client.patch(f"/api/v1/boards/{board_id}", json={"name": None})
    assert response.status_code == 422
    assert client.get(f"/api/v1/boards/{board_id}").json()["name"] == "Keep"


def test_replace_board(client, project_id):
    board_id = client.post(
        "/api/v1/boards",
        json={
            "name": "Old",
            "filter": "type == 'task'",
            "project_id": project_id,
        },
    ).json()["id"]
    response = client.put(
        f"/api/v1/boards/{board_id}",
        json={"name": "New", "project_id": project_id},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"
    assert response.json()["filter"] is None


def test_delete_board(client, project_id):
    board_id = client.post(
        "/api/v1/boards", json={"name": "Temp", "project_id": project_id}
    ).json()["id"]
    assert client.delete(f"/api/v1/boards/{board_id}").status_code == 204
    assert client.get(f"/api/v1/boards/{board_id}").status_code == 404


def test_view_groups_matching_items_by_status(client, project_id):
    """The view shows only items matching the filter, grouped into status columns."""
    project_id = client.post("/api/v1/projects", json={"name": "foo"}).json()["id"]
    other_id = client.post("/api/v1/projects", json={"name": "bar"}).json()["id"]
    first = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "In foo",
            "project_id": project_id,
        },
    ).json()
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "In bar",
            "project_id": other_id,
        },
    )
    client.patch(
        f"/api/v1/work-items/{first['id']}",
        json={"status_id": status_id(client, project_id, "done")},
    )
    board_id = client.post(
        "/api/v1/boards",
        json={
            "name": "Foo board",
            "filter": "project.name == 'foo'",
            "project_id": project_id,
        },
    ).json()["id"]

    response = client.get(f"/api/v1/boards/{board_id}/view")
    assert response.status_code == 200
    data = response.json()
    assert data["board"]["id"] == board_id
    assert [column["status"]["name"] for column in data["columns"]] == [
        "Open",
        "In Progress",
        "Done",
    ]
    assert data["columns"][0]["items"] == []
    assert [item["title"] for item in data["columns"][2]["items"]] == ["In foo"]


def test_board_filter_on_labels(client, project_id):
    """A board filtered on labels shows only the work items with that label."""
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Article",
            "project_id": project_id,
            "labels": ["derstandard", "derstandard:1"],
        },
    )
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Other",
            "project_id": project_id,
        },
    )
    board_id = client.post(
        "/api/v1/boards",
        json={
            "name": "Labels only",
            "filter": "labels contains 'derstandard'",
            "project_id": project_id,
        },
    ).json()["id"]

    data = client.get(f"/api/v1/boards/{board_id}/view").json()
    titles = [item["title"] for column in data["columns"] for item in column["items"]]
    assert titles == ["Article"]


def test_view_with_blank_filter_shows_everything(client, project_id):
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Anywhere",
            "project_id": project_id,
        },
    )
    board_id = client.post(
        "/api/v1/boards", json={"name": "All", "project_id": project_id}
    ).json()["id"]
    columns = client.get(f"/api/v1/boards/{board_id}/view").json()["columns"]
    assert [item["title"] for item in columns[0]["items"]] == ["Anywhere"]


def test_view_board_not_found(client):
    fake_uuid = "11111111-1111-1111-1111-111111111111"
    assert client.get(f"/api/v1/boards/{fake_uuid}/view").status_code == 404


def test_create_board_requires_project(client):
    """A board must name its project (422 without it)."""
    response = client.post("/api/v1/boards", json={"name": "Orphan"})
    assert response.status_code == 422


def test_create_board_unknown_project_returns_422(client, project_id):
    """A board must reference an existing project."""
    response = client.post(
        "/api/v1/boards",
        json={"name": "Lost", "project_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 422


def test_list_boards_filtered_by_project(client, project_id):
    """GET /api/v1/boards?project_id= returns only that project's boards."""
    alpha_id = client.post("/api/v1/projects", json={"name": "Alpha"}).json()["id"]
    client.post("/api/v1/boards", json={"name": "In alpha", "project_id": alpha_id})
    client.post(
        "/api/v1/boards",
        json={"name": "In default", "project_id": project_id},
    )

    data = client.get(f"/api/v1/boards?project_id={alpha_id}").json()
    assert [board["name"] for board in data["results"]] == ["In alpha"]


def test_list_boards_filter_by_project(client, project_id):
    """GET /api/v1/boards?filter=project.id == ... returns only that project's boards."""
    alpha_id = client.post("/api/v1/projects", json={"name": "Alpha"}).json()["id"]
    client.post("/api/v1/boards", json={"name": "In alpha", "project_id": alpha_id})
    client.post(
        "/api/v1/boards",
        json={"name": "In default", "project_id": project_id},
    )

    data = client.get(
        "/api/v1/boards", params={"filter": f"project.id == '{alpha_id}'"}
    ).json()
    assert [board["name"] for board in data["results"]] == ["In alpha"]
    assert data["total"] == 1


def test_list_boards_invalid_filter(client):
    """GET /api/v1/boards with a bad filter returns 422."""
    response = client.get("/api/v1/boards", params={"filter": "project.id ="})
    assert response.status_code == 422


def test_move_board_to_other_project(client, project_id):
    """PATCH can move a board to another project, which must exist."""
    project_id = client.post("/api/v1/projects", json={"name": "Beta"}).json()["id"]
    board_id = client.post(
        "/api/v1/boards", json={"name": "Mover", "project_id": project_id}
    ).json()["id"]

    moved = client.patch(f"/api/v1/boards/{board_id}", json={"project_id": project_id})
    assert moved.status_code == 200
    assert moved.json()["project_id"] == project_id

    missing = client.patch(
        f"/api/v1/boards/{board_id}",
        json={"project_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert missing.status_code == 422


def test_view_only_shows_items_of_board_project(client, project_id):
    """A board without a filter shows only the work items of its own project."""
    gamma_id = client.post("/api/v1/projects", json={"name": "Gamma"}).json()["id"]
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, gamma_id, "task"),
            "title": "Gamma item",
            "project_id": gamma_id,
        },
    )
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Default item",
            "project_id": project_id,
        },
    )
    board_id = client.post(
        "/api/v1/boards", json={"name": "Gamma board", "project_id": gamma_id}
    ).json()["id"]

    columns = client.get(f"/api/v1/boards/{board_id}/view").json()["columns"]
    assert [item["title"] for item in columns[0]["items"]] == ["Gamma item"]


def test_board_labels_default_to_empty(client, project_id):
    """A board created without labels has an empty label list."""
    response = client.post(
        "/api/v1/boards", json={"name": "Plain", "project_id": project_id}
    )
    assert response.json()["labels"] == []


def test_create_board_with_labels(client, project_id):
    """POST /api/v1/boards stores labels, trimmed and without duplicates."""
    response = client.post(
        "/api/v1/boards",
        json={
            "name": "Tagged",
            "project_id": project_id,
            "labels": [" news ", "sport", "news"],
        },
    )
    assert response.status_code == 201
    assert response.json()["labels"] == ["news", "sport"]


def test_create_board_empty_label_returns_422(client, project_id):
    """POST /api/v1/boards rejects a blank label."""
    response = client.post(
        "/api/v1/boards",
        json={"name": "Bad", "project_id": project_id, "labels": [""]},
    )
    assert response.status_code == 422


def test_update_board_labels_keeps_other_fields(client, project_id):
    """PATCH /api/v1/boards/{id} changes labels and keeps the rest."""
    board_id = client.post(
        "/api/v1/boards",
        json={"name": "Keep", "project_id": project_id, "labels": ["old"]},
    ).json()["id"]

    response = client.patch(f"/api/v1/boards/{board_id}", json={"labels": ["new"]})
    assert response.status_code == 200
    assert response.json()["labels"] == ["new"]
    assert response.json()["name"] == "Keep"


def test_patch_board_without_labels_keeps_labels(client, project_id):
    """PATCH without labels leaves the existing labels alone."""
    board_id = client.post(
        "/api/v1/boards",
        json={"name": "Keep", "project_id": project_id, "labels": ["kept"]},
    ).json()["id"]

    response = client.patch(f"/api/v1/boards/{board_id}", json={"name": "New"})
    assert response.json()["labels"] == ["kept"]


def test_replace_board_labels(client, project_id):
    """PUT /api/v1/boards/{id} replaces labels; omitting them clears the list."""
    board_id = client.post(
        "/api/v1/boards",
        json={"name": "Old", "project_id": project_id, "labels": ["old"]},
    ).json()["id"]

    replaced = client.put(
        f"/api/v1/boards/{board_id}",
        json={"name": "New", "project_id": project_id, "labels": ["fresh"]},
    )
    assert replaced.json()["labels"] == ["fresh"]

    cleared = client.put(
        f"/api/v1/boards/{board_id}", json={"name": "New", "project_id": project_id}
    )
    assert cleared.json()["labels"] == []


def test_view_has_a_column_for_every_status_including_empty(client, project_id):
    """Every status of the project is a column, even one with no work items."""
    client.post(
        "/api/v1/statuses/",
        json={"project_id": project_id, "name": "Review", "category": "in_progress"},
    )
    board_id = client.post(
        "/api/v1/boards", json={"name": "Board", "project_id": project_id}
    ).json()["id"]

    columns = client.get(f"/api/v1/boards/{board_id}/view").json()["columns"]
    assert [c["status"]["name"] for c in columns] == [
        "Open",
        "In Progress",
        "Done",
        "Review",
    ]
    assert all(c["items"] == [] for c in columns)


def test_view_columns_follow_status_position(client, project_id):
    """Columns are ordered by the statuses' positions."""
    statuses = client.get(f"/api/v1/statuses/?project_id={project_id}").json()
    done = next(s for s in statuses if s["name"] == "Done")
    client.patch(f"/api/v1/statuses/{done['id']}", json={"position": -1})
    board_id = client.post(
        "/api/v1/boards", json={"name": "Board", "project_id": project_id}
    ).json()["id"]

    columns = client.get(f"/api/v1/boards/{board_id}/view").json()["columns"]
    assert columns[0]["status"]["name"] == "Done"


def test_view_filter_by_status_name_and_category(client, project_id):
    """A board filter can use the status name or its category."""
    first = client.post(
        "/api/v1/work-items",
        json={
            "title": "Started",
            "project_id": project_id,
            "type_id": type_id(client, project_id, "task"),
            "status_id": status_id(client, project_id, "in_progress"),
        },
    )
    assert first.status_code == 201
    client.post(
        "/api/v1/work-items",
        json={
            "title": "Waiting",
            "project_id": project_id,
            "type_id": type_id(client, project_id, "task"),
        },
    )
    for text in ("status == 'in-progress'", "statusCategory == 'in_progress'"):
        board_id = client.post(
            "/api/v1/boards",
            json={"name": "B", "project_id": project_id, "filter": text},
        ).json()["id"]
        columns = client.get(f"/api/v1/boards/{board_id}/view").json()["columns"]
        titles = [i["title"] for c in columns for i in c["items"]]
        assert titles == ["Started"], text


def test_view_items_carry_status_and_type_names(client, project_id):
    client.post(
        "/api/v1/work-items",
        json={
            "title": "Item",
            "project_id": project_id,
            "type_id": type_id(client, project_id, "task"),
        },
    )
    board_id = client.post(
        "/api/v1/boards", json={"name": "Board", "project_id": project_id}
    ).json()["id"]
    columns = client.get(f"/api/v1/boards/{board_id}/view").json()["columns"]
    item = columns[0]["items"][0]
    assert item["status"]["name"] == "Open"
    assert item["type"]["name"] == "Task"
