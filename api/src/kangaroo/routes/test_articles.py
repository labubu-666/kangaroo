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
    body = {"title": "Setup", "body": "# Setup", **overrides}
    return client.post("/api/v1/articles", json=body)


def test_create_article(client):
    """POST /api/v1/articles saves an article."""
    response = create(client, labels=["howto"])
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Setup"
    assert data["body"] == "# Setup"
    assert data["labels"] == ["howto"]
    assert "created_at" in data


def test_create_article_missing_title(client):
    """POST /api/v1/articles without a title returns validation error."""
    response = client.post("/api/v1/articles", json={"body": "text"})
    assert response.status_code == 422


def test_get_article_renders_markdown(client):
    """GET /api/v1/articles/{id} returns the body and its sanitized HTML."""
    created = create(client, body="# Hi\n\n<script>bad()</script>").json()
    response = client.get(f"/api/v1/articles/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == "# Hi\n\n<script>bad()</script>"
    assert "<h1>Hi</h1>" in data["html"]
    assert "<script>" not in data["html"]


def test_get_missing_article(client):
    """GET /api/v1/articles/{id} returns 404 for an unknown ID."""
    response = client.get("/api/v1/articles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_articles_with_search(client):
    """GET /api/v1/articles?search= matches title or body."""
    create(client, title="Alpha")
    create(client, title="Beta", body="mentions alphabet")
    create(client, title="Gamma", body="nothing")
    response = client.get("/api/v1/articles", params={"search": "alpha"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_articles_paginates(client):
    """GET /api/v1/articles returns one page and the total."""
    for index in range(3):
        create(client, title=f"Article {index}")
    response = client.get("/api/v1/articles", params={"limit": 2, "offset": 2})
    data = response.json()
    assert data["total"] == 3
    assert len(data["results"]) == 1


def test_replace_article(client):
    """PUT /api/v1/articles/{id} replaces the article and keeps its ID."""
    created = create(client, labels=["old"]).json()
    response = client.put(
        f"/api/v1/articles/{created['id']}",
        json={"title": "New", "body": "New body"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["title"] == "New"
    assert data["labels"] == []


def test_update_article(client):
    """PATCH /api/v1/articles/{id} changes only the fields it sends."""
    created = create(client).json()
    response = client.patch(
        f"/api/v1/articles/{created['id']}", json={"body": "Changed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Setup"
    assert data["body"] == "Changed"


def test_update_article_rejects_null_title(client):
    """PATCH /api/v1/articles/{id} refuses a null title."""
    created = create(client).json()
    response = client.patch(f"/api/v1/articles/{created['id']}", json={"title": None})
    assert response.status_code == 422


def test_delete_article(client):
    """DELETE /api/v1/articles/{id} removes the article."""
    created = create(client).json()
    assert client.delete(f"/api/v1/articles/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/articles/{created['id']}").status_code == 404
