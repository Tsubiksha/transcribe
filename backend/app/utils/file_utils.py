import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from app.core.config import settings

UPLOAD_DIR = settings.UPLOAD_DIR
TEMP_DIR = settings.TEMP_DIR
PROCESSED_DIR = settings.PROCESSED_DIR
TRANSCRIPT_DIR = str(Path(settings.STORAGE_DIR) / "transcripts")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def create_unique_filename(filename: str) -> str:
    ext = get_file_extension(filename)
    return f"{uuid.uuid4()}.{ext}"


def is_video_file(filename: str) -> bool:
    return get_file_extension(filename) in ["mp4", "mov", "mkv", "webm"]


def is_audio_file(filename: str) -> bool:
    return get_file_extension(filename) in ["mp3", "wav", "m4a", "aac", "flac"]


def validate_upload(file: UploadFile) -> None:
    extension = get_file_extension(file.filename or "")
    if extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")


def safe_delete(path: str | None) -> None:
    if not path:
        return
    allowed_roots = [
        Path(UPLOAD_DIR).resolve(),
        Path(TEMP_DIR).resolve(),
        Path(PROCESSED_DIR).resolve(),
    ]
    target = Path(path).resolve()
    if any(root == target or root in target.parents or root == target.parent for root in allowed_roots):
        target.unlink(missing_ok=True)
