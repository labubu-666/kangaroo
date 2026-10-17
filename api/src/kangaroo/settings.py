from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SESSION_SECRET_KEY = "dev-only-change-me"


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

    # OpenID Connect login via Dex. The session key signs the session cookie.
    session_secret_key: str = DEV_SESSION_SECRET_KEY
    oidc_metadata_url: str = (
        "http://localhost:5556/dex/.well-known/openid-configuration"
    )
    oidc_client_id: str = "fastapi-app"
    oidc_client_secret: str = "a-safe-password"
    oidc_redirect_uri: str = "http://localhost:8000/auth/callback"

    @model_validator(mode="after")
    def require_session_secret_key_outside_development(self) -> "Settings":
        if (
            self.env.lower() != "development"
            and self.session_secret_key == DEV_SESSION_SECRET_KEY
        ):
            raise ValueError("SESSION_SECRET_KEY must be set outside development")
        return self


settings = Settings()
