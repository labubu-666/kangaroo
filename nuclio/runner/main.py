import json
import os
import re
import subprocess
import tempfile

# Hard cap on a script's run time, even if the caller asks for longer.
MAX_TIMEOUT_SECONDS = 15

# The PEP 723 block that uv reads to install a script's dependencies.
PEP723_BLOCK = re.compile(r"^# /// script$.*?^# ///$", re.MULTILINE | re.DOTALL)

# Runs the user's script and saves what its main() returned as JSON. A script
# with main() is loaded under a name other than "__main__" so that its
# ``if __name__ == "__main__"`` block does not call main() a second time.
# This copies api/src/kangaroo/runners/local.py, because this function is
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


def wrapper_for(code):
    match = PEP723_BLOCK.search(code)
    header = f"{match.group(0)}\n" if match else ""
    return header + WRAPPER


def run_script(code, env, timeout):
    """Run a script and return the RunResult fields as a dict."""
    with tempfile.TemporaryDirectory() as directory:
        script = os.path.join(directory, "script.py")
        wrapper = os.path.join(directory, "wrapper.py")
        result_path = os.path.join(directory, "result.json")
        with open(script, "w") as f:
            f.write(code)
        with open(wrapper, "w") as f:
            f.write(wrapper_for(code))
        with open(result_path, "w") as f:
            f.write("null")
        try:
            completed = subprocess.run(
                ["uv", "run", "--script", wrapper, script, result_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, **env},
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "ERROR",
                "logs": "",
                "result": None,
                "error": f"Timed out after {timeout} seconds",
            }
        logs = completed.stdout + completed.stderr
        if completed.returncode != 0:
            return {
                "status": "ERROR",
                "logs": logs,
                "result": None,
                "error": f"Exited with code {completed.returncode}",
            }
        with open(result_path) as f:
            return {"status": "SUCCESS", "logs": logs, "result": json.load(f), "error": None}


def run_tool(tool, args, timeout):
    """Run a tool with uvx and return the RunResult fields as a dict."""
    try:
        completed = subprocess.run(
            ["uvx", tool, *args], capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "ERROR",
            "logs": "",
            "result": None,
            "error": f"Timed out after {timeout} seconds",
        }
    logs = completed.stdout + completed.stderr
    if completed.returncode != 0:
        return {
            "status": "ERROR",
            "logs": logs,
            "result": None,
            "error": f"Exited with code {completed.returncode}",
        }
    return {"status": "SUCCESS", "logs": logs, "result": None, "error": None}


def handler(context, event):
    # Nuclio passes JSON bodies as a dict when Content-Type is application/json,
    # and as raw bytes otherwise.
    body = event.body if isinstance(event.body, dict) else json.loads(event.body or "{}")
    timeout = min(int(body.get("timeout_seconds", MAX_TIMEOUT_SECONDS)), MAX_TIMEOUT_SECONDS)
    if "tool" in body:  # e.g. {"tool": "cowsay", "args": ["-t", "hi"]}
        payload = run_tool(body["tool"], body.get("args", []), timeout)
    else:  # {"code": "...python with optional PEP 723 header..."}
        payload = run_script(body.get("code", ""), body.get("env", {}), timeout)
    return context.Response(
        body=json.dumps(payload),
        content_type="application/json",
        status_code=200,
    )
