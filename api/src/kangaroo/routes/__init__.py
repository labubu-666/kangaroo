from fastapi import APIRouter

from kangaroo.routes.boards import router as boards_router
from kangaroo.routes.docs import router as docs_router
from kangaroo.routes.functions import router as functions_router
from kangaroo.routes.project_templates import router as project_templates_router
from kangaroo.routes.projects import router as projects_router
from kangaroo.routes.reports import router as reports_router
from kangaroo.routes.work_items import router as work_items_router
from kangaroo.routes.workflow import (
    statuses_router,
    transitions_router,
    work_item_types_router,
)

api_v1_router = APIRouter()
api_v1_router.include_router(work_items_router)
api_v1_router.include_router(projects_router)
api_v1_router.include_router(boards_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(docs_router)
api_v1_router.include_router(project_templates_router)
api_v1_router.include_router(statuses_router)
api_v1_router.include_router(work_item_types_router)
api_v1_router.include_router(transitions_router)
api_v1_router.include_router(functions_router)

__all__ = ["api_v1_router"]
