import gzip
import importlib
import tempfile
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import kangaroo.app
import kangaroo.settings
from kangaroo.app import SPAStaticFiles, app


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


def test_docs_not_at_root():
    """Swagger UI docs should not be served at /docs."""
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 404


def test_spa_static_files_fallback_to_index():
    """SPAStaticFiles should serve index.html for unknown paths (SPA routing)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create index.html and a static file
        index_content = b"<html><body>Index</body></html>"
        (tmpdir_path / "index.html").write_bytes(index_content)
        (tmpdir_path / "asset.js").write_bytes(b"console.log('asset');")

        # Create a test app with SPAStaticFiles
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
    response = client.get("/web/index.html")

    assert response.status_code == 200
    assert response.content == b"body"
    assert response.headers["content-type"] == "text/plain"
    assert "content-encoding" not in response.headers
    assert "transfer-encoding" not in response.headers
