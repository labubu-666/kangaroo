from kangaroo.settings import Settings


def test_database_url_defaults_to_sqlite_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    assert Settings(_env_file=None).database_url == "sqlite://memory"


def test_database_url_read_from_env_file(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-only")
    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=sqlite:///kangaroo.db\n")
    assert Settings(_env_file=env_file).database_url == "sqlite:///kangaroo.db"


def test_database_url_read_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://memory")
    assert Settings().database_url == "sqlite://memory"
