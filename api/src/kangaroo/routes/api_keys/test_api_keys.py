from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.routes.auth import require_user
from kangaroo.routes.dependencies import get_engine

OWNER = {"sub": "user-1", "email": "test@example.com", "name": "test-user"}
OTHER_USER = {"sub": "user-2", "email": "other@example.com", "name": "other"}


@pytest.fixture
def client(engine):
    """A TestClient with a fresh database, logged in as OWNER."""
    app.dependency_overrides[get_engine] = lambda: engine
    app.dependency_overrides[require_user] = lambda: dict(OWNER)
    yield TestClient(app)
    app.dependency_overrides.clear()


def act_as(user: dict) -> None:
    app.dependency_overrides[require_user] = lambda: dict(user)


def create_key(client, name="ci", expires_at=None):
    body = {"name": name}
    if expires_at is not None:
        body["expires_at"] = expires_at.isoformat()
    response = client.post("/api/v1/api-keys/", json=body)
    assert response.status_code == 201
    return response.json()


def test_create_returns_key_with_secret(client):
    created = create_key(client)

    assert created["key"].startswith("kg_")
    assert created["name"] == "ci"
    assert created["last_used_at"] is None
    assert created["expires_at"] is None


def test_list_hides_secret(client):
    created = create_key(client)

    listed = client.get("/api/v1/api-keys/").json()
    assert [item["id"] for item in listed] == [created["id"]]
    assert "key" not in listed[0]


def test_list_only_shows_own_keys(client):
    create_key(client)
    act_as(OTHER_USER)

    assert client.get("/api/v1/api-keys/").json() == []


def test_revoke_removes_key_from_list(client):
    created = create_key(client)

    response = client.delete(f"/api/v1/api-keys/{created['id']}")
    assert response.status_code == 204
    assert client.get("/api/v1/api-keys/").json() == []


def test_revoke_unknown_key_returns_404(client):
    response = client.delete(f"/api/v1/api-keys/{uuid4()}")
    assert response.status_code == 404


def test_cannot_revoke_another_users_key(client):
    created = create_key(client)
    act_as(OTHER_USER)

    response = client.delete(f"/api/v1/api-keys/{created['id']}")
    assert response.status_code == 404

    act_as(OWNER)
    assert len(client.get("/api/v1/api-keys/").json()) == 1


def test_create_rejects_past_expiry(client):
    past = datetime.now(UTC) - timedelta(days=1)

    response = client.post(
        "/api/v1/api-keys/", json={"name": "old", "expires_at": past.isoformat()}
    )
    assert response.status_code == 422


def test_create_rejects_blank_name(client):
    response = client.post("/api/v1/api-keys/", json={"name": ""})
    assert response.status_code == 422


def test_api_key_cannot_manage_api_keys(client):
    key = create_key(client)["key"]
    app.dependency_overrides.pop(require_user, None)
    headers = {"Authorization": f"Bearer {key}"}

    assert client.get("/api/v1/api-keys/", headers=headers).status_code == 403
    assert (
        client.post(
            "/api/v1/api-keys/", json={"name": "x"}, headers=headers
        ).status_code
        == 403
    )
