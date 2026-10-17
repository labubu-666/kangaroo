from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables and ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "development" proxies /web to the Vite dev server; anything else serves web/dist.
    env: str = "production"

    # sqlite://memory is an in-memory database; sqlite:///path.db is a file.
    database_url: str = "sqlite://memory"

    # Where saved functions run: "local" on this machine, or "nuclio" in the
    # deployed Nuclio runner at nuclio_runner_url.
    function_runner: str = "local"
    nuclio_runner_url: str | None = None


settings = Settings()
