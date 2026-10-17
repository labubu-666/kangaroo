import hashlib
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from kangaroo.routes.auth import require_user
from kangaroo.schemas import CurrentUser

router = APIRouter(prefix="/user", tags=["user"])


def gravatar_url(email: str) -> str:
    """Gravatar image for an email; falls back to an identicon if none is set."""
    digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()
    return f"https://gravatar.com/avatar/{digest}?d=identicon&s=64"


@router.get("", response_model=CurrentUser)
def get_current_user(
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> CurrentUser:
    """Get the logged-in user's username and email, plus their Gravatar."""
    email = user.get("email")
    username = user.get("preferred_username") or user.get("name") or email or ""
    return CurrentUser(
        username=username,
        email=email,
        avatar_url=gravatar_url(email or ""),
    )
