from typing import Any

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from itsdangerous import BadData, URLSafeTimedSerializer

from kangaroo.schemas import MAX_RUN_TIMEOUT_SECONDS
from kangaroo.settings import settings

router = APIRouter()
DEFAULT_NEXT = "/web/"

# Impersonation tokens only need to outlive a function run, plus HTTP slack.
IMPERSONATION_TOKEN_MAX_AGE = MAX_RUN_TIMEOUT_SECONDS + 10
IMPERSONATION_TOKEN_SALT = "kangaroo-impersonation-token"
_impersonation_serializer = URLSafeTimedSerializer(
    settings.session_secret_key, salt=IMPERSONATION_TOKEN_SALT
)


def create_impersonation_token(user: dict[str, Any]) -> str:
    """Sign a short-lived token that lets a function run call the API as ``user``."""
    claims = {key: user[key] for key in ("sub", "email", "name") if key in user}
    return _impersonation_serializer.dumps(claims)


def _user_from_bearer(request: Request) -> dict[str, Any] | None:
    """Return the user in a valid, unexpired ``Authorization: Bearer`` impersonation token."""
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        return _impersonation_serializer.loads(
            token, max_age=IMPERSONATION_TOKEN_MAX_AGE
        )
    except BadData:
        return None


def require_user(request: Request) -> dict[str, Any]:
    """Accept a logged-in Dex session or an impersonation token; otherwise return 401."""
    user = request.session.get("user") or _user_from_bearer(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


oauth = OAuth()
oauth.register(
    name="dex",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.oidc_metadata_url,
    client_kwargs={"scope": "openid profile email"},
)


@router.get("/login")
async def login(request: Request, next: str = DEFAULT_NEXT) -> RedirectResponse:
    """Send the user to Dex to log in, then back to `next` (a path under /web/)."""
    is_safe = next.startswith("/web/") and not next.startswith("//")
    request.session["next"] = next if is_safe else DEFAULT_NEXT
    try:
        return await oauth.dex.authorize_redirect(request, settings.oidc_redirect_uri)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Login provider unavailable",
        ) from exc


@router.get("/auth/callback")
async def auth_callback(request: Request) -> RedirectResponse:
    """Exchange the Dex code for tokens and store the user in the session."""
    try:
        token = await oauth.dex.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Login failed"
        ) from exc
    request.session["user"] = token.get("userinfo")
    return RedirectResponse(url=request.session.pop("next", DEFAULT_NEXT))


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Clear the session and return to the web UI."""
    request.session.clear()
    return RedirectResponse(url="/web/", status_code=status.HTTP_303_SEE_OTHER)
