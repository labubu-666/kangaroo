# Authentication

Kangaroo signs users in through [Dex](https://dexidp.io), an OpenID Connect
provider. Everything under `/api/v1` requires a logged-in user, including the
docs. `/health` stays open.

## How login works

1. The browser opens `/auth/login`. If the user came from a page, that page is
   remembered so the user lands back on it after login.
2. The API redirects to Dex, where the user logs in.
3. Dex redirects to `/auth/callback`. The API exchanges the code for the
   user's details and stores them in a signed session cookie.
4. The user is sent back to the page they came from, or to `/web/`.

Logging out happens at `POST /auth/logout`, which clears the session. The web UI
does this from the profile menu.

If Dex can't be reached, `/auth/login` returns `503`.

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

## Machine access with API keys

Scripts and services outside Kangaroo can call the API with an API key. Create
one on the **API keys** page (profile menu, then API keys), or send
`POST /api/v1/api-keys/` while logged in:

```sh
curl -X POST https://kangaroo.example.com/api/v1/api-keys/ \
  -H "Content-Type: application/json" \
  -d '{"name": "nightly-import"}'
```

The response includes `key`, which starts with `kg_`. It is shown only once, so
store it somewhere safe. Send it as a bearer token:

```sh
curl https://kangaroo.example.com/api/v1/work-items \
  -H "Authorization: Bearer kg_..."
```

- A key acts as the user who created it, with that user's permissions.
- Keys can be given an `expires_at` time. Expired keys are rejected.
- Revoke a key with `DELETE /api/v1/api-keys/{id}`, or on the API keys page.
  Revoked keys are rejected straight away.
- A key cannot create, list or revoke API keys. Those calls need a login.
- Kangaroo stores only a SHA-256 hash of each key, so a lost key cannot be
  recovered. Create a new one instead.

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
