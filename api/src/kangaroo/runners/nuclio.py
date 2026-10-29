import requests

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
        # Allow the function its own timeout plus a margin for the HTTP round trip.
        http_timeout = request.timeout_seconds + 10
        try:
            resp = requests.post(
                self._url, json=request.model_dump(), timeout=http_timeout
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RunnerUnavailableError(
                f"Nuclio runner at {self._url} is unreachable: {exc}"
            ) from exc
        try:
            return RunResult.model_validate(resp.json())
        except ValueError as exc:
            # Usually NUCLIO_RUNNER_URL points at a different service.
            content_type = resp.headers.get("Content-Type", "unknown")
            raise RunnerUnavailableError(
                f"Nuclio runner at {self._url} returned an invalid response "
                f"({content_type}): {resp.text[:200]!r}"
            ) from exc
