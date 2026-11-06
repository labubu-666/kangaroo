import io
import json
import zipfile
from uuid import uuid4

from kangaroo.repositories.tables import Base
from kangaroo.services.backup import BACKUP_VERSION
from kangaroo.settings import settings
from kangaroo.testing import type_id


def download(client) -> bytes:
    response = client.get("/api/v1/backup/")
    assert response.status_code == 200
    return response.content


def restore(client, data: bytes):
    return client.post(
        "/api/v1/backup/restore",
        files={"file": ("backup.zip", data, "application/zip")},
    )


def make_backup(tables: dict[str, list[dict]], version: int = BACKUP_VERSION) -> bytes:
    """Build a backup zip by hand. Tables not listed are written empty."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"version": version}))
        for table in Base.metadata.sorted_tables:
            rows = tables.get(table.name, [])
            body = "".join(json.dumps(row) + "\n" for row in rows)
            archive.writestr(f"{table.name}.jsonl", body)
    return buffer.getvalue()


def project_names(client) -> list[str]:
    response = client.get("/api/v1/projects/?limit=100")
    return sorted(p["name"] for p in response.json()["results"])


def test_download_is_a_zip_with_every_table(client):
    """GET /api/v1/backup returns a zip with a manifest and one file per table."""
    response = client.get("/api/v1/backup/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "kangaroo-backup.zip" in response.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
    assert "manifest.json" in names
    assert "projects.jsonl" in names
    assert "work_items.jsonl" in names


def test_restore_round_trip_with_child(client):
    """A backup restores the same projects and work items, including parent links."""
    project_id = client.post("/api/v1/projects/", json={"name": "Kept"}).json()["id"]
    parent = client.post(
        "/api/v1/work-items/",
        json={
            "type_id": type_id(client, project_id, "task"),
            "summary": "Parent",
            "project_id": project_id,
        },
    ).json()
    client.post(
        "/api/v1/work-items/",
        json={
            "type_id": type_id(client, project_id, "task"),
            "summary": "Child",
            "project_id": project_id,
            "parent_id": parent["id"],
        },
    )
    backup = download(client)

    client.post("/api/v1/projects/", json={"name": "Added later"})
    assert project_names(client) == ["Added later", "Kept"]

    assert restore(client, backup).status_code == 204

    assert project_names(client) == ["Kept"]
    items = client.get(f"/api/v1/work-items/?project_id={project_id}").json()
    summaries = sorted(item["summary"] for item in items["results"])
    assert summaries == ["Child", "Parent"]
    child = next(item for item in items["results"] if item["summary"] == "Child")
    assert child["parent_id"] == parent["id"]


def test_restore_more_rows_than_one_batch(client):
    """Restoring more rows than one batch keeps every row."""
    rows = [
        {
            "id": str(uuid4()),
            "trashed": False,
            "created_at": "2026-01-01T00:00:00",
            "modified_at": "2026-01-01T00:00:00",
            "name": f"Project {i}",
            "description": None,
            "labels": [],
        }
        for i in range(2500)
    ]
    assert restore(client, make_backup({"projects": rows})).status_code == 204

    response = client.get("/api/v1/projects/?limit=1")
    assert response.json()["total"] == 2500


def test_restore_rejects_wrong_version_and_keeps_data(client):
    """An unsupported version is rejected and the existing data stays."""
    client.post("/api/v1/projects/", json={"name": "Kept"})
    bad = make_backup({}, version=BACKUP_VERSION + 1)

    response = restore(client, bad)

    assert response.status_code == 422
    assert project_names(client) == ["Kept"]


def test_restore_rejects_file_that_is_not_a_zip(client):
    """A file that is not a zip is rejected and the existing data stays."""
    client.post("/api/v1/projects/", json={"name": "Kept"})

    response = restore(client, b"not a zip")

    assert response.status_code == 422
    assert project_names(client) == ["Kept"]


def test_restore_rejects_missing_table_file(client):
    """An archive without every table file is rejected."""
    client.post("/api/v1/projects/", json={"name": "Kept"})
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("manifest.json", json.dumps({"version": BACKUP_VERSION}))

    response = restore(client, buffer.getvalue())

    assert response.status_code == 422
    assert project_names(client) == ["Kept"]


def test_restore_rejects_broken_foreign_key_and_keeps_data(client):
    """A work item pointing at a missing project is rejected and nothing changes."""
    client.post("/api/v1/projects/", json={"name": "Kept"})
    bad_item = {
        "id": str(uuid4()),
        "trashed": False,
        "created_at": "2026-01-01T00:00:00",
        "modified_at": "2026-01-01T00:00:00",
        "summary": "Orphan",
        "description": None,
        "project_id": str(uuid4()),
        "type_id": str(uuid4()),
        "status_id": str(uuid4()),
        "parent_id": None,
        "labels": [],
    }

    response = restore(client, make_backup({"work_items": [bad_item]}))

    assert response.status_code == 422
    assert project_names(client) == ["Kept"]


def test_restore_rejects_archive_over_size_limit(client, monkeypatch):
    """An archive whose contents exceed the configured limit is rejected."""
    client.post("/api/v1/projects/", json={"name": "Kept"})
    monkeypatch.setattr(settings, "backup_max_uncompressed_bytes", 10)

    response = restore(client, download(client))

    assert response.status_code == 422
    assert project_names(client) == ["Kept"]


def test_backup_leaves_out_derived_columns_and_restore_rebuilds_them(client):
    """Backups skip plain_* columns, and restoring rebuilds them from the Markdown."""
    project = client.post("/api/v1/projects", json={"name": "P"}).json()
    client.post(
        "/api/v1/work-items",
        json={
            "summary": "Task",
            "description": "**Find** me",
            "project_id": project["id"],
            "type_id": type_id(client, project["id"], "task"),
        },
    )
    backup = client.get("/api/v1/backup/").content
    with zipfile.ZipFile(io.BytesIO(backup)) as archive:
        rows = archive.read("work_items.jsonl").decode().splitlines()
    assert rows and all("plain_description" not in row for row in rows)

    assert restore(client, backup).status_code == 204

    assert client.get("/api/v1/work-items?search=find").json()["total"] == 1
    assert client.get("/api/v1/work-items?search=**find**").json()["total"] == 0


def test_restore_rejects_id_that_is_not_a_string(client):
    """A non-string UUID is an invalid row, not a server error."""
    item = {
        "id": 123,
        "trashed": False,
        "created_at": "2026-01-01T00:00:00",
        "modified_at": "2026-01-01T00:00:00",
        "summary": "Bad id",
        "description": None,
        "project_id": str(uuid4()),
        "type_id": str(uuid4()),
        "status_id": str(uuid4()),
        "parent_id": None,
        "labels": [],
    }

    response = restore(client, make_backup({"work_items": [item]}))

    assert response.status_code == 422


def test_restore_rejects_corrupt_member(client):
    """A table file whose data fails its CRC check is rejected, not a server error."""
    data = bytearray(make_backup({}))
    archive = zipfile.ZipFile(io.BytesIO(bytes(data)))
    info = archive.getinfo("manifest.json")
    # Flip a byte in the stored manifest so reading it fails the CRC check.
    offset = info.header_offset + 30 + len(info.filename) + len(info.extra)
    data[offset] ^= 0xFF

    response = restore(client, bytes(data))

    assert response.status_code == 422
