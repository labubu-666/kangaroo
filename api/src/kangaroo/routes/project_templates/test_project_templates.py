def test_lists_templates_with_default(client):
    """GET /api/v1/project-templates names the templates and the default."""
    response = client.get("/api/v1/project-templates/")
    assert response.status_code == 200
    assert response.json() == {"default": "To Do List", "names": ["To Do List"]}
