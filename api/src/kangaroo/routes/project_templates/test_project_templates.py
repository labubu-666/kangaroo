from fastapi.testclient import TestClient

from kangaroo.app import app


def test_lists_templates_with_default():
    """GET /api/v1/project-templates names the templates and the default."""
    response = TestClient(app).get("/api/v1/project-templates/")
    assert response.status_code == 200
    assert response.json() == {"default": "To Do List", "names": ["To Do List"]}
