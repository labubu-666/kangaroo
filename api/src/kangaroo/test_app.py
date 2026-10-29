import gzip
import importlib
import tempfile
from pathlib import Path
from urllib.parse import quote

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import kangaroo.app
import kangaroo.settings
from kangaroo.app import SPAStaticFiles, app
from kangaroo.routes.auth import require_user

auth = importlib.import_module("kangaroo.routes.auth.router")


def log_in(client, monkeypatch):
    """Store a logged-in user in the client's session via the real callback."""

    async def fake_authorize_access_token(request):
        return {"userinfo": {"email": "test@example.com", "name": "test-user"}}

    monkeypatch.setattr(
        auth.oauth.dex, "authorize_access_token", fake_authorize_access_token
    )
    client.get("/auth/callback", follow_redirects=False)


def test_logged_out_web_request_redirects_to_login():
    """Logged-out browsers go to login before the web UI is served."""
    app.dependency_overrides.pop(require_user, None)
    client = TestClient(app)
    response = client.get("/web/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/auth/login?next=%2Fweb%2F"


def test_login_redirect_keeps_path_and_query():
    """The original path and query string come back after logging in."""
    app.dependency_overrides.pop(require_user, None)
    client = TestClient(app)
    response = client.get("/web/projects?view=list", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/auth/login?next=" + quote(
        "/web/projects?view=list", safe=""
    )


def test_logged_in_web_request_is_not_redirected(monkeypatch):
    """Logged-in users are not sent to login when opening the web UI."""
    app.dependency_overrides.pop(require_user, None)
    client = TestClient(app)
    log_in(client, monkeypatch)
    response = client.get("/web/", follow_redirects=False)
    assert "/auth/login" not in response.headers.get("location", "")


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_redirects_to_web():
    """Root path should redirect to the web UI."""
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/web/"


def test_docs_at_api_v1():
    """Swagger UI docs should be served at /api/v1/docs."""
    client = TestClient(app)
    response = client.get("/api/v1/docs")
    assert response.status_code == 200


@pytest.mark.parametrize("path", ["/api/v1/docs", "/api/v1/openapi.json"])
def test_docs_require_login(path):
    """API docs and the OpenAPI schema should not be public."""
    app.dependency_overrides.pop(require_user, None)
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 401


def test_openapi_schema_for_logged_in_user():
    """Logged-in users get the OpenAPI schema for the API."""
    client = TestClient(app)
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/work-items/" in response.json()["paths"]


def test_docs_not_at_root():
    """Swagger UI docs should not be served at /docs."""
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 404


def test_spa_static_files_fallback_to_index():
    """SPAStaticFiles should serve index.html for unknown paths (SPA routing)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        index_content = b"<html><body>Index</body></html>"
        (tmpdir_path / "index.html").write_bytes(index_content)
        (tmpdir_path / "asset.js").write_bytes(b"console.log('asset');")

        test_app = FastAPI()
        test_app.mount(
            "/static",
            SPAStaticFiles(directory=str(tmpdir_path), html=True),
            name="static",
        )

        client = TestClient(test_app)

        # Real file should be served as-is
        response = client.get("/static/asset.js")
        assert response.status_code == 200
        assert response.content == b"console.log('asset');"

        # Unknown path should fall back to index.html
        response = client.get("/static/work-items/123")
        assert response.status_code == 200
        assert response.content == index_content

        # Direct index.html request should work
        response = client.get("/static/index.html")
        assert response.status_code == 200
        assert response.content == index_content


@pytest.fixture
def dev_app(monkeypatch):
    """Reload kangaroo.app with ENV=development so the Vite proxy routes exist."""
    monkeypatch.setattr(kangaroo.settings.settings, "env", "development")
    dev_module = importlib.reload(kangaroo.app)
    yield dev_module
    monkeypatch.undo()
    importlib.reload(kangaroo.app)


def test_dev_proxy_forwards_query_string(dev_app, monkeypatch):
    """Vite code-splitting imports (?tsr-split=component) must reach the dev server."""
    requested_urls = []

    async def fake_get(self, url, **kwargs):
        requested_urls.append(str(url))
        return httpx.Response(
            200,
            content=b"export const component = () => null;",
            headers={
                "content-type": "application/javascript",
                "content-length": "38",
                "connection": "keep-alive",
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = TestClient(dev_app.app)
    log_in(client, monkeypatch)
    response = client.get("/web/src/routes/work-items/index.tsx?tsr-split=component")

    assert response.status_code == 200
    assert requested_urls == [
        "http://localhost:5173/web/src/routes/work-items/index.tsx?tsr-split=component"
    ]
    assert response.content == b"export const component = () => null;"
    assert response.headers["content-type"] == "application/javascript"
    assert "connection" not in response.headers


def test_dev_proxy_drops_headers_for_decoded_body(dev_app, monkeypatch):
    """Headers describing the encoded body must not reach the client after decoding."""
    compressed = gzip.compress(b"body")

    async def fake_get(self, url, **kwargs):
        return httpx.Response(
            200,
            content=compressed,
            headers={
                "content-type": "text/plain",
                "content-encoding": "gzip",
                "content-length": str(len(compressed)),
                "transfer-encoding": "chunked",
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    client = TestClient(dev_app.app)
    log_in(client, monkeypatch)
    response = client.get("/web/index.html")

    assert response.status_code == 200
    assert response.content == b"body"
    assert response.headers["content-type"] == "text/plain"
    assert "content-encoding" not in response.headers
    assert "transfer-encoding" not in response.headers
