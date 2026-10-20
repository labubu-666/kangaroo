from fastapi import APIRouter, Depends

from kangaroo.routes.articles import router as articles_router
from kangaroo.routes.auth import require_user
from kangaroo.routes.boards import router as boards_router
from kangaroo.routes.docs import router as docs_router
from kangaroo.routes.functions import router as functions_router
from kangaroo.routes.invocations import router as invocations_router
from kangaroo.routes.knowledge_bases import router as knowledge_bases_router
from kangaroo.routes.project_templates import router as project_templates_router
from kangaroo.routes.projects import router as projects_router
from kangaroo.routes.reports import router as reports_router
from kangaroo.routes.user import router as user_router
from kangaroo.routes.work_items import router as work_items_router
from kangaroo.routes.workflow import (
    statuses_router,
    transitions_router,
    work_item_types_router,
)

api_v1_router = APIRouter(dependencies=[Depends(require_user)])
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
api_v1_router.include_router(articles_router)
api_v1_router.include_router(knowledge_bases_router)
api_v1_router.include_router(invocations_router)
api_v1_router.include_router(user_router)

__all__ = ["api_v1_router"]
