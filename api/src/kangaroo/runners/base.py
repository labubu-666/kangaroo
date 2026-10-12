from abc import ABC, abstractmethod

from kangaroo.schemas import RunRequest, RunResult


class BaseRunner(ABC):
    """Runs a Python script and reports its output.

    Every runner takes a ``RunRequest`` and returns a ``RunResult``, so callers do
    not depend on where the script runs.
    """

    @abstractmethod
    def run(self, request: RunRequest) -> RunResult:
        """Run the script and return what it printed and how it exited.

        A run that exceeds ``request.timeout_seconds`` returns exit code -1.

        Raises:
            RunnerUnavailableError: If the runner cannot be reached.
        """
