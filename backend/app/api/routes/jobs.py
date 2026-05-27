from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.database.db import get_db
from app.services.job_service import get_user_job, list_active_jobs, request_cancel_job, serialize_job

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.get("/active")
def active_jobs(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return [serialize_job(job) for job in list_active_jobs(db, user_id)]


@router.get("/{job_id}")
def get_job(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return serialize_job(get_user_job(db, job_id, user_id))


@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return serialize_job(request_cancel_job(db, job_id, user_id))
