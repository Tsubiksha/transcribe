import json
import threading
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session
from yt_dlp.utils import DownloadCancelled

from app.core.config import settings
from app.core.logging import logger
from app.database.db import SessionLocal
from app.database.models import MediaSource, ProcessingJob
from app.services.audio_service import extract_audio, get_audio_duration, prepare_audio_for_whisper
from app.services.chunking_service import create_chunks
from app.services.transcription_service import transcribe_audio
from app.services.vector_store_service import store_chunks
from app.services.youtube_service import YouTubeProcessingError, download_youtube_audio, extract_youtube_captions
from app.utils.file_utils import is_video_file

TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def serialize_job(job: ProcessingJob) -> dict:
    payload = json.loads(job.payload_json or "{}")
    result = payload.get("result") or {}
    return {
        "job_id": job.id,
        "job_type": job.job_type,
        "source_type": job.source_type or job.job_type,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "percentage": job.progress,
        "error_message": job.error_message,
        "source_id": job.source_id,
        "input_value": job.input_value,
        "title": job.title or result.get("title"),
        "channel": job.channel or result.get("channel"),
        "duration": job.duration if job.duration is not None else result.get("duration"),
        "chunks_count": job.chunks_count or result.get("chunks_count") or 0,
        "chunks_stored": result.get("chunks_stored") or job.chunks_count or 0,
        "thumbnail": job.thumbnail_url or result.get("thumbnail"),
        "thumbnail_url": job.thumbnail_url or result.get("thumbnail"),
        "cancel_requested": job.cancel_requested,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def create_processing_job(db: Session, user_id: int, job_type: str, payload: dict, background_tasks=None) -> ProcessingJob:
    job = ProcessingJob(
        id=uuid.uuid4().hex,
        job_id=uuid.uuid4().hex,
        user_id=user_id,
        job_type=job_type,
        source_type=job_type,
        status="pending",
        stage="pending",
        progress=0,
        percentage=0,
        input_value=payload.get("url") or payload.get("filename") or payload.get("file_path"),
        title=payload.get("title"),
        thumbnail_url=payload.get("thumbnail") or payload.get("thumbnail_url"),
        duration=payload.get("duration"),
        channel=payload.get("channel"),
        payload_json=json.dumps(payload),
    )
    job.job_id = job.id
    db.add(job)
    db.commit()
    db.refresh(job)
    if background_tasks:
        background_tasks.add_task(run_processing_job, job.id)
    else:
        thread = threading.Thread(target=run_processing_job, args=(job.id,), daemon=True)
        thread.start()
    return job


def request_cancel_job(db: Session, job_id: str, user_id: int) -> ProcessingJob:
    job = get_user_job(db, job_id, user_id)
    if job.status not in TERMINAL_STATUSES:
        job.cancel_requested = True
        job.status = "cancelled"
        job.stage = "cancelled"
        job.error_message = "Cancellation requested."
        job.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
    return job


def get_user_job(db: Session, job_id: str, user_id: int) -> ProcessingJob:
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id, ProcessingJob.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def list_active_jobs(db: Session, user_id: int) -> list[ProcessingJob]:
    return db.query(ProcessingJob).filter(
        ProcessingJob.user_id == user_id,
        ProcessingJob.status.notin_(TERMINAL_STATUSES),
    ).order_by(ProcessingJob.created_at.desc()).all()


def _update(db: Session, job: ProcessingJob, *, status: str | None = None, stage: str | None = None,
            percentage: int | None = None, error_message: str | None = None, source_id: int | None = None) -> None:
    old_status = job.status
    old_stage = job.stage
    old_progress = job.progress
    if status is not None:
        job.status = status
    if stage is not None:
        job.stage = stage
    if percentage is not None:
        progress = max(0, min(100, int(percentage)))
        job.progress = progress
        job.percentage = progress
    if error_message is not None:
        job.error_message = error_message
    if source_id is not None:
        job.source_id = source_id
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    if job.stage != old_stage or job.status != old_status:
        logger.info(
            "Job stage job_id=%s type=%s status=%s stage=%s progress=%s%%",
            job.id,
            job.job_type,
            job.status,
            job.stage,
            job.progress,
        )
    elif percentage is not None and job.progress != old_progress and job.stage in {"embedding", "transcribing"}:
        logger.info(
            "Job progress job_id=%s stage=%s progress=%s%%",
            job.id,
            job.stage,
            job.progress,
        )


def _save_result(db: Session, job: ProcessingJob, result: dict) -> None:
    payload = json.loads(job.payload_json or "{}")
    payload["result"] = result
    job.title = result.get("title") or job.title
    job.channel = result.get("channel") or job.channel
    job.duration = result.get("duration") if result.get("duration") is not None else job.duration
    job.thumbnail_url = result.get("thumbnail") or job.thumbnail_url
    job.chunks_count = result.get("chunks_count") or job.chunks_count or 0
    job.payload_json = json.dumps(payload)
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)


def _check_cancelled(db: Session, job: ProcessingJob) -> None:
    db.refresh(job)
    if job.cancel_requested or job.status == "cancelled":
        _update(db, job, status="cancelled", stage="cancelled", percentage=job.progress, error_message="Processing cancelled.")
        raise RuntimeError("Processing cancelled.")


def _store_source_and_chunks(
    db: Session,
    *,
    job: ProcessingJob,
    user_id: int,
    title: str,
    source_type: str,
    file_path: str,
    youtube_url: str | None,
    duration: float,
    transcript: list[dict],
    metadata: dict | None = None,
) -> MediaSource:
    _check_cancelled(db, job)
    source = MediaSource(
        user_id=user_id,
        title=title,
        source_type=source_type,
        file_path=file_path,
        youtube_url=youtube_url,
        duration=duration,
        channel=(metadata or {}).get("channel"),
        thumbnail=(metadata or {}).get("thumbnail"),
        status="processing",
        transcript_status="transcribing",
        chunks_count=0,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    _update(db, job, source_id=source.id)
    logger.info("Processing source created source_id=%s title=%s job_id=%s", source.id, source.title, job.id)

    try:
        _check_cancelled(db, job)
        source.transcript_status = "completed"
        db.commit()

        _update(db, job, status="chunking", stage="chunking", percentage=72)
        chunk_metadata = {
            **(metadata or {}),
            "title": title,
            "transcript_source": (metadata or {}).get("transcript_source") or source_type,
        }
        chunks = create_chunks(transcript, source.id, user_id, metadata=chunk_metadata)
        logger.info("Chunks created count=%s source_id=%s job_id=%s", len(chunks), source.id, job.id)
        if not chunks:
            raise ValueError("Processing completed, but no transcript chunks were created. Please check transcription.")

        for chunk in chunks:
            chunk["source_id"] = source.id

        _check_cancelled(db, job)
        _update(db, job, status="embedding", stage="embedding", percentage=80)

        def embedding_progress(stored: int, total: int) -> None:
            _check_cancelled(db, job)
            if total:
                percentage = 80 + int((stored / total) * 15)
                _update(db, job, status="embedding", stage="embedding", percentage=percentage)

        chunks_stored = store_chunks(chunks, source.id, user_id, progress_callback=embedding_progress)
        logger.info("ChromaDB stored count=%s source_id=%s job_id=%s", chunks_stored, source.id, job.id)
        if not chunks_stored:
            raise ValueError("Processing completed, but no transcript chunks were stored. Please check transcription.")

        _check_cancelled(db, job)
        _update(db, job, status="saving_source", stage="saving_source", percentage=96)
        source.status = "ready"
        source.transcript_status = "completed"
        source.chunks_count = chunks_stored
        source.error_message = None
        db.commit()
        db.refresh(source)
    except Exception:
        source.status = "failed"
        source.error_message = "Processing failed before the source became ready."
        db.commit()
        raise

    logger.info("Source saved source_id=%s title=%s job_id=%s", source.id, source.title, job.id)
    _save_result(db, job, {
        "message": f"{'YouTube video' if source_type == 'youtube' else 'File'} processed successfully",
        "source_id": source.id,
        "title": source.title,
        "channel": source.channel,
        "duration": duration,
        "chunks_count": chunks_stored,
        "chunks_stored": chunks_stored,
        "thumbnail": source.thumbnail,
        "status": "ready",
    })
    _update(db, job, status="completed", stage="completed", percentage=100, source_id=source.id, error_message="")
    return source


def _download_progress(db: Session, job: ProcessingJob):
    def hook(data: dict) -> None:
        db.refresh(job)
        if job.cancel_requested:
            raise DownloadCancelled("Processing cancelled by user.")
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            downloaded = data.get("downloaded_bytes") or 0
            if total:
                percentage = 5 + int((downloaded / total) * 35)
                _update(db, job, status="downloading", stage="downloading", percentage=percentage)
        elif status == "finished":
            _update(db, job, status="converting", stage="converting", percentage=45)
        elif status == "post_process":
            _update(db, job, status="converting", stage="converting", percentage=48)
    return hook


def _run_youtube(db: Session, job: ProcessingJob, payload: dict) -> None:
    url = payload["url"]
    _update(db, job, status="transcribing", stage="captions", percentage=12)
    caption_result = extract_youtube_captions(url)
    if caption_result:
        transcript, title, metadata = caption_result
        job.title = title
        job.channel = metadata.get("channel")
        job.thumbnail_url = metadata.get("thumbnail")
        job.duration = metadata.get("duration")
        duration = float(metadata.get("duration") or transcript[-1]["end"] or 0.0)
        logger.info(
            "YouTube caption transcript ready job_id=%s source=%s segments=%s duration=%s",
            job.id,
            metadata.get("transcript_source"),
            len(transcript),
            duration,
        )
        _store_source_and_chunks(
            db,
            job=job,
            user_id=job.user_id,
            title=title,
            source_type="youtube",
            file_path=metadata.get("caption_file") or url,
            youtube_url=url,
            duration=duration,
            transcript=transcript,
            metadata=metadata,
        )
        return

    logger.info("No usable YouTube captions found job_id=%s; falling back to Whisper transcription", job.id)
    _update(db, job, status="downloading", stage="downloading", percentage=5)
    file_path, title, metadata = download_youtube_audio(url, progress_hook=_download_progress(db, job))
    job.title = title
    job.channel = metadata.get("channel")
    job.thumbnail_url = metadata.get("thumbnail")
    job.duration = metadata.get("duration")
    _update(db, job, status="converting", stage="converting", percentage=50)
    logger.info("YouTube audio downloaded file=%s title=%s job_id=%s", file_path, title, job.id)
    if not Path(file_path).exists() or Path(file_path).stat().st_size == 0:
        raise ValueError("YouTube audio download completed, but the audio file is missing or empty.")

    _check_cancelled(db, job)
    try:
        duration = get_audio_duration(file_path)
    except Exception:
        logger.exception("Could not determine YouTube audio duration")
        duration = float(metadata.get("duration") or 0.0)

    _update(db, job, status="converting", stage="preparing_audio", percentage=52)
    whisper_audio_path = prepare_audio_for_whisper(file_path)
    _update(db, job, status="transcribing", stage="transcribing", percentage=55)
    transcript = transcribe_audio(whisper_audio_path, job_id=job.id, label="youtube")
    logger.info("YouTube transcription segments count=%s job_id=%s", len(transcript), job.id)
    if not transcript:
        raise ValueError("Whisper returned an empty transcript for this YouTube video.")

    _store_source_and_chunks(
        db,
        job=job,
        user_id=job.user_id,
        title=title,
        source_type="youtube",
        file_path=file_path,
        youtube_url=url,
        duration=duration,
        transcript=transcript,
        metadata=metadata,
    )


def _run_upload(db: Session, job: ProcessingJob, payload: dict) -> None:
    file_path = payload["file_path"]
    filename = payload["filename"]
    if not Path(file_path).exists() or Path(file_path).stat().st_size == 0:
        raise ValueError("Uploaded file is missing or empty.")

    _update(db, job, status="converting", stage="converting", percentage=25)
    audio_path = extract_audio(file_path) if is_video_file(filename) else file_path
    if not Path(audio_path).exists() or Path(audio_path).stat().st_size == 0:
        raise ValueError("Processed audio file is missing or empty.")

    _check_cancelled(db, job)
    try:
        duration = get_audio_duration(audio_path)
    except Exception:
        logger.exception("Could not determine upload duration")
        duration = 0.0

    _update(db, job, status="converting", stage="preparing_audio", percentage=52)
    whisper_audio_path = prepare_audio_for_whisper(audio_path)
    _update(db, job, status="transcribing", stage="transcribing", percentage=55)
    transcript = transcribe_audio(whisper_audio_path, job_id=job.id, label="upload")
    logger.info("Upload transcription segments count=%s job_id=%s", len(transcript), job.id)
    if not transcript:
        raise ValueError("Whisper returned an empty transcript for this uploaded file.")

    _store_source_and_chunks(
        db,
        job=job,
        user_id=job.user_id,
        title=filename,
        source_type="upload",
        file_path=file_path,
        youtube_url=None,
        duration=duration,
        transcript=transcript,
        metadata={},
    )


def _public_error(exc: Exception) -> str:
    if isinstance(exc, YouTubeProcessingError):
        return exc.public_message
    text = str(exc) or exc.__class__.__name__
    lowered = text.lower()
    if "ffmpeg" in lowered and ("not found" in lowered or "not installed" in lowered):
        return "FFmpeg is missing. Install FFmpeg and make sure ffmpeg and ffprobe are available."
    if "interrupted" in lowered or "signal 2" in lowered or "immediate exit requested" in lowered:
        return "Processing was interrupted. Run the backend without --reload for long videos."
    if "timed out" in lowered or "timeout" in lowered:
        return "Processing timed out. Try again or use a shorter media file."
    if "too large" in lowered:
        return "This media file is too large for the configured processing limit."
    if "cancelled" in lowered:
        return "Processing cancelled."
    return text


def run_processing_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return
        payload = json.loads(job.payload_json or "{}")
        _update(db, job, status="pending", stage="pending", percentage=1)
        _check_cancelled(db, job)
        if job.job_type == "youtube":
            _run_youtube(db, job, payload)
        elif job.job_type == "upload":
            _run_upload(db, job, payload)
        else:
            raise ValueError(f"Unsupported job type: {job.job_type}")
    except Exception as exc:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job and job.status != "cancelled":
            logger.exception("Processing job failed: %s", job_id)
            if job.source_id:
                source = db.query(MediaSource).filter(MediaSource.id == job.source_id).first()
                if source:
                    source.status = "failed"
                    source.error_message = _public_error(exc)
                    db.commit()
            _update(db, job, status="failed", stage="failed", error_message=_public_error(exc))
    finally:
        db.close()


def mark_interrupted_jobs_failed() -> int:
    db = SessionLocal()
    try:
        jobs = db.query(ProcessingJob).filter(ProcessingJob.status.notin_(TERMINAL_STATUSES)).all()
        for job in jobs:
            job.status = "failed"
            job.stage = "failed"
            job.error_message = "Processing was interrupted by a backend restart. Start the job again and run long jobs without --reload."
            job.updated_at = datetime.utcnow()
            if job.source_id:
                source = db.query(MediaSource).filter(MediaSource.id == job.source_id).first()
                if source and source.status != "ready":
                    source.status = "failed"
                    source.error_message = job.error_message
        db.commit()
        if jobs:
            logger.warning("Marked %s interrupted processing job(s) as failed after backend startup", len(jobs))
        return len(jobs)
    finally:
        db.close()
