import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.routes.dependencies import get_engine


@pytest.fixture
def client(engine):
    """Provide a TestClient that uses fresh database for each test."""
    app.dependency_overrides[get_engine] = lambda: engine
    yield TestClient(app)
    app.dependency_overrides.clear()


def create_function(client, code="print(1 + 1)"):
    response = client.post("/api/v1/functions", json={"name": "Hello", "code": code})
    return response.json()["id"]


def test_run_stores_invocation(client):
    """POST /api/v1/functions/{id}/run returns the stored invocation."""
    function_id = create_function(client)
    response = client.post(f"/api/v1/functions/{function_id}/run")
    assert response.status_code == 200
    data = response.json()
    assert data["function_id"] == function_id
    assert data["stdout"] == "2\n"
    assert data["exit_code"] == 0
    assert "created_at" in data


def test_get_invocation(client):
    """GET /api/v1/invocations/{id} returns the stored run."""
    function_id = create_function(client)
    run = client.post(f"/api/v1/functions/{function_id}/run").json()
    response = client.get(f"/api/v1/invocations/{run['id']}")
    assert response.status_code == 200
    assert response.json() == run


def test_get_missing_invocation(client):
    """GET /api/v1/invocations/{id} returns 404 for an unknown ID."""
    response = client.get("/api/v1/invocations/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_invocations_filters_by_function(client):
    """GET /api/v1/invocations lists only the runs of the given function."""
    first = create_function(client, code="print('a')")
    second = create_function(client, code="print('b')")
    client.post(f"/api/v1/functions/{first}/run")
    client.post(f"/api/v1/functions/{second}/run")
    client.post(f"/api/v1/functions/{first}/run")

    data = client.get(f"/api/v1/invocations?function_id={first}").json()
    assert data["total"] == 2
    assert {item["function_id"] for item in data["results"]} == {first}


def test_deleting_function_deletes_its_invocations(client):
    """Invocations are removed with the function they ran."""
    function_id = create_function(client)
    client.post(f"/api/v1/functions/{function_id}/run")
    client.delete(f"/api/v1/functions/{function_id}")
    assert client.get("/api/v1/invocations").json()["total"] == 0
