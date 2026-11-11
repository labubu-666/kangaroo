from kangaroo.routes.pipelines.test_pipelines import create, save_steps, steps_for

TWO_STEPS = {"a": (["b"], []), "b": ([], [])}


def test_list_runs_and_get_a_run(client):
    """A queued run shows in its pipeline's runs, with every step PENDING."""
    ids = save_steps(client, "a", "b")
    created = create(client, steps=steps_for(ids, TWO_STEPS)).json()
    run_id = client.post(f"/api/v1/pipelines/{created['id']}/run").json()["run_id"]

    runs = client.get(f"/api/v1/pipelines/{created['id']}/runs").json()
    assert runs["total"] == 1
    assert runs["results"][0]["id"] == run_id

    run = client.get(f"/api/v1/runs/{run_id}").json()
    assert run["status"] == "RUNNING"
    assert run["steps"] == [
        {"step": "a", "status": "PENDING", "invocation_id": None},
        {"step": "b", "status": "PENDING", "invocation_id": None},
    ]


def test_get_missing_run(client):
    """GET /api/v1/runs/{id} returns 404 for an unknown run."""
    response = client.get("/api/v1/runs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_list_all_runs_filters_by_pipeline(client):
    """GET /api/v1/runs lists every pipeline's runs, or one pipeline's with a filter."""
    ids = save_steps(client, "a")
    one_step = steps_for(ids, {"a": ([], [])})
    first = create(client, name="First", steps=one_step).json()
    second = create(client, name="Second", steps=one_step).json()
    client.post(f"/api/v1/pipelines/{first['id']}/run")
    client.post(f"/api/v1/pipelines/{second['id']}/run")
    client.post(f"/api/v1/pipelines/{first['id']}/run")

    everything = client.get("/api/v1/runs/").json()
    assert everything["total"] == 3

    only_first = client.get(f"/api/v1/runs/?pipeline_id={first['id']}").json()
    assert only_first["total"] == 2
    assert {run["pipeline_id"] for run in only_first["results"]} == {first["id"]}
