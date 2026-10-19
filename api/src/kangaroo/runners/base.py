from abc import ABC, abstractmethod

from kangaroo.schemas import RunRequest, RunResult


class BaseRunner(ABC):
    """Runs a Python script and reports its output.

    Every runner takes a ``RunRequest`` and returns a ``RunResult``, so callers do
    not depend on where the script runs.
    """

    @abstractmethod
    def run(self, request: RunRequest) -> RunResult:
        """Run the script and return its logs, its result and its status.

        A run that exceeds ``request.timeout_seconds`` returns ERROR.

        Raises:
            RunnerUnavailableError: If the runner cannot be reached.
        """
