import pytest
from fastapi.testclient import TestClient

from kangaroo.app import app
from kangaroo.backends import InMemoryFunctionBackend
from kangaroo.routes.dependencies import get_function_backend

HELLO = 'print("hello")'


@pytest.fixture
def client():
    """Provide a TestClient with a fresh in-memory function backend for each test."""
    functions = InMemoryFunctionBackend()
    app.dependency_overrides[get_function_backend] = lambda: functions
    yield TestClient(app)
    app.dependency_overrides.clear()


def create(client, **overrides):
    body = {"name": "Hello", "code": HELLO, **overrides}
    return client.post("/api/v1/functions", json=body)


def test_create_function(client):
    """POST /api/v1/functions saves a function."""
    response = create(client, description="Says hi", labels=["demo"])
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Hello"
    assert data["description"] == "Says hi"
    assert data["code"] == HELLO
    assert data["labels"] == ["demo"]
    assert "created_at" in data


def test_create_function_missing_code(client):
    """POST /api/v1/functions without code returns validation error."""
    response = client.post("/api/v1/functions", json={"name": "Hello"})
    assert response.status_code == 422


def test_get_function(client):
    """GET /api/v1/functions/{id} returns the saved function."""
    created = create(client).json()
    response = client.get(f"/api/v1/functions/{created['id']}")
    assert response.status_code == 200
    assert response.json()["code"] == HELLO


def test_get_missing_function(client):
    """GET /api/v1/functions/{id} returns 404 for an unknown ID."""
    response = client.get("/api/v1/functions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_functions_with_search(client):
    """GET /api/v1/functions?search= matches name or description."""
    create(client, name="Alpha")
    create(client, name="Beta", description="alpha tool")
    create(client, name="Gamma")

    data = client.get("/api/v1/functions?search=ALPHA").json()
    assert data["total"] == 2
    assert [item["name"] for item in data["results"]] == ["Alpha", "Beta"]


def test_patch_function(client):
    """PATCH /api/v1/functions/{id} updates only the given fields."""
    created = create(client).json()
    response = client.patch(
        f"/api/v1/functions/{created['id']}", json={"name": "Renamed"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert response.json()["code"] == HELLO


def test_put_function(client):
    """PUT /api/v1/functions/{id} replaces the function."""
    created = create(client).json()
    response = client.put(
        f"/api/v1/functions/{created['id']}",
        json={"name": "New", "code": "print(2)"},
    )
    assert response.status_code == 200
    assert response.json()["code"] == "print(2)"
    assert response.json()["description"] is None


def test_delete_function(client):
    """DELETE /api/v1/functions/{id} removes the function."""
    created = create(client).json()
    assert client.delete(f"/api/v1/functions/{created['id']}").status_code == 204
    assert client.get(f"/api/v1/functions/{created['id']}").status_code == 404


def test_run_function(client):
    """POST /api/v1/functions/{id}/run executes the code and returns its output."""
    created = create(client, code="print(1 + 1)").json()
    response = client.post(f"/api/v1/functions/{created['id']}/run")
    assert response.status_code == 200
    data = response.json()
    assert data["stdout"] == "2\n"
    assert data["exit_code"] == 0


def test_run_function_reports_errors(client):
    """A script that raises returns a non-zero exit code and its traceback."""
    created = create(client, code="raise SystemExit('boom')").json()
    response = client.post(f"/api/v1/functions/{created['id']}/run")
    assert response.status_code == 200
    data = response.json()
    assert data["exit_code"] == 1
    assert "boom" in data["stderr"]


def test_run_missing_function(client):
    """POST /api/v1/functions/{id}/run returns 404 for an unknown ID."""
    response = client.post("/api/v1/functions/00000000-0000-0000-0000-000000000000/run")
    assert response.status_code == 404
