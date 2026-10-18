import pytest

from kangaroo.settings import Settings


def test_database_url_defaults_to_sqlite_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    assert Settings(_env_file=None, env="development").database_url == "sqlite://memory"


def test_database_url_read_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=sqlite:///kangaroo.db\n")
    settings = Settings(_env_file=env_file, env="development")
    assert settings.database_url == "sqlite:///kangaroo.db"


def test_default_oidc_secret_used_when_unset(monkeypatch):
    """The built-in OIDC client secret is used when none is passed."""
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    settings = Settings(_env_file=None, env="production")
    assert settings.oidc_client_secret == "a-safe-password"


def test_custom_oidc_secret_is_used(monkeypatch):
    """A passed OIDC client secret is used as-is."""
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    settings = Settings(
        _env_file=None, env="production", oidc_client_secret="a-real-secret"
    )
    assert settings.oidc_client_secret == "a-real-secret"


def test_local_runner_is_default(monkeypatch):
    """FUNCTION_RUNNER defaults to local."""
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    assert Settings(_env_file=None).function_runner == "local"


def test_nuclio_runner_is_used_when_set(monkeypatch):
    """A passed FUNCTION_RUNNER is used as-is."""
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    settings = Settings(
        _env_file=None,
        env="production",
        function_runner="nuclio",
        nuclio_runner_url="http://runner",
    )
    assert settings.function_runner == "nuclio"


def test_database_url_read_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://memory")
    assert Settings().database_url == "sqlite://memory"
