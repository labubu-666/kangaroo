from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SESSION_SECRET_KEY = "dev-only-change-me"
OIDC_CLIENT_SECRET = "a-safe-password"


class Settings(BaseSettings):
    """Application settings, read from environment variables and ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "development" proxies /web to the Vite dev server; anything else serves web/dist.
    env: str = "production"

    # sqlite://memory is an in-memory database; sqlite:///path.db is a file.
    database_url: str = "sqlite://memory"

    # Upper limit on the total uncompressed size of a restored backup. Guards
    # against zip bombs that would fill the disk when extracted.
    backup_max_uncompressed_bytes: int = 10 * 1024**3

    # Where saved functions run: "local" on this machine, or "nuclio" in the
    # deployed Nuclio runner at nuclio_runner_url.
    function_runner: str = "local"
    nuclio_runner_url: str | None = None

    # Base URL that function scripts use to call this API. Scripts run in other
    # containers when FUNCTION_RUNNER=nuclio, so set this to an address they can reach.
    api_public_url: str = "http://localhost:8000"

    # OpenID Connect login via Dex. The session key signs the session cookie.
    session_secret_key: SecretStr = SecretStr(SESSION_SECRET_KEY)
    oidc_metadata_url: str = (
        "http://localhost:5556/dex/.well-known/openid-configuration"
    )
    oidc_client_id: str = "fastapi-app"
    oidc_client_secret: SecretStr = SecretStr(OIDC_CLIENT_SECRET)
    oidc_redirect_uri: str = "http://localhost:8000/auth/callback"


settings = Settings()
