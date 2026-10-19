import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from kangaroo.app import app
from kangaroo.repositories import (
    ProjectRepository,
    StatusRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
)
from kangaroo.routes.dependencies import get_engine
from kangaroo.runners import RunnerUnavailableError
from kangaroo.schemas import RunResult
from kangaroo.testing import new_task, seed_project


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
    assert data["status"] == "SUCCESS"
    assert data["logs"] == "2\n"
    assert data["result"] is None
    assert data["error"] is None
    assert "created_at" in data


def test_script_can_write_to_the_database_during_a_run(client, engine, monkeypatch):
    """A script's own API writes succeed while its run is in progress.

    The RUNNING row must not hold the database lock for the length of the run.
    """
    with Session(engine) as session, session.begin():
        seeded = seed_project(
            ProjectRepository(session),
            StatusRepository(session),
            WorkItemTypeRepository(session),
        )

    class WritingRunner:
        def run(self, request):
            with Session(engine) as session, session.begin():
                WorkItemRepository(session).create(new_task(seeded, "During run"))
            return RunResult(status="SUCCESS", logs="", result=None, error=None)

    monkeypatch.setattr(
        "kangaroo.routes.dependencies.get_function_runner",
        lambda: WritingRunner(),
    )
    function_id = create_function(client)
    response = client.post(f"/api/v1/functions/{function_id}/run")
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"


def test_unreachable_runner_stores_error(client, monkeypatch):
    """A runner that cannot be reached returns 503 and the invocation is stored as ERROR."""

    class UnreachableRunner:
        def run(self, request):
            raise RunnerUnavailableError("Nuclio runner unavailable: down")

    monkeypatch.setattr(
        "kangaroo.routes.dependencies.get_function_runner",
        lambda: UnreachableRunner(),
    )
    function_id = create_function(client)
    response = client.post(f"/api/v1/functions/{function_id}/run")
    assert response.status_code == 503
    listed = client.get(f"/api/v1/invocations?function_id={function_id}").json()
    assert listed["total"] == 1
    assert listed["results"][0]["status"] == "ERROR"
    assert listed["results"][0]["error"] == "Nuclio runner unavailable: down"


def test_run_stores_main_result(client):
    """The value main() returns is stored as the invocation's result."""
    code = "def main():\n    return {'answer': 42}\n"
    function_id = create_function(client, code=code)
    data = client.post(f"/api/v1/functions/{function_id}/run").json()
    assert data["result"] == {"answer": 42}
    assert client.get(f"/api/v1/invocations/{data['id']}").json()["result"] == {
        "answer": 42
    }


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


def test_list_invocations_newest_first(client):
    """GET /api/v1/invocations lists the newest runs first, across pages."""
    function_id = create_function(client)
    runs = [
        client.post(f"/api/v1/functions/{function_id}/run").json() for _ in range(3)
    ]

    data = client.get("/api/v1/invocations?limit=2").json()
    assert data["total"] == 3
    assert [item["id"] for item in data["results"]] == [runs[2]["id"], runs[1]["id"]]

    data = client.get("/api/v1/invocations?limit=2&offset=2").json()
    assert [item["id"] for item in data["results"]] == [runs[0]["id"]]


def test_deleting_function_deletes_its_invocations(client):
    """Invocations are removed with the function they ran."""
    function_id = create_function(client)
    client.post(f"/api/v1/functions/{function_id}/run")
    client.delete(f"/api/v1/functions/{function_id}")
    assert client.get("/api/v1/invocations").json()["total"] == 0
