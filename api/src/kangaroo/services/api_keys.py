import hashlib
import secrets
from typing import Any
from uuid import UUID

from kangaroo.errors import NotFoundError
from kangaroo.repositories import ApiKeyRepository
from kangaroo.repositories.tables import ApiKeyRow
from kangaroo.schemas import ApiKey, ApiKeyCreate, ApiKeyCreated

API_KEY_PREFIX = "kg_"


def hash_api_key(key: str) -> str:
    """Hash a key for storage. A key is random, so a fast hash is enough."""
    return hashlib.sha256(key.encode()).hexdigest()


def owner_id(user: dict[str, Any]) -> str:
    """The stable ID that ties a key to its owner, from the logged-in user's claims."""
    owner = user.get("sub") or user.get("email")
    if not owner:
        raise ValueError("The logged-in user has no sub or email to own a key")
    return owner


class ApiKeyService:
    """Creates, lists and revokes the API keys a user owns."""

    def __init__(self, api_keys: ApiKeyRepository) -> None:
        self._api_keys = api_keys

    def create(self, user: dict[str, Any], item: ApiKeyCreate) -> ApiKeyCreated:
        key = API_KEY_PREFIX + secrets.token_urlsafe(32)
        row = self._api_keys.create(
            name=item.name,
            key_hash=hash_api_key(key),
            owner=owner_id(user),
            owner_email=user.get("email"),
            owner_name=user.get("name"),
            expires_at=item.expires_at,
        )
        return ApiKeyCreated(
            **ApiKey.model_validate(row, from_attributes=True).model_dump(), key=key
        )

    def list_for(self, user: dict[str, Any]) -> list[ApiKey]:
        return [
            ApiKey.model_validate(row, from_attributes=True)
            for row in self._api_keys.list_active(owner_id(user))
        ]

    def revoke(self, item_id: UUID, user: dict[str, Any]) -> None:
        if not self._api_keys.revoke(item_id, owner_id(user)):
            raise NotFoundError(f"API key {item_id} not found")


def api_key_claims(row: ApiKeyRow) -> dict[str, Any]:
    """The user claims a request gets when it authenticates with this key."""
    return {
        "sub": row.owner,
        "email": row.owner_email,
        "name": row.owner_name,
        "api_key_id": str(row.id),
    }
