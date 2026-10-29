import os
import tempfile
from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status
from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from kangaroo.routes.dependencies import BackupServiceDep

router = APIRouter(prefix="/backup", tags=["backup"])


@router.get("/")
def download_backup(service: BackupServiceDep) -> FileResponse:
    """Download every table as a zip of JSON Lines files.

    The zip is built in a temporary file, so large databases do not need to fit
    in memory. The file is deleted once it has been sent.
    """
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        try:
            service.export(tmp)
        except BaseException:
            os.unlink(tmp.name)
            raise
    return FileResponse(
        tmp.name,
        media_type="application/zip",
        filename="kangaroo-backup.zip",
        background=BackgroundTask(os.unlink, tmp.name),
    )


@router.post("/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_backup(
    file: Annotated[UploadFile, File()],
    service: BackupServiceDep,
) -> None:
    """Replace all data with a backup zip. Any problem leaves the data unchanged."""
    service.restore(file.file)
