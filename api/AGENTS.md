# Database migrations
- This is a greenfield project.
- During schema changes. Run DDL and retroactively backfill the columns. 
- Create `kangaroo.db.*.bak` in case things go south.
- When ready, we will add an `alembic` based migration utility.
# Dependencies
- The project uses `uv`.
# Linting
## ruff
- After making changes, run `uv run ruff format` to make sure files are correctly linted.
# Testing
- The project exclusively uses `pytest`.
- Prefer `monkeypatch` to `unittest.mock.patch`.
- Run tests using `uv run pytest -vvv`.