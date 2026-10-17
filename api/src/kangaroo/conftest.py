import os

# The app reads DATABASE_URL when its backends are first used. Point it at an
# in-memory database before any test runs.
os.environ["DATABASE_URL"] = "sqlite://memory"

import pytest

from kangaroo.backends import Backends, create_backends


@pytest.fixture
def backends() -> Backends:
    """Fresh, empty backends on a new in-memory database for each test."""
    return create_backends("sqlite://memory")
