from kangaroo.repositories import (
    BoardRepository,
    ProjectRepository,
    StatusRepository,
    WorkItemRepository,
)
from kangaroo.schemas import (
    ReportSummary,
    StatusCount,
    WorkItemCounts,
)


class ReportService:
    """Headline counts across the whole store, for the dashboard."""

    def __init__(
        self,
        work_items: WorkItemRepository,
        projects: ProjectRepository,
        boards: BoardRepository,
        statuses: StatusRepository,
    ) -> None:
        self._work_items = work_items
        self._projects = projects
        self._boards = boards
        self._statuses = statuses

    def summary(self) -> ReportSummary:
        """Count projects, boards and work items, split by status and category."""
        counts = self._work_items.count_by("status_id", trashed=False)
        by_status = [
            StatusCount(status=status, count=counts.get(status.id, 0))
            for status in self._statuses.list_all()
        ]
        per_category = {"todo": 0, "in_progress": 0, "done": 0}
        for entry in by_status:
            per_category[entry.status.category] += entry.count
        return ReportSummary(
            projects=self._projects.count(),
            boards=self._boards.count(),
            work_items=WorkItemCounts(
                total=self._work_items.count(trashed=False),
                by_status=by_status,
                **per_category,
            ),
        )
