import pytest


@pytest.fixture
def project_id(client):
    """Create a project from the default template, through the API."""
    return client.post("/api/v1/projects", json={"name": "Test"}).json()["id"]
