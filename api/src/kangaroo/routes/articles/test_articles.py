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


@pytest.fixture
def knowledge_base_id(client):
    """Create a knowledge base for the tests to put their articles in."""
    return client.post("/api/v1/knowledge-bases", json={"name": "Docs"}).json()["id"]


def create(client, knowledge_base_id, **overrides):
    body = {
        "knowledge_base_id": knowledge_base_id,
        "title": "Setup",
        "body": "# Setup",
        **overrides,
    }
    return client.post("/api/v1/articles", json=body)


def test_create_article(client, knowledge_base_id):
    """POST /api/v1/articles saves an article in its knowledge base."""
    response = create(client, knowledge_base_id, labels=["howto"])
    assert response.status_code == 201
    data = response.json()
    assert data["knowledge_base_id"] == knowledge_base_id
    assert data["title"] == "Setup"
    assert data["body"] == "# Setup"
    assert data["labels"] == ["howto"]
    assert "created_at" in data


def test_create_article_missing_title(client, knowledge_base_id):
    """POST /api/v1/articles without a title returns validation error."""
    response = client.post(
        "/api/v1/articles",
        json={"knowledge_base_id": knowledge_base_id, "body": "text"},
    )
    assert response.status_code == 422


def test_create_article_unknown_knowledge_base(client):
    """POST /api/v1/articles returns 422 for a knowledge base that does not exist."""
    response = create(client, "00000000-0000-0000-0000-000000000000")
    assert response.status_code == 422
    assert response.json()["detail"] == "Knowledge base not found"


def test_get_article_renders_markdown(client, knowledge_base_id):
    """GET /api/v1/articles/{id} returns the body and its sanitized HTML."""
    created = create(
        client, knowledge_base_id, body="# Hi\n\n<script>bad()</script>"
    ).json()
    response = client.get(f"/api/v1/articles/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == "# Hi\n\n<script>bad()</script>"
    assert "<h1>Hi</h1>" in data["html"]
    assert "<script>" not in data["html"]


def test_get_article_records_view(client, knowledge_base_id):
    """GET /api/v1/articles/{id} sets viewed_at without changing modified_at."""
    created = create(client, knowledge_base_id).json()
    assert created["viewed_at"] is None

    response = client.get(f"/api/v1/articles/{created['id']}")
    data = response.json()
    assert data["viewed_at"] is not None
    assert data["modified_at"] == created["modified_at"]


def test_get_missing_article(client):
    """GET /api/v1/articles/{id} returns 404 for an unknown ID."""
    response = client.get("/api/v1/articles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_articles_with_search(client, knowledge_base_id):
    """GET /api/v1/articles?search= matches title or body."""
    create(client, knowledge_base_id, title="Alpha")
    create(client, knowledge_base_id, title="Beta", body="mentions alphabet")
    create(client, knowledge_base_id, title="Gamma", body="nothing")
    response = client.get("/api/v1/articles", params={"search": "alpha"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_list_articles_filters_by_knowledge_base(client, knowledge_base_id):
    """GET /api/v1/articles?knowledge_base_id= lists only that base's articles."""
    other = client.post("/api/v1/knowledge-bases", json={"name": "Other"}).json()
    create(client, knowledge_base_id, title="Mine")
    create(client, other["id"], title="Theirs")
    response = client.get(
        "/api/v1/articles", params={"knowledge_base_id": knowledge_base_id}
    )
    titles = [item["title"] for item in response.json()["results"]]
    assert titles == ["Mine"]


def test_list_articles_paginates(client, knowledge_base_id):
    """GET /api/v1/articles returns one page and the total."""
    for index in range(3):
        create(client, knowledge_base_id, title=f"Article {index}")
    response = client.get("/api/v1/articles", params={"limit": 2, "offset": 2})
    data = response.json()
    assert data["total"] == 3
    assert len(data["results"]) == 1


def titles(response):
    return [item["title"] for item in response.json()["results"]]


def test_list_articles_sorts_ascending_by_default(client, knowledge_base_id):
    """GET /api/v1/articles?sort=title sorts A to Z, and +title does the same."""
    for title in ["Beta", "Alpha", "Gamma"]:
        create(client, knowledge_base_id, title=title)
    for sort in ["title", "+title"]:
        response = client.get("/api/v1/articles", params={"sort": sort})
        assert response.status_code == 200
        assert titles(response) == ["Alpha", "Beta", "Gamma"]


def test_list_articles_sorts_descending(client, knowledge_base_id):
    """GET /api/v1/articles?sort=-title sorts Z to A."""
    for title in ["Beta", "Alpha", "Gamma"]:
        create(client, knowledge_base_id, title=title)
    response = client.get("/api/v1/articles", params={"sort": "-title"})
    assert titles(response) == ["Gamma", "Beta", "Alpha"]


def test_list_articles_sorts_by_modified_at(client, knowledge_base_id):
    """GET /api/v1/articles?sort=-modified_at puts the last edited article first."""
    first = create(client, knowledge_base_id, title="First").json()
    create(client, knowledge_base_id, title="Second")
    client.patch(f"/api/v1/articles/{first['id']}", json={"body": "Edited"})
    response = client.get("/api/v1/articles", params={"sort": "-modified_at"})
    assert titles(response) == ["First", "Second"]


def test_list_articles_rejects_unknown_sort_field(client, knowledge_base_id):
    """GET /api/v1/articles returns 422 for a sort field it does not know."""
    response = client.get("/api/v1/articles", params={"sort": "-nope"})
    assert response.status_code == 422
    assert "nope" in response.json()["detail"]


def test_replace_article(client, knowledge_base_id):
    """PUT /api/v1/articles/{id} replaces the article and keeps its ID."""
    created = create(client, knowledge_base_id, labels=["old"]).json()
    response = client.put(
        f"/api/v1/articles/{created['id']}",
        json={
            "knowledge_base_id": knowledge_base_id,
            "title": "New",
            "body": "New body",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["title"] == "New"
    assert data["labels"] == []


def test_update_article(client, knowledge_base_id):
    """PATCH /api/v1/articles/{id} changes only the fields it sends."""
    created = create(client, knowledge_base_id).json()
    response = client.patch(
        f"/api/v1/articles/{created['id']}", json={"body": "Changed"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Setup"
    assert data["body"] == "Changed"


def test_move_article_to_another_knowledge_base(client, knowledge_base_id):
    """PATCH /api/v1/articles/{id} can move an article to another knowledge base."""
    other = client.post("/api/v1/knowledge-bases", json={"name": "Other"}).json()
    created = create(client, knowledge_base_id).json()
    response = client.patch(
        f"/api/v1/articles/{created['id']}",
        json={"knowledge_base_id": other["id"]},
    )
    assert response.status_code == 200
    assert response.json()["knowledge_base_id"] == other["id"]


def test_update_article_rejects_null_title(client, knowledge_base_id):
    """PATCH /api/v1/articles/{id} refuses a null title."""
    created = create(client, knowledge_base_id).json()
    response = client.patch(f"/api/v1/articles/{created['id']}", json={"title": None})
    assert response.status_code == 422


def test_delete_article(client, knowledge_base_id):
    """DELETE /api/v1/articles/{id} removes the article."""
    created = create(client, knowledge_base_id).json()
    assert client.delete(f"/api/v1/articles/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/articles/{created['id']}").status_code == 404
