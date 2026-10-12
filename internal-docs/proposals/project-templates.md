# Proposal: Project templates with dynamic statuses and types

Status: Draft (iterate)

## 1. Summary

Replace the hard-coded work item statuses (`open`, `in_progress`, `done`) and types (`task`, `subtask`) with per-project definitions, in the style of Jira:

- **Status categories** (`todo`, `in_progress`, `done`) are a fixed system list. Reports, badge colours and "is it finished?" checks use the category, so they keep working whatever a project calls its statuses.
- **Statuses** belong to one project. Each has a name, a category and a position.
- **Work item types** belong to one project. Each has a name, a level (`standard` or `subtask`) and a position. Levels are a fixed system list, so the parent/subtask rules keep working whatever a project calls its types.
- **Workflow transitions** are per project and say which status can move to which. A project with no transitions allows every move.
- **Project templates** are defined in code. Creating a project copies a template once. After that the project is fully independent and has no link back to the template. Templates are not versioned and there are no migrations between template versions.

## 2. Motivation

Status and type are global today. Every project gets the same three statuses and the same two types, and the board columns, reports and filters all assume that. Teams that work differently (for example a bug tracker or a content pipeline) can't model their process.

## 3. Current state

- `api/src/kangaroo/schemas.py:19`: `Status` is a fixed `Literal`. `schemas.py:114-181`: `Task` and `SubTask` are separate models.
- `api/src/kangaroo/backends/sqlite.py:114-119`: `TaskRow` and `SubTaskRow`. `work_items.status` and `work_items.type` are plain strings with no foreign keys.
- `api/src/kangaroo/services.py:32` and `services.py:354-362`: board columns and report counts come from the fixed status list. `services.py:88-188` holds the subtask rules.
- `api/src/kangaroo/filters.py`: `status` and `type` are text fields.
- Frontend: `web/src/lib/work-items.ts`, `web/src/lib/reports.ts`, `web/src/components/shared/StatusBadge.tsx`, `TypeBadge.tsx`, `TypeIcon.tsx`.
- `sqlite.py:156`: `Base.metadata.create_all`. There are no migrations. The only upgrade step is `_add_missing_labels_column` (`sqlite.py:161`).

## 4. Concepts

| Concept | Owned by | Fixed or user-defined | Notes |
|---|---|---|---|
| Status category | System | Fixed: `todo`, `in_progress`, `done` | Used by reports, colours and "finished" checks |
| Status | Project | User-defined | Name, category, position |
| Type level | System | Fixed: `standard`, `subtask` | Used by the parent/subtask rules |
| Work item type | Project | User-defined | Name, level, position |
| Workflow transition | Project | User-defined | From status to status. None means any move is allowed |
| Project template | Code | Fixed per release | Copied once into a new project |

## 5. Data model

New tables:

- `work_item_types`: `id`, `project_id` (FK to `projects`), `name`, `level` (`standard` or `subtask`), `position`, timestamps.
- `statuses`: `id`, `project_id` (FK to `projects`), `name`, `category` (`todo`, `in_progress` or `done`), `position`, timestamps.
- `status_transitions`: `id`, `project_id` (FK to `projects`), `from_status_id` (FK to `statuses`), `to_status_id` (FK to `statuses`).

Changed table:

- `work_items`: `status` and `type` are removed. `status_id` (FK to `statuses`, NOT NULL) and `type_id` (FK to `work_item_types`, NOT NULL) are added. `parent_id` is unchanged.

The table is rebuilt during the upgrade, see §9.

## 6. Templates

- Defined in code in a new module `api/src/kangaroo/templates.py`.
- Each template has a `name`, a list of types (name, level, position), a list of statuses (name, category, position) and optionally transitions.
- The first template is **"To Do List"**, which is the current setup:

| Kind | Name | Level or category | Position |
|---|---|---|---|
| Type | Task | `standard` | 0 |
| Type | Subtask | `subtask` | 1 |
| Status | Open | `todo` | 0 |
| Status | In Progress | `in_progress` | 1 |
| Status | Done | `done` | 2 |

- Transitions: none, so any status can move to any other, as today.
- "To Do List" is the default when creating a project.
- Creating a project from a template copies its types and statuses into the new project's rows. Nothing stored refers back to the template.

## 7. API

- Create a project with an optional `template` name (default `"To Do List"`). An unknown name returns 400.
- The template is only used at creation. Updating a project does not accept a template, and an existing project can't switch templates, because projects are independent after the copy.
- Create, update and delete a project's statuses, types and transitions. Each has a `position` field, and changing it through the normal update call is how items are reordered.
- A work item's `status` and `type` are sent as ids. Each request checks that the id belongs to the work item's project.
- When a work item's status changes, a transition from the old status to the new one must exist. If the project has no transitions, every change is allowed.
- Deleting a status or type that work items still use requires a replacement id. All matching work items move to it.
- The parent/subtask rules in `services.py` check the **type level** (`subtask`) instead of the type name.
- Board columns come from the project's statuses, in position order. Every status is a column, even when it has no work items.
- Reports count work items per status and per category.
- Moving a work item to another project requires a status and a type from the new project in the same request.

## 8. Filters

- `status` matches a status by **id** or by **name**. Name matching ignores case and treats `_`, `-` and spaces as the same, so `in_progress`, `In Progress` and `in-progress` all match.
- `type` works the same way for work item types.
- New fields: `statusCategory` (matches the category) and `typeLevel` (matches the level).
- Renaming a status breaks filters that use its old name. Filters that use the id keep working.
- Every saved filter in the current database keeps working after the upgrade, because the old values match the names of the "To Do List" statuses and types.

## 9. Migrating existing data (one-off upgrade at startup)

A new function, `_migrate_to_project_templates(engine)` in `sqlite.py`, runs right after `create_all`. It only runs if `work_items` still has a `status` column, so an upgraded database does nothing. It is not versioned and is not repeated for future template changes.

**Step 1: backup (required before anything else)**

- Runs only when the upgrade is about to run, so normal startups don't create backup files.
- Uses SQLite's built-in backup feature (`sqlite3.Connection.backup`), not a file copy, so changes still in the `-wal` or `-journal` files are included. This gives a consistent copy, so no separate check of the backup is needed.
- Written next to the database as `kangaroo.db.pre-project-templates-<YYYYmmddTHHMMSS>.bak`.
- If the backup fails, the upgrade stops and the app doesn't start. The original database is not touched.
- After a successful upgrade the backup path is logged. Backups are never deleted automatically.
- In-memory databases (`sqlite://memory`, used in tests) skip this step.

**Step 2: turn foreign key checks off**

- Run `PRAGMA foreign_keys=OFF`. SQLite ignores this inside a transaction, so it must come first.

**Step 3: transaction**

1. `create_all` has already created `work_item_types`, `statuses` and `status_transitions`.
2. Copy the "To Do List" types and statuses into every project.
3. Create `work_items_new` from the SQLAlchemy model, with `NOT NULL` on `type_id` and `status_id`, real foreign keys, and without the old `status` and `type` columns.
4. Fill it with `INSERT ... SELECT`, joining each project's statuses and types by the old value: `open` to Open, `in_progress` to In Progress, `done` to Done, `task` to Task, `subtask` to Subtask. A status that doesn't match goes to the project's first `todo` status and is logged as a warning.
5. `DROP TABLE work_items`, then `ALTER TABLE work_items_new RENAME TO work_items`.
6. Run `PRAGMA foreign_key_check`. If it reports anything, roll back and refuse to start.

**Step 4: turn foreign key checks back on**

- Run `PRAGMA foreign_keys=ON`.

**Restoring a backup:** stop the app, replace `kangaroo.db` with the `.bak` file, and start the app. This only works with the old app version, because the old schema is what's in the backup.

**Tests** (in `backends/test_sqlite.py`):
- Upgrading an old-schema database keeps every work item, maps statuses and types correctly, and keeps the `parent_id` links. Saved board filters return the same work items before and after.
- `foreign_key_check` finds nothing after the upgrade, and running the upgrade again changes nothing.
- A failing foreign key check rolls back and leaves the original data unchanged.
- A failed backup stops the upgrade and leaves the database unchanged. No backup is created when the upgrade doesn't run.

## 10. Frontend

- Load statuses and types from the API instead of `web/src/lib/work-items.ts`.
- Colour `StatusBadge` by category, not by status name.
- Board columns and report cards use the project's statuses.
- Filter bubbles and the create and edit forms use the project's types and statuses.
- **Template picker:** only on `web/src/routes/projects/create.tsx`, as a required select that defaults to "To Do List". The `createProject` call in `web/src/lib/projects.ts` sends the chosen `template`. The edit page (`web/src/routes/projects/$id_.edit.tsx`) does not get a template field, because a project can't change templates.
- **Statuses and types settings page:** a new route, `web/src/routes/projects/$id_.statuses.tsx`, following the naming of the existing `$id_.boards.create.tsx`. Linked from the project detail page. It manages statuses, types and transitions, and is separate from the name and description edit page.
- Deleting a status or type that is in use opens a dialog. The dialog lists the affected work item count and requires the user to pick a replacement of the same kind (status for status, type for type). The delete button stays disabled until a replacement is chosen.
- Renaming a status that saved filters use shows a warning listing those board filters.

## 11. Edge cases

Deleting and moving:

- **Deleting a status or type in use:** the user must choose a replacement. The API returns 409 if none is given.
- **Moving a work item to another project:** the user must choose a status and type in the new project.
- **Transitions that point at a deleted status:** deleted with the status.

Changing a status or type that is in use:

- **Changing a type's level:** not allowed while work items use it. The parent/subtask rules depend on the level, so changing it would break existing links. The API returns 409.
- **Changing a status's category:** allowed, even while work items use it. The status keeps its id, so work items stay attached. Reports and the board count by category on the next request, so no data is moved. The UI shows a confirmation that says how many work items will change category.
- **Renaming a status:** allowed. Filters that use the old name stop matching (see §8). The UI warns about the saved board filters that use the name. Filters that use the id keep working.

Project-level rules:

- **No status in the `done` category:** allowed, but the board and reports show a warning, since "finished" work items can't be counted.
- **No status in the `todo` category:** not allowed. New work items need a starting status, so the API returns 409 when the last `todo` status is removed or changed.
- **No subtask-level type:** allowed. Subtasks can't be created until one exists.

## 12. Out of scope

- Versioned migrations and Alembic.
- Template versioning and upgrading existing projects to a newer template.
- Per-type workflows (one workflow per project for now).
- Linking a project back to its template.
- Automatic cleanup of backup files.

## 13. Rollout

1. Backend: new tables, templates module, upgrade function, statuses, types and transitions API, updated work item rules, and filters (id and name matching, new fields), with tests.
2. Frontend: load from the API, colours by category, settings page, template picker, and the delete and rename dialogs.

## 14. Open questions

- None for now. Board columns are settled in §7: every status is a column.
