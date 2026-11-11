import click
import uvicorn

from kangaroo.jobs import build_scheduler
from kangaroo.repositories import create_engine_for
from kangaroo.settings import settings


@click.group()
def cli() -> None:
    """Kangaroo CLI."""


@cli.command()
@click.option("--host", default="127.0.0.1", help="Server host.")
@click.option("--port", default=8000, type=int, help="Server port.")
@click.option(
    "--reload/--no-reload", default=False, help="Enable auto-reload on file changes."
)
@click.option("--log-level", default="info", help="Logging level.")
def serve(host: str, port: int, reload: bool, log_level: str) -> None:
    """Serve the FastAPI application."""
    uvicorn.run(
        "kangaroo.app:app", host=host, port=port, reload=reload, log_level=log_level
    )


@cli.command()
def worker() -> None:
    """Run background jobs. Blocks until stopped."""
    build_scheduler(create_engine_for(settings.database_url)).start()
