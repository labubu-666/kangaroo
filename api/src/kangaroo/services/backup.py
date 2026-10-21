"""Back up and restore the whole database as a zip of JSON Lines files.

Rows are read and written in batches, so memory use does not grow with the
size of the database.
"""

import json
import zipfile
from datetime import UTC, datetime
from typing import IO, Any
from uuid import UUID

from pydantic_core import to_jsonable_python
from sqlalchemy import Table, Uuid, insert, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.types import TypeEngine

from kangaroo.errors import InvalidBackupError
from kangaroo.repositories.tables import Base, UTCDateTime

BACKUP_VERSION = 1
BATCH_SIZE = 1000
MANIFEST = "manifest.json"


class BackupService:
    """Export every table to a zip, or replace every table from one."""

    def __init__(self, session: Session, max_uncompressed_bytes: int) -> None:
        self.session = session
        self.max_uncompressed_bytes = max_uncompressed_bytes

    def export(self, target: IO[bytes]) -> None:
        """Write the backup zip to ``target``, one batch of rows at a time."""
        tables = Base.metadata.sorted_tables
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            manifest = {
                "version": BACKUP_VERSION,
                "created_at": datetime.now(UTC).isoformat(),
            }
            archive.writestr(MANIFEST, json.dumps(manifest))
            for table in tables:
                self._export_table(archive, table)

    def restore(self, source: IO[bytes]) -> None:
        """Replace all data with the backup in ``source``.

        Runs in the request's transaction. Foreign keys are checked at the end,
        so a backup can list work items in any order. Any problem raises
        InvalidBackupError, which rolls back the whole restore.
        """
        try:
            archive = zipfile.ZipFile(source)
        except zipfile.BadZipFile as exc:
            raise InvalidBackupError("The file is not a backup archive.") from exc

        with archive:
            tables = Base.metadata.sorted_tables
            self._check_members(archive, tables)
            self._check_manifest(archive)

            try:
                self.session.execute(text("PRAGMA defer_foreign_keys=ON"))
                for table in reversed(tables):
                    self.session.execute(table.delete())
                for table in tables:
                    self._restore_table(archive, table)
            except IntegrityError as exc:
                raise InvalidBackupError(
                    "The backup does not fit the database."
                ) from exc

            if self.session.execute(text("PRAGMA foreign_key_check")).first():
                raise InvalidBackupError(
                    "The backup has rows that refer to rows it does not contain."
                )

    def _export_table(self, archive: zipfile.ZipFile, table: Table) -> None:
        statement = select(table).execution_options(yield_per=BATCH_SIZE)
        with archive.open(f"{table.name}.jsonl", "w") as lines:
            for batch in (
                self.session.execute(statement).mappings().partitions(BATCH_SIZE)
            ):
                for row in batch:
                    line = json.dumps(to_jsonable_python(dict(row)))
                    lines.write(line.encode() + b"\n")

    def _check_members(self, archive: zipfile.ZipFile, tables: list[Table]) -> None:
        """Reject archives with missing or extra files, and too much data."""
        expected = {MANIFEST} | {f"{table.name}.jsonl" for table in tables}
        names = {info.filename for info in archive.infolist()}
        if names != expected:
            raise InvalidBackupError("The backup does not match this schema.")
        total = sum(info.file_size for info in archive.infolist())
        if total > self.max_uncompressed_bytes:
            raise InvalidBackupError("The backup is too large to restore.")

    def _check_manifest(self, archive: zipfile.ZipFile) -> None:
        try:
            manifest = json.loads(archive.read(MANIFEST))
        except ValueError as exc:
            raise InvalidBackupError("The backup manifest is not valid.") from exc
        if not isinstance(manifest, dict) or manifest.get("version") != BACKUP_VERSION:
            raise InvalidBackupError(
                f"Unsupported backup version. Expected {BACKUP_VERSION}."
            )

    def _restore_table(self, archive: zipfile.ZipFile, table: Table) -> None:
        batch: list[dict[str, Any]] = []
        with archive.open(f"{table.name}.jsonl") as lines:
            for line in lines:
                if not line.strip():
                    continue
                batch.append(_parse_row(table, line))
                if len(batch) == BATCH_SIZE:
                    self.session.execute(insert(table), batch)
                    batch = []
        if batch:
            self.session.execute(insert(table), batch)


def _parse_row(table: Table, line: bytes) -> dict[str, Any]:
    """Turn one JSON line back into Python values the table's columns accept."""
    try:
        raw = json.loads(line)
        if not isinstance(raw, dict) or set(raw) != set(table.c.keys()):
            raise ValueError("columns do not match")
        return {
            name: _from_json(table.c[name].type, value) for name, value in raw.items()
        }
    except (ValueError, TypeError) as exc:
        raise InvalidBackupError(f"Invalid row in {table.name}.") from exc


def _from_json(column_type: TypeEngine, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(column_type, Uuid):
        return UUID(value)
    if isinstance(column_type, UTCDateTime):
        return datetime.fromisoformat(value)
    return value
