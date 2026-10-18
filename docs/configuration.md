# Configuration

Settings are read from environment variables or `api/.env`. Variable names are
the field names in upper case.

| Variable | Default | Description |
| --- | --- | --- |
| `ENV` | `production` | Environment name. `development` proxies `/web` to the Vite dev server; anything else serves `web/dist`. |
| `DATABASE_URL` | `sqlite://memory` | Database URL. `sqlite://memory` is an in-memory database; `sqlite:///path.db` is a file. |
| `FUNCTION_RUNNER` | `local` | Where saved functions run. `local` runs them on the API host; `nuclio` runs them in the Nuclio runner at `NUCLIO_RUNNER_URL`. |
| `NUCLIO_RUNNER_URL` | unset | URL of the Nuclio runner. Required when `FUNCTION_RUNNER=nuclio`. |
| `SESSION_SECRET_KEY` | `dev-only-change-me` | Signs the session cookie. Use a long random value in every deployed environment. |
| `OIDC_METADATA_URL` | `http://localhost:5556/dex/.well-known/openid-configuration` | Dex's `.well-known/openid-configuration` URL. |
| `OIDC_CLIENT_ID` | `fastapi-app` | Client ID registered in Dex. |
| `OIDC_CLIENT_SECRET` | `a-safe-password` | Client secret registered in Dex. |
| `OIDC_REDIRECT_URI` | `http://localhost:8000/auth/callback` | Callback URL, which must be `/auth/callback` on the API. |

See [Authentication](./auth) for how the OIDC settings fit together.
