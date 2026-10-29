from typing import Any

from fastapi import APIRouter

from kangaroo.settings import settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/")
def get_settings() -> dict[str, Any]:
    """Dump the current settings for troubleshooting. Secrets show as asterisks."""
    return settings.model_dump(mode="json")
