from fastapi import APIRouter

from kangaroo.routes.dependencies import ReportServiceDep
from kangaroo.schemas import ReportSummary

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummary)
def get_summary(service: ReportServiceDep) -> ReportSummary:
    """Get headline counts: projects, boards and work items by status."""
    return service.summary()
