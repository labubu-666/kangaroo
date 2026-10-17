"""Helpers for tests that need a project's statuses and types.

Work items refer to a project's own statuses and types by ID, so tests look
the IDs up by name instead of hard-coding them.
"""

from dataclasses import dataclass
from uuid import UUID

from kangaroo.schemas import (
    ProjectCreate,
    StatusCreate,
    WorkItemCreate,
    WorkItemTypeCreate,
)
from kangaroo.templates import TO_DO_LIST

NAMES = {
    "task": "Task",
    "subtask": "Subtask",
    "open": "Open",
    "in_progress": "In Progress",
    "done": "Done",
}


def type_id(client, project_id, key: str) -> str:
    """The ID of a project's work item type: ``task`` or ``subtask``."""
    response = client.get(f"/api/v1/work-item-types/?project_id={project_id}")
    return next(t["id"] for t in response.json() if t["name"] == NAMES[key])


def status_id(client, project_id, key: str) -> str:
    """The ID of a project's status: ``open``, ``in_progress`` or ``done``."""
    response = client.get(f"/api/v1/statuses/?project_id={project_id}")
    return next(s["id"] for s in response.json() if s["name"] == NAMES[key])


@dataclass(frozen=True)
class SeededProject:
    """A project with the "To Do List" statuses and types, and their IDs."""

    project_id: UUID
    task_id: UUID
    subtask_id: UUID
    open_id: UUID
    in_progress_id: UUID
    done_id: UUID


def seed_project(projects, statuses, types, name: str = "Test") -> SeededProject:
    """Create a project and copy the "To Do List" template into the repositories."""
    project = projects.create(ProjectCreate(name=name))
    type_ids = {
        t.name: types.create(
            WorkItemTypeCreate(
                project_id=project.id, name=t.name, level=t.level, position=t.position
            )
        ).id
        for t in TO_DO_LIST.types
    }
    status_ids = {
        s.name: statuses.create(
            StatusCreate(
                project_id=project.id,
                name=s.name,
                category=s.category,
                position=s.position,
            )
        ).id
        for s in TO_DO_LIST.statuses
    }
    return SeededProject(
        project_id=project.id,
        task_id=type_ids["Task"],
        subtask_id=type_ids["Subtask"],
        open_id=status_ids["Open"],
        in_progress_id=status_ids["In Progress"],
        done_id=status_ids["Done"],
    )


def new_task(seeded: SeededProject, title: str = "Task", **extra) -> WorkItemCreate:
    """A task create request in the first To Do status, ready for a repository."""
    extra.setdefault("status_id", seeded.open_id)
    return WorkItemCreate(
        title=title, project_id=seeded.project_id, type_id=seeded.task_id, **extra
    )


def new_subtask(
    seeded: SeededProject, parent_id: UUID, title: str = "Child", **extra
) -> WorkItemCreate:
    """A subtask create request in the first To Do status, ready for a repository."""
    extra.setdefault("status_id", seeded.open_id)
    return WorkItemCreate(
        title=title,
        project_id=seeded.project_id,
        type_id=seeded.subtask_id,
        parent_id=parent_id,
        **extra,
    )
