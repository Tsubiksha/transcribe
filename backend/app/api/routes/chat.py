from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.core.security import get_current_user_id
from app.services.rag_service import generate_answer
from app.services.chat_service import (
    add_chat_message,
    delete_chat_session,
    delete_user_chat_history,
    get_or_create_chat_session,
    get_recent_turns,
    get_user_chat_history,
)
from app.database.models import MediaSource

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    source = db.query(MediaSource).filter(
        MediaSource.id == request.source_id,
        MediaSource.user_id == user_id
    ).first()
    
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.status != "ready":
        raise HTTPException(status_code=409, detail="This source is still processing. Please wait.")

    if source.chunks_count <= 0:
        raise HTTPException(status_code=409, detail="Transcript chunks are not ready yet.")
    
    session = get_or_create_chat_session(db, user_id, request.source_id, request.session_id)
    recent_history = get_recent_turns(db, session.id)
    
    result = generate_answer(
        request.question,
        request.source_id,
        user_id,
        source_title=source.title,
        recent_history=recent_history,
    )
    result["session_id"] = session.id
    
    add_chat_message(
        db, session.id,
        question=request.question,
        answer=result["answer"],
        start_time=result["start_time"],
        end_time=result["end_time"],
        matched_text=result["matched_text"],
        confidence_score=result["confidence_score"]
    )
    
    return result


@router.get("/history")
def get_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return get_user_chat_history(db, user_id)


@router.delete("/history")
def delete_history(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    count = delete_user_chat_history(db, user_id)
    return {"message": f"Deleted {count} chat sessions"}


@router.delete("/history/{session_id}")
def delete_session(
    session_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    deleted = delete_chat_session(db, session_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"message": "Chat session deleted"}
