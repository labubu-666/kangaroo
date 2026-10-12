#!/usr/bin/env python3
"""Remove the runner function from the Nuclio dashboard."""

import json
import os
import urllib.request

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://localhost:8070")
PROJECT = os.environ.get("PROJECT", "kangaroo")


def main() -> None:
    payload = {"metadata": {"name": "runner", "namespace": "nuclio"}}
    req = urllib.request.Request(
        f"{DASHBOARD_URL}/api/functions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Nuclio-Project-Name": PROJECT,
        },
        method="DELETE",
    )
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode())


if __name__ == "__main__":
    main()
