import importlib
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from authlib.integrations.starlette_client import OAuthError
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import select

from kangaroo.app import app
from kangaroo.repositories import ApiKeyRepository
from kangaroo.repositories.tables import ApiKeyRow
from kangaroo.routes.auth import require_user
from kangaroo.routes.dependencies import get_engine
from kangaroo.services.api_keys import hash_api_key
from kangaroo.settings import settings

auth = importlib.import_module("kangaroo.routes.auth.router")


def fake_dex_login(monkeypatch, email="test@example.com"):
    async def fake_authorize_access_token(request):
        return {"userinfo": {"email": email, "name": "test-user"}}

    monkeypatch.setattr(
        auth.oauth.dex, "authorize_access_token", fake_authorize_access_token
    )


def test_login_redirects_to_dex(monkeypatch):
    async def fake_authorize_redirect(request, redirect_uri):
        assert redirect_uri == settings.oidc_redirect_uri
        return RedirectResponse(url="http://localhost:5556/dex/auth")

    monkeypatch.setattr(auth.oauth.dex, "authorize_redirect", fake_authorize_redirect)

    client = TestClient(app)
    response = client.get("/auth/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].startswith("http://localhost:5556/dex/auth")


def test_login_returns_503_when_dex_is_unreachable(monkeypatch):
    async def fake_authorize_redirect(request, redirect_uri):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(auth.oauth.dex, "authorize_redirect", fake_authorize_redirect)

    client = TestClient(app)
    response = client.get("/auth/login")
    assert response.status_code == 503
    assert response.json() == {"detail": "Login provider unavailable"}


@pytest.mark.parametrize("next_path", ["/web/projects/1", "/web/boards?view=list#top"])
def test_login_returns_to_next_path_after_callback(monkeypatch, next_path):
    async def fake_authorize_redirect(request, redirect_uri):
        return RedirectResponse(url="http://localhost:5556/dex/auth")

    monkeypatch.setattr(auth.oauth.dex, "authorize_redirect", fake_authorize_redirect)
    fake_dex_login(monkeypatch)

    client = TestClient(app)
    client.get("/auth/login", params={"next": next_path}, follow_redirects=False)
    response = client.get("/auth/callback", follow_redirects=False)
    assert response.headers["location"] == next_path


@pytest.mark.parametrize("next_path", ["//evil.com", "https://evil.com", "/projects"])
def test_login_ignores_unsafe_next_path(monkeypatch, next_path):
    async def fake_authorize_redirect(request, redirect_uri):
        return RedirectResponse(url="http://localhost:5556/dex/auth")

    monkeypatch.setattr(auth.oauth.dex, "authorize_redirect", fake_authorize_redirect)
    fake_dex_login(monkeypatch)

    client = TestClient(app)
    client.get("/auth/login", params={"next": next_path}, follow_redirects=False)
    response = client.get("/auth/callback", follow_redirects=False)
    assert response.headers["location"] == "/web/"


def test_callback_stores_user_in_session_and_redirects(monkeypatch):
    monkeypatch.delitem(app.dependency_overrides, require_user)
    fake_dex_login(monkeypatch)

    client = TestClient(app)
    response = client.get("/auth/callback", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/web/"
    assert "session" in response.cookies

    user = client.get("/api/v1/user")
    assert user.status_code == 200
    assert user.json()["email"] == "test@example.com"


def test_callback_returns_400_when_token_exchange_fails(monkeypatch):
    async def fake_authorize_access_token(request):
        raise OAuthError(error="invalid_grant")

    monkeypatch.setattr(
        auth.oauth.dex, "authorize_access_token", fake_authorize_access_token
    )

    client = TestClient(app)
    response = client.get("/auth/callback")
    assert response.status_code == 400
    assert response.json() == {"detail": "Login failed"}


def test_api_requires_login():
    """Unauthenticated API calls get 401; open routes stay reachable."""
    app.dependency_overrides.pop(require_user, None)

    client = TestClient(app)
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    assert client.get("/health").status_code == 200


def test_logout_clears_session_and_redirects(monkeypatch):
    monkeypatch.delitem(app.dependency_overrides, require_user)
    fake_dex_login(monkeypatch)

    client = TestClient(app)
    client.get("/auth/callback", follow_redirects=False)
    response = client.post("/auth/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/web/"
    assert client.get("/api/v1/user").status_code == 401


def test_impersonation_token_authenticates_api_calls():
    """A bearer impersonation token impersonates the user it was created for."""
    app.dependency_overrides.pop(require_user, None)
    token = auth.create_impersonation_token({"sub": "abc", "email": "run@example.com"})

    client = TestClient(app)
    response = client.get("/api/v1/user", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "run@example.com"


@pytest.mark.parametrize(
    "header",
    [
        "Bearer not-a-real-token",
        "Basic dXNlcjpwYXNz",
        "Bearer",
    ],
)
def test_bad_authorization_header_is_rejected(header):
    app.dependency_overrides.pop(require_user, None)
    client = TestClient(app)
    response = client.get("/api/v1/user", headers={"Authorization": header})
    assert response.status_code == 401


def test_expired_impersonation_token_is_rejected(monkeypatch):
    app.dependency_overrides.pop(require_user, None)
    monkeypatch.setattr(auth, "IMPERSONATION_TOKEN_MAX_AGE", -1)
    token = auth.create_impersonation_token({"email": "run@example.com"})

    client = TestClient(app)
    response = client.get("/api/v1/user", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_impersonation_token_signed_with_other_key_is_rejected():
    """A token signed with a different key is refused."""
    app.dependency_overrides.pop(require_user, None)
    forged = URLSafeTimedSerializer(
        "someone-else", salt=auth.IMPERSONATION_TOKEN_SALT
    ).dumps({"email": "admin@example.com"})

    client = TestClient(app)
    response = client.get("/api/v1/user", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_logout_rejects_get():
    client = TestClient(app)
    response = client.get("/auth/logout", follow_redirects=False)
    assert response.status_code == 405


API_KEY = "kg_test-secret"


@pytest.fixture
def api_key_client(engine, session):
    """A client with no login, plus one stored key that belongs to owner@example.com."""
    app.dependency_overrides.pop(require_user, None)
    app.dependency_overrides[get_engine] = lambda: engine
    ApiKeyRepository(session).create(
        name="ci",
        key_hash=hash_api_key(API_KEY),
        owner="user-1",
        owner_email="owner@example.com",
        owner_name="owner",
        expires_at=None,
    )
    session.commit()
    yield TestClient(app)
    app.dependency_overrides.clear()


def get_user_with_key(client: TestClient, key: str = API_KEY):
    return client.get("/api/v1/user", headers={"Authorization": f"Bearer {key}"})


def test_api_key_authenticates_as_its_owner(api_key_client):
    response = get_user_with_key(api_key_client)
    assert response.status_code == 200
    assert response.json()["email"] == "owner@example.com"


def test_unknown_api_key_is_rejected(api_key_client):
    assert get_user_with_key(api_key_client, "kg_not-a-real-key").status_code == 401


def test_revoked_api_key_is_rejected(api_key_client, session):
    row = session.scalars(select(ApiKeyRow)).one()
    row.revoked_at = datetime.now(UTC)
    session.commit()

    assert get_user_with_key(api_key_client).status_code == 401


def test_expired_api_key_is_rejected(api_key_client, session):
    row = session.scalars(select(ApiKeyRow)).one()
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()

    assert get_user_with_key(api_key_client).status_code == 401


def test_using_an_api_key_records_last_used(api_key_client, session):
    assert get_user_with_key(api_key_client).status_code == 200
    row = session.scalars(select(ApiKeyRow)).one()
    assert row.last_used_at is not None
