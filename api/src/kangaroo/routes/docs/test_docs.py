import importlib

from fastapi.testclient import TestClient

from kangaroo.app import app

docs = importlib.import_module("kangaroo.routes.docs.router")


def test_get_doc_renders_markdown(monkeypatch, tmp_path):
    """GET /api/v1/docs/{name} renders docs/{name}.md to HTML."""
    monkeypatch.setattr(docs, "DOCS_DIR", tmp_path)
    (tmp_path / "guide.md").write_text("# Guide\n\nHello **world**", encoding="utf-8")
    client = TestClient(app)

    response = client.get("/api/v1/docs/guide")

    assert response.status_code == 200
    assert response.json() == {
        "name": "guide",
        "html": "<h1>Guide</h1>\n<p>Hello <strong>world</strong></p>",
    }


def test_get_doc_keeps_internal_links_in_same_tab(monkeypatch, tmp_path):
    """Links between docs have no target; external links open in a new tab."""
    monkeypatch.setattr(docs, "DOCS_DIR", tmp_path)
    (tmp_path / "index.md").write_text(
        "- [Filter](./filter-language)\n- [Site](https://example.com)",
        encoding="utf-8",
    )
    client = TestClient(app)

    response = client.get("/api/v1/docs/index")

    html = response.json()["html"]
    assert '<a href="./filter-language" rel="noopener noreferrer">Filter</a>' in html
    assert (
        '<a href="https://example.com" target="_blank" rel="noopener noreferrer">Site</a>'
        in html
    )


def test_get_doc_missing_returns_404(monkeypatch, tmp_path):
    """A doc without a matching file returns 404."""
    monkeypatch.setattr(docs, "DOCS_DIR", tmp_path)
    client = TestClient(app)

    response = client.get("/api/v1/docs/missing")

    assert response.status_code == 404


def test_get_doc_rejects_path_traversal(monkeypatch, tmp_path):
    """Names outside the simple slug format are rejected, even if the file exists."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (tmp_path / "secret.md").write_text("nope", encoding="utf-8")
    monkeypatch.setattr(docs, "DOCS_DIR", docs_dir)
    client = TestClient(app)

    response = client.get("/api/v1/docs/..%2Fsecret")

    assert response.status_code == 404
