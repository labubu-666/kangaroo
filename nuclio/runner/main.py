import json
import os
import subprocess
import tempfile

# Hard cap on a script's run time, even if the caller asks for longer.
MAX_TIMEOUT_SECONDS = 15


def handler(context, event):
    # Nuclio passes JSON bodies as a dict when Content-Type is application/json,
    # and as raw bytes otherwise.
    body = event.body if isinstance(event.body, dict) else json.loads(event.body or "{}")
    timeout = min(int(body.get("timeout_seconds", MAX_TIMEOUT_SECONDS)), MAX_TIMEOUT_SECONDS)
    script_path = None
    try:
        if "tool" in body:  # e.g. {"tool": "cowsay", "args": ["-t", "hi"]}
            cmd = ["uvx", body["tool"], *body.get("args", [])]
        else:  # {"code": "...python with optional PEP 723 header..."}
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                f.write(body.get("code", ""))
                script_path = f.name
            cmd = ["uv", "run", "--script", script_path]
        env = {**os.environ, **body.get("env", {})}
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, env=env
        )
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
