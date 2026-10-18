import os
import subprocess
import tempfile

from kangaroo.runners.base import BaseRunner
from kangaroo.schemas import RunRequest, RunResult


class LocalRunner(BaseRunner):
    """Runs scripts with ``uv run --script`` on the machine running the API.

    Intended for development and tests. Scripts run with the API's own user,
    files and network, so do not use it for untrusted code.
    """

    def run(self, request: RunRequest) -> RunResult:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as script:
            script.write(request.code)
        try:
            result = subprocess.run(
                ["uv", "run", "--script", script.name],
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                env={**os.environ, **request.env},
                check=False,
            )
            return RunResult(
                stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode
            )
        except subprocess.TimeoutExpired:
            return RunResult(
                stdout="",
                stderr=f"Timed out after {request.timeout_seconds} seconds",
                exit_code=-1,
            )
        finally:
            os.remove(script.name)
