from kangaroo.runners.base import BaseRunner
from kangaroo.runners.local import LocalRunner
from kangaroo.runners.nuclio import NuclioRunner


def create_runner(runner: str, nuclio_url: str | None = None) -> BaseRunner:
    """Build the runner named in settings.

    ``local`` runs scripts on this machine. ``nuclio`` sends them to the Nuclio
    runner at ``nuclio_url``.

    Raises:
        ValueError: If the runner name is unknown or ``nuclio_url`` is missing.
    """
    if runner == "local":
        return LocalRunner()
    if runner == "nuclio":
        if not nuclio_url:
            raise ValueError(
                "NUCLIO_RUNNER_URL must be set when FUNCTION_RUNNER=nuclio"
            )
        return NuclioRunner(nuclio_url)
    raise ValueError(f"Unsupported FUNCTION_RUNNER: {runner}")
