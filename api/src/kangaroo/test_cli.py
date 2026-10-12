from click.testing import CliRunner

from kangaroo.cli import cli


def test_serve_default_options(monkeypatch):
    """Test serve command with default options."""
    calls = []

    def mock_run(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr("kangaroo.cli.uvicorn.run", mock_run)

    runner = CliRunner()
    result = runner.invoke(cli, ["serve"])

    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0][0] == ("kangaroo.app:app",)
    assert calls[0][1] == {
        "host": "127.0.0.1",
        "port": 8000,
        "reload": False,
        "log_level": "info",
    }


def test_serve_custom_options(monkeypatch):
    """Test serve command with custom options."""
    calls = []

    def mock_run(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr("kangaroo.cli.uvicorn.run", mock_run)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "serve",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--reload",
            "--log-level",
            "debug",
        ],
    )

    assert result.exit_code == 0
    assert len(calls) == 1
    assert calls[0][0] == ("kangaroo.app:app",)
    assert calls[0][1] == {
        "host": "0.0.0.0",
        "port": 9000,
        "reload": True,
        "log_level": "debug",
    }
