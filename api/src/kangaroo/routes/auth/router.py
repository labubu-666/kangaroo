from typing import Annotated, Any

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from itsdangerous import BadData, URLSafeTimedSerializer
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from kangaroo.repositories import ApiKeyRepository
from kangaroo.routes.dependencies import get_engine
from kangaroo.schemas import MAX_RUN_TIMEOUT_SECONDS
from kangaroo.services.api_keys import API_KEY_PREFIX, api_key_claims, hash_api_key
from kangaroo.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])
DEFAULT_NEXT = "/web/"

# Impersonation tokens only need to outlive a function run, plus HTTP slack.
IMPERSONATION_TOKEN_MAX_AGE = MAX_RUN_TIMEOUT_SECONDS + 10
IMPERSONATION_TOKEN_SALT = "kangaroo-impersonation-token"
_impersonation_serializer = URLSafeTimedSerializer(
    settings.session_secret_key.get_secret_value(), salt=IMPERSONATION_TOKEN_SALT
)


def create_impersonation_token(user: dict[str, Any]) -> str:
    """Sign a short-lived token that lets a function run call the API as ``user``."""
    # api_key_id carries over so a run started with an API key cannot manage keys.
    keys = ("sub", "email", "name", "api_key_id")
    claims = {key: user[key] for key in keys if key in user}
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


def _user_from_api_key(request: Request, engine: Engine) -> dict[str, Any] | None:
    """Return the owner of a valid ``kg_`` API key sent as a bearer token.

    Recording the key's use commits in its own transaction. Done in the request's
    transaction, it would hold SQLite's write lock until the request ends, and a
    function run's own writes would fail with "database is locked".
    """
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.startswith(API_KEY_PREFIX):
        return None
    with Session(engine) as session, session.begin():
        row = ApiKeyRepository(session).authenticate(hash_api_key(token))
        return api_key_claims(row) if row else None


def require_user(
    request: Request,
    engine: Annotated[Engine, Depends(get_engine)],
) -> dict[str, Any]:
    """Accept a Dex session, an API key or an impersonation token; otherwise 401."""
    user = (
        request.session.get("user")
        or _user_from_api_key(request, engine)
        or _user_from_bearer(request)
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user


oauth = OAuth()
oauth.register(
    name="dex",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret.get_secret_value(),
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


@router.get("/callback")
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
