from fastapi import APIRouter, Depends

from kangaroo.routes.dependencies import get_report_service
from kangaroo.schemas import ReportSummary
from kangaroo.services import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummary)
def get_summary(service: ReportService = Depends(get_report_service)) -> ReportSummary:
    """Get headline counts: projects, boards and work items by status."""
    return service.summary()
