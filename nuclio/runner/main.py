import json
import os
import subprocess
import tempfile


def handler(context, event):
    # Nuclio passes JSON bodies as a dict when Content-Type is application/json,
    # and as raw bytes otherwise.
    body = event.body if isinstance(event.body, dict) else json.loads(event.body or "{}")
    timeout = int(body.get("timeout_seconds", 120))
    script_path = None
    try:
        if "tool" in body:  # e.g. {"tool": "cowsay", "args": ["-t", "hi"]}
            cmd = ["uvx", body["tool"], *body.get("args", [])]
        else:  # {"code": "...python with optional PEP 723 header..."}
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                f.write(body.get("code", ""))
                script_path = f.name
            cmd = ["uv", "run", "--script", script_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        payload = {"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        payload = {"stdout": "", "stderr": f"Timed out after {timeout} seconds", "exit_code": -1}
    finally:
        if script_path and os.path.exists(script_path):
            os.remove(script_path)
    return context.Response(
        body=json.dumps(payload),
        content_type="application/json",
        status_code=200,
    )
