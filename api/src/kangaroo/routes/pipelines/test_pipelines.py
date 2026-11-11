from uuid import UUID, uuid4

from kangaroo.repositories.tables import PipelineRunRow


def save_function(client, name):
    response = client.post(
        "/api/v1/functions", json={"name": name, "code": 'print("hi")'}
    )
    return response.json()["id"]


def save_steps(client, *names):
    """Save a function per name and return their IDs, keyed by name."""
    return {name: save_function(client, name) for name in names}


def steps_for(function_ids, graph):
    """Build a pipeline's steps from {step: (on_success, on_failure)} and IDs."""
    return {
        step: {
            "function_id": function_ids[step],
            "on_success": ok,
            "on_failure": fail,
        }
        for step, (ok, fail) in graph.items()
    }


def create(client, **overrides):
    body = {"name": "Flow", "steps": {}, **overrides}
    return client.post("/api/v1/pipelines/", json=body)


def test_create_pipeline(client):
    """POST /api/v1/pipelines saves a pipeline whose steps refer to saved functions."""
    ids = save_steps(client, "a", "b")
    steps = steps_for(ids, {"a": (["b"], []), "b": ([], [])})
    response = create(client, steps=steps, description="Two steps", labels=["demo"])
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Flow"
    assert data["steps"]["a"] == {
        "function_id": ids["a"],
        "on_success": ["b"],
        "on_failure": [],
    }
    assert data["labels"] == ["demo"]


def test_create_pipeline_allows_the_same_function_in_several_steps(client):
    """Steps are keyed by their own name, so one function can run more than once."""
    ids = save_steps(client, "check")
    steps = {
        "check": {"function_id": ids["check"], "on_success": ["again"]},
        "again": {"function_id": ids["check"]},
    }
    response = create(client, steps=steps)
    assert response.status_code == 201


def test_create_pipeline_rejects_unknown_reference(client):
    """A reference to a step that the pipeline does not define is rejected."""
    ids = save_steps(client, "a")
    steps = {"a": {"function_id": ids["a"], "on_success": ["missing"]}}
    response = create(client, steps=steps)
    assert response.status_code == 422


def test_create_pipeline_rejects_a_missing_function(client):
    """Each step must refer to a saved function."""
    ids = save_steps(client, "a")
    steps = {"a": {"function_id": ids["a"]}, "b": {"function_id": str(uuid4())}}
    response = create(client, steps=steps)
    assert response.status_code == 422
    assert "does not exist" in response.json()["detail"]


def test_saving_a_function_with_a_taken_name_is_rejected(client):
    """Function names are unique, so a second function cannot take a used name."""
    save_steps(client, "a")
    response = client.post("/api/v1/functions", json={"name": "a", "code": "x"})
    assert response.status_code == 409


def test_run_pipeline_records_the_user_who_started_it(client, session):
    """A run remembers the user who started it, so its steps can act as that user."""
    ids = save_steps(client, "a")
    created = create(client, steps=steps_for(ids, {"a": ([], [])})).json()
    run_id = client.post(f"/api/v1/pipelines/{created['id']}/run").json()["run_id"]

    row = session.get(PipelineRunRow, UUID(run_id))
    assert row.started_by["email"] == "test@example.com"


def test_run_pipeline_queues_a_run(client):
    """POST /api/v1/pipelines/{id}/run returns 202 with the run ID."""
    save_steps(client, "a", "b")
    created = create(client).json()
    response = client.post(f"/api/v1/pipelines/{created['id']}/run")
    assert response.status_code == 202
    assert "run_id" in response.json()


def test_run_missing_pipeline(client):
    """POST /api/v1/pipelines/{id}/run returns 404 for an unknown ID."""
    response = client.post("/api/v1/pipelines/00000000-0000-0000-0000-000000000000/run")
    assert response.status_code == 404
