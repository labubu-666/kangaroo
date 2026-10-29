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
                {
                    "status": "SUCCESS",
                    "logs": "from nuclio\n",
                    "result": None,
                    "error": None,
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", received
    server.shutdown()
    server.server_close()


@pytest.fixture
def fake_nuclio_html():
    """Serve an HTML page on every path, like a different service on the runner's port."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = b"<!DOCTYPE html><html><body>Adminer</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_local_runner_runs_script():
    """A script that prints succeeds and its output is in the logs."""
    result = LocalRunner().run(RunRequest(code="print(1 + 1)"))
    assert result == RunResult(status="SUCCESS", logs="2\n", result=None, error=None)


def test_local_runner_reports_failure():
    """A script that exits with an error has ERROR status and its stderr in the logs."""
    result = LocalRunner().run(RunRequest(code="raise SystemExit('boom')"))
    assert result.status == "ERROR"
    assert result.error == "Exited with code 1"
    assert "boom" in result.logs


def test_local_runner_times_out():
    """A script over its timeout has ERROR status."""
    result = LocalRunner().run(
        RunRequest(code="import time\ntime.sleep(10)", timeout_seconds=1)
    )
    assert result.status == "ERROR"
    assert result.error == "Timed out after 1 seconds"


def test_local_runner_returns_main_result():
    """The value main() returns is the result, and main() runs once."""
    code = 'def main():\n    print("ran")\n    return {"count": 2}\n\nif __name__ == "__main__":\n    main()\n'
    result = LocalRunner().run(RunRequest(code=code))
    assert result.status == "SUCCESS"
    assert result.result == {"count": 2}
    assert result.logs == "ran\n"


def test_local_runner_main_returning_nothing_is_null():
    """A main() that returns nothing gives a null result."""
    result = LocalRunner().run(RunRequest(code="def main():\n    pass\n"))
    assert result == RunResult(status="SUCCESS", logs="", result=None, error=None)


def test_local_runner_script_without_main_has_null_result():
    """A script with no main() runs top to bottom and has a null result."""
    result = LocalRunner().run(RunRequest(code="print('hi')"))
    assert result == RunResult(status="SUCCESS", logs="hi\n", result=None, error=None)


def test_local_runner_non_json_result_is_error():
    """A main() whose return value is not JSON-serializable is an ERROR."""
    result = LocalRunner().run(RunRequest(code="def main():\n    return object()\n"))
    assert result.status == "ERROR"
    assert result.error == "Exited with code 1"
    assert "not JSON serializable" in result.logs


def test_nuclio_runner_sends_standard_request(fake_nuclio):
    """NuclioRunner posts the RunRequest fields and returns the RunResult."""
    url, received = fake_nuclio
    result = NuclioRunner(url).run(RunRequest(code="print(1)", timeout_seconds=15))
    assert received["body"] == {"code": "print(1)", "timeout_seconds": 15, "env": {}}
    assert result == RunResult(
        status="SUCCESS", logs="from nuclio\n", result=None, error=None
    )


def test_nuclio_runner_sends_env(fake_nuclio):
    """NuclioRunner passes the env to the runner so the script can use it."""
    url, received = fake_nuclio
    NuclioRunner(url).run(RunRequest(code="print(1)", env={"KANGAROO_TOKEN": "t"}))
    assert received["body"]["env"] == {"KANGAROO_TOKEN": "t"}


def test_local_runner_passes_env():
    """LocalRunner makes the request env visible to the script."""
    code = 'import os\nprint(os.environ["KANGAROO_TOKEN"])'
    result = LocalRunner().run(RunRequest(code=code, env={"KANGAROO_TOKEN": "abc"}))
    assert result.logs == "abc\n"


def test_nuclio_runner_unreachable_raises():
    """A runner that cannot be reached raises RunnerUnavailableError."""
    with pytest.raises(RunnerUnavailableError):
        NuclioRunner("http://127.0.0.1:1").run(RunRequest(code="print(1)"))


def test_nuclio_runner_non_json_response_raises(fake_nuclio_html):
    """A response that is not JSON, such as another service's HTML page, raises RunnerUnavailableError."""
    url = fake_nuclio_html
    with pytest.raises(RunnerUnavailableError, match="invalid response") as exc:
        NuclioRunner(url).run(RunRequest(code="print(1)"))
    assert url in str(exc.value)


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
