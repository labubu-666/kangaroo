import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from kangaroo.runners.base import BaseRunner
from kangaroo.schemas import RunRequest, RunResult

# The PEP 723 block that uv reads to install a script's dependencies.
PEP723_BLOCK = re.compile(r"^# /// script$.*?^# ///$", re.MULTILINE | re.DOTALL)

# Runs the user's script and saves what its main() returned as JSON. A script
# with main() is loaded under a name other than "__main__" so that its
# ``if __name__ == "__main__"`` block does not call main() a second time.
# nuclio/runner/main.py carries a copy of this, because that function is
# deployed separately and cannot import the API.
WRAPPER = """
import ast
import json
import runpy
import sys

script, result_path = sys.argv[1], sys.argv[2]
with open(script) as f:
    tree = ast.parse(f.read())
has_main = any(
    isinstance(node, ast.FunctionDef) and node.name == "main" for node in tree.body
)
if has_main:
    value = runpy.run_path(script, run_name="kangaroo")["main"]()
else:
    runpy.run_path(script, run_name="__main__")
    value = None
try:
    payload = json.dumps(value)
except (TypeError, ValueError) as exc:
    print(f"Result is not JSON serializable: {exc}", file=sys.stderr)
    sys.exit(1)
with open(result_path, "w") as f:
    f.write(payload)
"""


def wrapper_for(code: str) -> str:
    """Return the wrapper with the script's PEP 723 header, so uv installs its dependencies."""
    match = PEP723_BLOCK.search(code)
    header = f"{match.group(0)}\n" if match else ""
    return header + WRAPPER


class LocalRunner(BaseRunner):
    """Runs scripts with ``uv run --script`` on the machine running the API.

    Intended for development and tests. Scripts run with the API's own user,
    files and network, so do not use it for untrusted code.
    """

    def run(self, request: RunRequest) -> RunResult:
        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory, "script.py")
            script.write_text(request.code)
            wrapper = Path(directory, "wrapper.py")
            wrapper.write_text(wrapper_for(request.code))
            result_path = Path(directory, "result.json")
            # Read as null if the script exits without the wrapper saving a result.
            result_path.write_text("null")
            try:
                completed = subprocess.run(
                    [
                        "uv",
                        "run",
                        "--script",
                        str(wrapper),
                        str(script),
                        str(result_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=request.timeout_seconds,
                    env={**os.environ, **request.env},
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return RunResult(
                    status="ERROR",
                    logs="",
                    error=f"Timed out after {request.timeout_seconds} seconds",
                )
            logs = completed.stdout + completed.stderr
            if completed.returncode != 0:
                return RunResult(
                    status="ERROR",
                    logs=logs,
                    error=f"Exited with code {completed.returncode}",
                )
            return RunResult(
                status="SUCCESS",
                logs=logs,
                result=json.loads(result_path.read_text()),
            )
