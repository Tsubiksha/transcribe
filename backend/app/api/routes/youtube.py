from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.core.security import get_current_user_id
from app.database.db import get_db
from app.services.job_service import create_processing_job, serialize_job
from app.services.youtube_service import YouTubeProcessingError, get_youtube_metadata, validate_youtube_url

router = APIRouter(prefix="/api/youtube", tags=["YouTube"])


class YouTubeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        try:
            return validate_youtube_url(value)
        except YouTubeProcessingError as exc:
            raise ValueError(exc.public_message) from exc


@router.post("/metadata")
def fetch_youtube_metadata(
    request: YouTubeRequest,
    user_id: int = Depends(get_current_user_id),
):
    try:
        metadata = get_youtube_metadata(request.url)
        return {"status": "ok", **metadata}
    except YouTubeProcessingError as exc:
        logger.error("YouTube metadata error: %s", exc.log_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.public_message) from exc


@router.post("/process")
def process_youtube(
    request: YouTubeRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        job = create_processing_job(db, user_id, "youtube", {"url": request.url}, background_tasks=background_tasks)
        response = serialize_job(job)
        response["status"] = "pending"
        return {"message": "YouTube processing started", **response}

    except YouTubeProcessingError as exc:
        logger.error("YouTube processing error: %s", exc.log_message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.public_message) from exc
    except Exception as exc:
        logger.exception("Could not create YouTube processing job")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not start YouTube processing job.",
        ) from exc


@router.post("")
def process_youtube_legacy(
    request: YouTubeRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return process_youtube(request, background_tasks, user_id, db)
