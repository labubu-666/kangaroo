import json
import urllib.error
import urllib.request

from kangaroo.runners.base import BaseRunner
from kangaroo.schemas import RunRequest, RunResult


class RunnerUnavailableError(Exception):
    """The runner could not be reached or returned an error."""


class NuclioRunner(BaseRunner):
    """Sends scripts to the deployed Nuclio ``runner`` function over HTTP.

    The function runs each script in its own container. It saves the value the
    script's ``main()`` returned and reports it as ``result``.
    """

    def __init__(self, url: str) -> None:
        self._url = url

    def run(self, request: RunRequest) -> RunResult:
        body = json.dumps(request.model_dump()).encode()
        req = urllib.request.Request(
            self._url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # Allow the function its own timeout plus a margin for the HTTP round trip.
        http_timeout = request.timeout_seconds + 10
        try:
            with urllib.request.urlopen(req, timeout=http_timeout) as resp:
                return RunResult.model_validate(json.loads(resp.read().decode()))
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise RunnerUnavailableError(f"Nuclio runner unavailable: {exc}") from exc
