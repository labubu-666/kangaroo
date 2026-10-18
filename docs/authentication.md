# Authentication

Kangaroo signs users in through [Dex](https://dexidp.io), an OpenID Connect
provider. Everything under `/api/v1` requires a logged-in user, including the
docs. `/health` stays open.

## How login works

1. The browser opens `/login`. If the user came from a page, that page is
   remembered so the user lands back on it after login.
2. The API redirects to Dex, where the user logs in.
3. Dex redirects to `/auth/callback`. The API exchanges the code for the
   user's details and stores them in a signed session cookie.
4. The user is sent back to the page they came from, or to `/web/`.

Logging out happens at `POST /logout`, which clears the session. The web UI
does this from the profile menu.

If Dex can't be reached, `/login` returns `503`.

## Local setup

1. Copy `dex/config.dist.yaml` to `dex/config.yaml`.
2. Replace the placeholder password hash. The command to generate one is in
   the file. Dex also keeps its GitHub connector, which needs real credentials
   before it can be used.
3. Start Dex with `docker compose up dex`. Log in with the static user from the
   config file.

`dex/config.yaml` is ignored by git, so it stays local.

## Calling the API from a function

Functions run with two extra environment variables:

- `KANGAROO_API_URL`: the base URL of the API (`API_PUBLIC_URL`).
- `KANGAROO_TOKEN`: a signed impersonation token for the user who ran the function.

Send the token as a bearer header:

```python
import os

import httpx

httpx.get(
    f"{os.environ['KANGAROO_API_URL']}/api/v1/work-items",
    headers={"Authorization": f"Bearer {os.environ['KANGAROO_TOKEN']}"},
)
```

An impersonation token is created for each run and is valid for 25 seconds from
creation, which covers the run's 15-second limit plus a margin. The script
impersonates the user who ran it, with the same permissions.

## Settings

These are read from environment variables or `api/.env`.

| Setting | Purpose |
| --- | --- |
| `SESSION_SECRET_KEY` | Signs the session cookie. Required unless `ENV=development`, where a built-in dev value is used. Use a long random value in every deployed environment. |
| `OIDC_METADATA_URL` | Dex's `.well-known/openid-configuration` URL. |
| `OIDC_CLIENT_ID` | Client ID registered in Dex. |
| `OIDC_CLIENT_SECRET` | Client secret registered in Dex. |
| `OIDC_REDIRECT_URI` | Callback URL, which must be `/auth/callback` on the API. |
| `API_PUBLIC_URL` | Base URL function scripts use to call the API. Must be reachable from the runner (for Nuclio, not `localhost` unless the runner shares the host network). |

The client ID, client secret and redirect URI must match the `staticClients`
entry in `dex/config.yaml`.
