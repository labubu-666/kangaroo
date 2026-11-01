from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from kangaroo.routes.auth import require_user
from kangaroo.routes.dependencies import ApiKeyServiceDep
from kangaroo.schemas import ApiKey, ApiKeyCreate, ApiKeyCreated

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def require_interactive_user(
    user: Annotated[dict[str, Any], Depends(require_user)],
) -> dict[str, Any]:
    """Refuse API key callers, so a leaked key cannot mint or revoke other keys."""
    if "api_key_id" in user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API keys cannot manage API keys",
        )
    return user


CurrentUserDep = Annotated[dict[str, Any], Depends(require_interactive_user)]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ApiKeyCreated)
def create_api_key(
    item: ApiKeyCreate,
    service: ApiKeyServiceDep,
    user: CurrentUserDep,
) -> ApiKeyCreated:
    """Create an API key that acts as you. The key is shown only in this response."""
    return service.create(user, item)


@router.get("/", response_model=list[ApiKey])
def list_api_keys(service: ApiKeyServiceDep, user: CurrentUserDep) -> list[ApiKey]:
    """List your API keys that have not been revoked. The secrets are not returned."""
    return service.list_for(user)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    item_id: UUID, service: ApiKeyServiceDep, user: CurrentUserDep
) -> None:
    """Revoke one of your API keys. Requests using it fail from then on."""
    service.revoke(item_id, user)
