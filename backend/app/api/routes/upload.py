import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_current_user_id
from app.database.db import get_db
from app.services.job_service import create_processing_job, serialize_job
from app.utils.file_utils import UPLOAD_DIR, create_unique_filename, validate_upload

os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/api/upload", tags=["Upload"])


async def _save_upload(file: UploadFile) -> tuple[str, int]:
    validate_upload(file)
    unique_filename = create_unique_filename(file.filename or "upload")
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    size = 0

    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="File is too large for the configured upload limit.")
                buffer.write(chunk)
    except Exception:
        Path(file_path).unlink(missing_ok=True)
        raise

    if not Path(file_path).exists() or Path(file_path).stat().st_size == 0:
        Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return file_path, size


@router.post("/process")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        file_path, size = await _save_upload(file)
        job = create_processing_job(
            db,
            user_id,
            "upload",
            {"file_path": file_path, "filename": file.filename or Path(file_path).name, "size": size},
            background_tasks=background_tasks
        )
        response = serialize_job(job)
        response["status"] = "pending"
        return {"message": "Upload processing started", "filename": file.filename, **response}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Could not create upload processing job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not start upload processing job.",
        ) from exc


@router.post("")
async def upload_file_legacy(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return await upload_file(background_tasks, file, user_id, db)
