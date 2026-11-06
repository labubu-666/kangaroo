import pytest


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


def test_create_article_without_body(client, knowledge_base_id):
    """POST /api/v1/articles without a body stores a null body."""
    response = client.post(
        "/api/v1/articles",
        json={"knowledge_base_id": knowledge_base_id, "title": "Empty"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["body"] is None


def test_get_article_without_body_has_null_html(client, knowledge_base_id):
    """GET /api/v1/articles/{id} returns null html when the article has no body."""
    created = client.post(
        "/api/v1/articles",
        json={"knowledge_base_id": knowledge_base_id, "title": "Empty"},
    ).json()
    data = client.get(f"/api/v1/articles/{created['id']}").json()
    assert data["body"] is None
    assert data["html"] is None


def test_update_article_clears_body(client, knowledge_base_id):
    """PATCH with a null body clears it, as the work item description does."""
    created = create(client, knowledge_base_id).json()
    response = client.patch(f"/api/v1/articles/{created['id']}", json={"body": None})
    assert response.status_code == 200
    assert response.json()["body"] is None


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


def test_search_matches_plain_body_not_markdown_syntax(client, knowledge_base_id):
    """Article search matches rendered text, so Markdown markup is not searchable."""
    create(client, knowledge_base_id, title="A", body="**Setup** steps")

    assert client.get("/api/v1/articles?search=setup").json()["total"] == 1
    assert client.get("/api/v1/articles?search=**Setup**").json()["total"] == 0


def test_article_search_result_has_snippet(client, knowledge_base_id):
    """A body match comes back with a snippet and the match count."""
    create(client, knowledge_base_id, title="Guide", body="Install it. Install again.")

    results = client.get("/api/v1/articles?search=install").json()["results"]

    assert results[0]["snippet"] == {
        "text": "Install it. Install again.",
        "match_count": 2,
    }


def test_article_title_match_has_no_snippet(client, knowledge_base_id):
    """A match only in the title has no snippet."""
    create(client, knowledge_base_id, title="Install", body="unrelated")

    results = client.get("/api/v1/articles?search=install").json()["results"]

    assert results[0]["snippet"] is None


def test_plain_body_follows_updates(client, knowledge_base_id):
    """Updating the body changes what search matches."""
    created = create(client, knowledge_base_id, body="old").json()

    client.patch(f"/api/v1/articles/{created['id']}", json={"body": "fresh"})

    assert client.get("/api/v1/articles?search=fresh").json()["total"] == 1
    assert client.get("/api/v1/articles?search=old").json()["total"] == 0


def test_sort_by_internal_field_is_rejected(client, knowledge_base_id):
    """Internal fields such as plain_body cannot be used to sort."""
    create(client, knowledge_base_id)
    assert client.get("/api/v1/articles?sort=plain_body").status_code == 422
    assert client.get("/api/v1/articles?sort=snippet").status_code == 422


def test_padded_search_still_gets_a_snippet(client, knowledge_base_id):
    """Spaces around the search term do not stop a snippet from being returned."""
    create(client, knowledge_base_id, title="G", body="Install it")

    results = client.get("/api/v1/articles?search=%20install%20").json()["results"]

    assert results[0]["snippet"]["match_count"] == 1


def test_snippet_is_only_in_article_list(client, knowledge_base_id):
    """The snippet appears in list results only, never on a single article."""
    created = create(client, knowledge_base_id, title="G", body="Install it").json()

    assert "snippet" not in created
    assert "snippet" not in client.get(f"/api/v1/articles/{created['id']}").json()
    listed = client.get("/api/v1/articles?search=install").json()["results"][0]
    assert listed["snippet"]["match_count"] == 1
    assert client.get("/api/v1/articles").json()["results"][0]["snippet"] is None
