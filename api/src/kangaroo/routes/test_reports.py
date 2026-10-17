import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.routes.dependencies import get_backends
from kangaroo.testing import status_id, type_id


@pytest.fixture
def client(backends):
    """Provide a TestClient that uses fresh backends for each test."""
    app.dependency_overrides[get_backends] = lambda: backends
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def project_id(client):
    """Create a project for the tests to put their work items in."""
    return client.post("/api/v1/projects", json={"name": "Test"}).json()["id"]


def test_summary_empty_store(client):
    """With no data, every count is zero."""
    response = client.get("/api/v1/reports/summary")
    assert response.status_code == 200
    assert response.json() == {
        "projects": 0,
        "boards": 0,
        "work_items": {
            "total": 0,
            "todo": 0,
            "in_progress": 0,
            "done": 0,
            "by_status": [],
        },
    }


def test_summary_excludes_trashed_work_items(client, project_id):
    """Trashed work items are not counted on the dashboard."""
    live = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Live",
            "project_id": project_id,
        },
    ).json()
    trashed = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Gone",
            "project_id": project_id,
        },
    ).json()
    client.patch(f"/api/v1/work-items/{trashed['id']}", json={"trashed": True})
    client.patch(
        f"/api/v1/work-items/{live['id']}",
        json={"status_id": status_id(client, project_id, "in_progress")},
    )

    data = client.get("/api/v1/reports/summary").json()
    counts = data["work_items"]
    assert counts["total"] == 1
    assert (counts["todo"], counts["in_progress"], counts["done"]) == (0, 1, 0)


def test_summary_counts_by_status(client, project_id):
    """Counts reflect created projects, boards and work items per status."""
    project = client.post("/api/v1/projects", json={"name": "Alpha"}).json()
    client.post(
        "/api/v1/boards",
        json={"name": "Board", "project_id": project["id"]},
    )
    first = client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project["id"], "task"),
            "title": "One",
            "project_id": project["id"],
        },
    ).json()
    client.post(
        "/api/v1/work-items",
        json={
            "type_id": type_id(client, project_id, "task"),
            "title": "Two",
            "project_id": project_id,
        },
    )
    client.patch(
        f"/api/v1/work-items/{first['id']}",
        json={"status_id": status_id(client, project["id"], "done")},
    )

    data = client.get("/api/v1/reports/summary").json()
    assert data["projects"] == 2
    assert data["boards"] == 1
    counts = data["work_items"]
    assert counts["total"] == 2
    assert (counts["todo"], counts["in_progress"], counts["done"]) == (1, 0, 1)
    per_status = {
        entry["status"]["name"]: entry["count"]
        for entry in counts["by_status"]
        if entry["count"]
    }
    assert per_status == {"Open": 1, "Done": 1}


def test_summary_counts_by_category_across_custom_statuses(client, project_id):
    """Statuses named differently still count under their category."""
    review = client.post(
        "/api/v1/statuses/",
        json={"project_id": project_id, "name": "Review", "category": "in_progress"},
    ).json()
    for status in (review["id"], review["id"], status_id(client, project_id, "done")):
        client.post(
            "/api/v1/work-items",
            json={
                "title": "T",
                "project_id": project_id,
                "type_id": type_id(client, project_id, "task"),
                "status_id": status,
            },
        )

    counts = client.get("/api/v1/reports/summary").json()["work_items"]
    assert (counts["todo"], counts["in_progress"], counts["done"]) == (0, 2, 1)
    by_name = {e["status"]["name"]: e["count"] for e in counts["by_status"]}
    assert by_name == {"Open": 0, "In Progress": 0, "Done": 1, "Review": 2}
