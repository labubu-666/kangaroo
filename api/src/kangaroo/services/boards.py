from typing import Any
from uuid import UUID

from kangaroo.backends import (
    BoardBackend,
    ProjectBackend,
    StatusBackend,
    WorkItemBackend,
    WorkItemTypeBackend,
)
from kangaroo.backends.base import clean_search, matches_search
from kangaroo.filters import parse_filter
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
    _detail,
    _ensure_project_exists,
    _filter_record,
    _in_position_order,
    _lookups,
    _project_names,
)


def _board_record(board: Board, project_names: dict[UUID, str]) -> dict[str, Any]:
    """Flatten a board into the record that filter predicates read.

    A board's name is its ``title``. Work-item-only fields are None, so a filter
    on them never matches a board.
    """
    return {
        "title": board.name,
        "description": board.description,
        "status": None,
        "status_id": None,
        "statusCategory": None,
        "type": None,
        "type_id": None,
        "typeLevel": None,
        "parent_id": None,
        "project.id": str(board.project_id),
        "project.name": project_names.get(board.project_id),
        "labels": [],
        "trashed": None,
    }


class BoardService:
    """Business rules for boards.

    A board belongs to a project and must reference an existing one. Its filter
    is checked when it is saved, so a board never holds an invalid filter. Its
    view groups the matching work items of its project by status.
    """

    def __init__(
        self,
        boards: BoardBackend,
        work_items: WorkItemBackend,
        projects: ProjectBackend,
        statuses: StatusBackend,
        types: WorkItemTypeBackend,
    ) -> None:
        self._boards = boards
        self._work_items = work_items
        self._projects = projects
        self._statuses = statuses
        self._types = types

    def create(self, item: BoardCreate) -> Board:
        """Create a board after checking its project and filter."""
        _ensure_project_exists(self._projects, item.project_id)
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
        matches = parse_filter(filter)
        project_names = _project_names(self._projects)
        candidates = self._boards.list_all(project_id=project_id)
        text = clean_search(search)
        fields = self._boards.search_fields
        matched = [
            board
            for board in candidates
            if matches(_board_record(board, project_names))
            and (text is None or matches_search(board, text, fields))
        ]
        return PaginatedResponse[Board](
            results=matched[offset : offset + limit],
            limit=limit,
            offset=offset,
            total=len(matched),
        )

    def get(self, item_id: UUID) -> Board:
        """Get a board by ID."""
        return self._boards.get_by_id(item_id)

    def update(self, item_id: UUID, update: BoardUpdate) -> Board:
        """Update a board (partial update) after checking its project and filter."""
        if "project_id" in update.model_fields_set:
            _ensure_project_exists(self._projects, update.project_id)
        if "filter" in update.model_fields_set:
            parse_filter(update.filter)
        return self._boards.update(item_id, update)

    def replace(self, item_id: UUID, replace: BoardReplace) -> Board:
        """Replace a board (full update) after checking its project and filter."""
        _ensure_project_exists(self._projects, replace.project_id)
        parse_filter(replace.filter)
        return self._boards.replace(item_id, replace)

    def delete(self, item_id: UUID) -> None:
        """Delete a board."""
        self._boards.delete(item_id)

    def view(self, item_id: UUID) -> BoardView:
        """Return the board with its project's matching work items grouped by status.

        Every status of the project is a column, in position order, even when it
        has no work items.
        """
        board = self._boards.get_by_id(item_id)
        matches = parse_filter(board.filter)
        project_names = _project_names(self._projects)
        statuses, types = _lookups(self._statuses, self._types)
        project_statuses = _in_position_order(
            self._statuses.list_all(project_id=board.project_id)
        )
        columns: dict[UUID, list[WorkItemDetail]] = {
            status.id: [] for status in project_statuses
        }
        for item in self._work_items.list_all(
            project_id=board.project_id, trashed=False
        ):
            if matches(_filter_record(item, project_names, statuses, types)):
                columns[item.status_id].append(_detail(item, statuses, types))
        return BoardView(
            board=board,
            columns=[
                BoardColumn(status=status, items=columns[status.id])
                for status in project_statuses
            ],
        )
