import httpx
import pytest
from authlib.integrations.starlette_client import OAuthError
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.routes import auth
from kangaroo.routes.auth import require_user
from kangaroo.settings import settings


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
    response = client.get("/login", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].startswith("http://localhost:5556/dex/auth")


def test_login_returns_503_when_dex_is_unreachable(monkeypatch):
    async def fake_authorize_redirect(request, redirect_uri):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(auth.oauth.dex, "authorize_redirect", fake_authorize_redirect)

    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 503
    assert response.json() == {"detail": "Login provider unavailable"}


@pytest.mark.parametrize("next_path", ["/web/projects/1", "/web/boards?view=list#top"])
def test_login_returns_to_next_path_after_callback(monkeypatch, next_path):
    async def fake_authorize_redirect(request, redirect_uri):
        return RedirectResponse(url="http://localhost:5556/dex/auth")

    monkeypatch.setattr(auth.oauth.dex, "authorize_redirect", fake_authorize_redirect)
    fake_dex_login(monkeypatch)

    client = TestClient(app)
    client.get("/login", params={"next": next_path}, follow_redirects=False)
    response = client.get("/auth/callback", follow_redirects=False)
    assert response.headers["location"] == next_path


@pytest.mark.parametrize("next_path", ["//evil.com", "https://evil.com", "/projects"])
def test_login_ignores_unsafe_next_path(monkeypatch, next_path):
    async def fake_authorize_redirect(request, redirect_uri):
        return RedirectResponse(url="http://localhost:5556/dex/auth")

    monkeypatch.setattr(auth.oauth.dex, "authorize_redirect", fake_authorize_redirect)
    fake_dex_login(monkeypatch)

    client = TestClient(app)
    client.get("/login", params={"next": next_path}, follow_redirects=False)
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
    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/web/"
    assert client.get("/api/v1/user").status_code == 401


def test_logout_rejects_get():
    client = TestClient(app)
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 405
