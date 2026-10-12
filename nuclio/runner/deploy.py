#!/usr/bin/env python3
"""Deploy the runner function to the Nuclio dashboard via its REST API."""

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://localhost:8070")
PROJECT = os.environ.get("PROJECT", "kangaroo")
SOURCE = Path(__file__).resolve().parent / "main.py"


def request(method: str, path: str, payload: dict, project: str | None = None) -> str:
    headers = {"Content-Type": "application/json"}
    if project:
        headers["X-Nuclio-Project-Name"] = project
    req = urllib.request.Request(
        f"{DASHBOARD_URL}{path}",
        data=json.dumps(payload).encode(),
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode()


def main() -> None:
    # Create the project if it does not exist yet.
    try:
        request(
            "POST",
            "/api/projects",
            {"metadata": {"name": PROJECT, "namespace": "nuclio"}, "spec": {}},
        )
    except urllib.error.HTTPError:
        pass  # Project already exists.

    payload = {
        "metadata": {
            "name": "runner",
            "namespace": "nuclio",
            "labels": {"nuclio.io/project-name": PROJECT},
        },
        "spec": {
            "runtime": "python:3.11",
            "handler": "main:handler",
            "build": {
                "functionSourceCode": base64.b64encode(SOURCE.read_bytes()).decode(),
                "commands": ["pip install uv"],
            },
            "env": [{"name": "UV_CACHE_DIR", "value": "/tmp/uv-cache"}],
            "triggers": {
                "default-http": {
                    "kind": "http",
                    "name": "default-http",
                    "numWorkers": 1,
                    "mode": "sync",
                    "attributes": {"port": 18090},
                }
            },
        },
    }
    # The dashboard rejects updates (409 on POST, 405 on PUT), so remove any
    # existing runner first. Ignore the error if it does not exist.
    try:
        request("DELETE", "/api/functions", {"metadata": {"name": "runner", "namespace": "nuclio"}}, project=PROJECT)
    except urllib.error.HTTPError:
        pass

    print(request("POST", "/api/functions", payload, project=PROJECT))


if __name__ == "__main__":
    main()
