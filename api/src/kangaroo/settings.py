from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables and ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "development" proxies /web to the Vite dev server; anything else serves web/dist.
    env: str = "production"

    # memory:// selects the in-memory backends, sqlite://... the SQLite backends.
    database_url: str = "memory://"

    # Where saved functions run: "local" on this machine, or "nuclio" in the
    # deployed Nuclio runner at nuclio_runner_url.
    function_runner: str = "local"
    nuclio_runner_url: str | None = None


settings = Settings()
