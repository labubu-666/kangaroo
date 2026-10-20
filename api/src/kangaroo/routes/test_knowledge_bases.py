import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.routes.dependencies import get_engine


@pytest.fixture
def client(engine):
    """Provide a TestClient that uses fresh database for each test."""
    app.dependency_overrides[get_engine] = lambda: engine
    yield TestClient(app)
    app.dependency_overrides.clear()


def create(client, **overrides):
    body = {"name": "Docs", **overrides}
    return client.post("/api/v1/knowledge-bases", json=body)


def test_create_knowledge_base(client):
    """POST /api/v1/knowledge-bases creates a knowledge base."""
    response = create(client, description="Team docs", labels=["internal"])
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Docs"
    assert data["description"] == "Team docs"
    assert data["labels"] == ["internal"]
    assert "created_at" in data


def test_create_knowledge_base_missing_name(client):
    """POST /api/v1/knowledge-bases without a name returns validation error."""
    response = client.post("/api/v1/knowledge-bases", json={})
    assert response.status_code == 422


def test_get_knowledge_base(client):
    """GET /api/v1/knowledge-bases/{id} returns the knowledge base."""
    created = create(client).json()
    response = client.get(f"/api/v1/knowledge-bases/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Docs"


def test_get_missing_knowledge_base(client):
    """GET /api/v1/knowledge-bases/{id} returns 404 for an unknown ID."""
    response = client.get(
        "/api/v1/knowledge-bases/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404


def test_list_knowledge_bases_with_search(client):
    """GET /api/v1/knowledge-bases?search= matches name or description."""
    create(client, name="Alpha")
    create(client, name="Beta", description="about alphabet")
    create(client, name="Gamma")
    response = client.get("/api/v1/knowledge-bases", params={"search": "alpha"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_replace_knowledge_base(client):
    """PUT /api/v1/knowledge-bases/{id} replaces it and keeps its ID."""
    created = create(client, labels=["old"]).json()
    response = client.put(
        f"/api/v1/knowledge-bases/{created['id']}", json={"name": "New"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["name"] == "New"
    assert data["labels"] == []


def test_update_knowledge_base(client):
    """PATCH /api/v1/knowledge-bases/{id} changes only the fields it sends."""
    created = create(client).json()
    response = client.patch(
        f"/api/v1/knowledge-bases/{created['id']}", json={"description": "Notes"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Docs"
    assert data["description"] == "Notes"


def test_update_knowledge_base_rejects_null_name(client):
    """PATCH /api/v1/knowledge-bases/{id} refuses a null name."""
    created = create(client).json()
    response = client.patch(
        f"/api/v1/knowledge-bases/{created['id']}", json={"name": None}
    )
    assert response.status_code == 422


def test_delete_knowledge_base(client):
    """DELETE /api/v1/knowledge-bases/{id} deletes an empty knowledge base."""
    created = create(client).json()
    assert client.delete(f"/api/v1/knowledge-bases/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/knowledge-bases/{created['id']}").status_code == 404


def test_delete_knowledge_base_with_articles_forbidden(client):
    """DELETE /api/v1/knowledge-bases/{id} returns 409 while it has articles."""
    kb_id = create(client).json()["id"]
    client.post(
        "/api/v1/articles",
        json={"knowledge_base_id": kb_id, "title": "A", "body": "text"},
    )
    response = client.delete(f"/api/v1/knowledge-bases/{kb_id}")
    assert response.status_code == 409
    assert client.get(f"/api/v1/knowledge-bases/{kb_id}").status_code == 200
