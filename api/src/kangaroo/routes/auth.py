from typing import Any

import httpx
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from kangaroo.settings import settings

router = APIRouter()
DEFAULT_NEXT = "/web/"


def require_user(request: Request) -> dict[str, Any]:
    """Reject the request with 401 unless a user has logged in via Dex."""
    user = request.session.get("user")
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
