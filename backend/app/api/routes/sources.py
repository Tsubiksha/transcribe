from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.security import get_current_user_id
from app.database.models import MediaSource
from app.services.vector_store_service import count_source_chunks, delete_source_chunks
from app.utils.file_utils import safe_delete
from app.schemas.source_schema import MediaSourceResponse

router = APIRouter(prefix="/api/sources", tags=["Sources"])


@router.get("", response_model=list[MediaSourceResponse])
def get_sources(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    sources = db.query(MediaSource).filter(MediaSource.user_id == user_id).all()
    changed = False
    for source in sources:
        if source.status == "ready" and source.chunks_count <= 0:
            source.chunks_count = count_source_chunks(source.id, user_id)
            changed = True
    if changed:
        db.commit()
    return sources


@router.delete("/{source_id}")
def delete_source(
    source_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    source = db.query(MediaSource).filter(
        MediaSource.id == source_id,
        MediaSource.user_id == user_id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    delete_source_chunks(source_id, user_id)
    safe_delete(source.file_path)
    db.delete(source)
    db.commit()
    
    return {"message": "Source deleted successfully"}


@router.get("/{source_id}/media")
def stream_source_media(
    source_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    source = db.query(MediaSource).filter(
        MediaSource.id == source_id,
        MediaSource.user_id == user_id
    ).first()

    if not source or not source.file_path:
        raise HTTPException(status_code=404, detail="Media file not found")

    if source.status != "ready":
        raise HTTPException(status_code=409, detail="This source is still processing. Please wait.")

    if source.chunks_count <= 0:
        raise HTTPException(status_code=409, detail="Transcript chunks are not ready yet.")

    media_path = Path(source.file_path)
    if not media_path.exists():
        raise HTTPException(status_code=404, detail="Media file not found")

    return FileResponse(media_path, filename=media_path.name)
