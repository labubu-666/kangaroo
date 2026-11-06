import pytest


@pytest.fixture
def project_id(seeded):
    return seeded.project_id
