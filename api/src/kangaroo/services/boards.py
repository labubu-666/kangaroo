import logging
from collections.abc import Callable
from typing import Any
from uuid import UUID

from kangaroo.errors import InvalidFilterError
from kangaroo.filters import parse_filter
from kangaroo.repositories import (
    BoardRepository,
    ProjectRepository,
    StatusRepository,
    WorkItemRepository,
    WorkItemTypeRepository,
)
from kangaroo.schemas import (
    Board,
    BoardColumn,
    BoardCreate,
    BoardReplace,
    BoardUpdate,
    BoardView,
    PaginatedResponse,
    WorkItemDetail,
)
from kangaroo.services.helpers import (
    detail,
    ensure_project_exists,
    filter_record,
    filtered_page,
    in_position_order,
    lookups,
    make_record,
    project_names,
)

logger = logging.getLogger(__name__)


def _board_record(board: Board, project_names: dict[UUID, str]) -> dict[str, Any]:
    """Flatten a board into the record that filter predicates read.

    A board's name is its ``title``. Work-item-only fields are None, so a filter
    on them never matches a board.
    """
    return make_record(
        {
            "title": board.name,
            "description": board.description,
            "project.id": str(board.project_id),
            "project.name": project_names.get(board.project_id),
            "labels": [],
        }
    )


class BoardService:
    """Business rules for boards.

    A board belongs to a project and must reference an existing one. Its filter
    is checked when it is saved, so a board never holds an invalid filter. Its
    view groups the matching work items of its project by status.
    """

    def __init__(
        self,
        boards: BoardRepository,
        work_items: WorkItemRepository,
        projects: ProjectRepository,
        statuses: StatusRepository,
        types: WorkItemTypeRepository,
    ) -> None:
        self._boards = boards
        self._work_items = work_items
        self._projects = projects
        self._statuses = statuses
        self._types = types

    def create(self, item: BoardCreate) -> Board:
        """Create a board after checking its project and filter."""
        ensure_project_exists(self._projects, item.project_id)
        parse_filter(item.filter)
        return self._boards.create(item)

    def list_paginated(
        self,
        limit: int,
        offset: int,
        search: str | None = None,
        project_id: UUID | None = None,
        filter: str | None = None,
    ) -> PaginatedResponse[Board]:
        """List boards with pagination, optionally only those of one project.

        With a filter, the boards are checked against it in Python first, then
        ``search`` and the page are applied to the matches.
        """
        if not filter or not filter.strip():
            return self._boards.list_paginated(
                limit, offset, search, project_id=project_id
            )
        names = project_names(self._projects)
        page, total = filtered_page(
            self._boards.list_all(project_id=project_id),
            filter,
            lambda board: _board_record(board, names),
            search,
            self._boards.search_fields,
            limit,
            offset,
        )
        return PaginatedResponse[Board](
            results=page, limit=limit, offset=offset, total=total
        )

    def get(self, item_id: UUID) -> Board:
        return self._boards.get_by_id(item_id)

    def update(self, item_id: UUID, update: BoardUpdate) -> Board:
        """Update a board (partial update) after checking its project and filter."""
        if "project_id" in update.model_fields_set:
            ensure_project_exists(self._projects, update.project_id)
        if "filter" in update.model_fields_set:
            parse_filter(update.filter)
        return self._boards.update(item_id, update)

    def replace(self, item_id: UUID, replace: BoardReplace) -> Board:
        """Replace a board (full update) after checking its project and filter."""
        ensure_project_exists(self._projects, replace.project_id)
        parse_filter(replace.filter)
        return self._boards.replace(item_id, replace)

    def delete(self, item_id: UUID) -> None:
        self._boards.delete(item_id)

    def _stored_filter(self, board: Board) -> Callable[[dict[str, Any]], bool]:
        """Compile a board's saved filter. A saved filter that no longer parses shows nothing.

        The API refuses invalid filters on save, so this only happens to rows written
        before that check existed. Logging it keeps the problem visible while the board
        still loads, so it can be edited.
        """
        try:
            return parse_filter(board.filter)
        except InvalidFilterError as exc:
            logger.warning("Board %s has an invalid filter: %s", board.id, exc)
            return lambda _record: False

    def view(self, item_id: UUID) -> BoardView:
        """Return the board with its project's matching work items grouped by status.

        Every status of the project is a column, in position order, even when it
        has no work items.
        """
        board = self._boards.get_by_id(item_id)
        matches = self._stored_filter(board)
        names = project_names(self._projects)
        statuses, types = lookups(self._statuses, self._types)
        project_statuses = in_position_order(
            self._statuses.list_all(project_id=board.project_id)
        )
        columns: dict[UUID, list[WorkItemDetail]] = {
            status.id: [] for status in project_statuses
        }
        for item in self._work_items.list_all(
            project_id=board.project_id, trashed=False
        ):
            if matches(filter_record(item, names, statuses, types)):
                columns[item.status_id].append(detail(item, statuses, types))
        return BoardView(
            board=board,
            columns=[
                BoardColumn(status=status, items=columns[status.id])
                for status in project_statuses
            ],
        )
