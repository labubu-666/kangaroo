import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from kangaroo.runners import (
    LocalRunner,
    NuclioRunner,
    RunnerUnavailableError,
    create_runner,
)
from kangaroo.schemas import MAX_RUN_TIMEOUT_SECONDS, RunRequest, RunResult


@pytest.fixture
def fake_nuclio():
    """Serve a real HTTP endpoint that answers like the Nuclio runner does."""
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers["Content-Length"])
            received["body"] = json.loads(self.rfile.read(length))
            payload = json.dumps(
                {"stdout": "from nuclio\n", "stderr": "", "exit_code": 0}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", received
    server.shutdown()
    server.server_close()


def test_local_runner_runs_script():
    """LocalRunner runs the code with uv and returns its output."""
    result = LocalRunner().run(RunRequest(code="print(1 + 1)"))
    assert result == RunResult(stdout="2\n", stderr=result.stderr, exit_code=0)


def test_local_runner_reports_failure():
    """A script that exits with an error returns its exit code and stderr."""
    result = LocalRunner().run(RunRequest(code="raise SystemExit('boom')"))
    assert result.exit_code == 1
    assert "boom" in result.stderr


def test_local_runner_times_out():
    """A script over its timeout returns exit code -1."""
    result = LocalRunner().run(
        RunRequest(code="import time\ntime.sleep(10)", timeout_seconds=1)
    )
    assert result.exit_code == -1
    assert result.stderr == "Timed out after 1 seconds"


def test_nuclio_runner_sends_standard_request(fake_nuclio):
    """NuclioRunner posts the RunRequest fields and returns the RunResult."""
    url, received = fake_nuclio
    result = NuclioRunner(url).run(RunRequest(code="print(1)", timeout_seconds=15))
    assert received["body"] == {"code": "print(1)", "timeout_seconds": 15}
    assert result == RunResult(stdout="from nuclio\n", stderr="", exit_code=0)


def test_nuclio_runner_unreachable_raises():
    """A runner that cannot be reached raises RunnerUnavailableError."""
    with pytest.raises(RunnerUnavailableError):
        NuclioRunner("http://127.0.0.1:1").run(RunRequest(code="print(1)"))


def test_create_runner_local():
    assert isinstance(create_runner("local"), LocalRunner)


def test_create_runner_nuclio(fake_nuclio):
    url, _ = fake_nuclio
    assert isinstance(create_runner("nuclio", url), NuclioRunner)


def test_create_runner_nuclio_requires_url():
    with pytest.raises(ValueError, match="NUCLIO_RUNNER_URL"):
        create_runner("nuclio")


def test_create_runner_unknown_name():
    with pytest.raises(ValueError, match="Unsupported FUNCTION_RUNNER"):
        create_runner("docker")


def test_run_request_timeout_is_capped():
    """The timeout defaults to the maximum, and anything above or below the range is refused."""
    assert RunRequest(code="print(1)").timeout_seconds == MAX_RUN_TIMEOUT_SECONDS
    with pytest.raises(ValueError):
        RunRequest(code="print(1)", timeout_seconds=MAX_RUN_TIMEOUT_SECONDS + 1)
    with pytest.raises(ValueError):
        RunRequest(code="print(1)", timeout_seconds=0)
