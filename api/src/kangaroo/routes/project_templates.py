from fastapi import APIRouter
from pydantic import BaseModel

from kangaroo.templates import DEFAULT_TEMPLATE_NAME, TEMPLATES

router = APIRouter(prefix="/project-templates", tags=["project-templates"])


class ProjectTemplateList(BaseModel):
    """The templates a new project can be created from, and the default one."""

    default: str
    names: list[str]


@router.get("/", response_model=ProjectTemplateList)
def list_project_templates() -> ProjectTemplateList:
    """List the project templates. The first one is the default."""
    return ProjectTemplateList(default=DEFAULT_TEMPLATE_NAME, names=list(TEMPLATES))
