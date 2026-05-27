from sqlalchemy.orm import Session
from app.database.models import ChatSession, ChatMessage


def create_chat_session(db: Session, user_id: int, source_id: int = None) -> ChatSession:
    session = ChatSession(user_id=user_id, source_id=source_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_chat_session(db: Session, session_id: int, user_id: int, source_id: int | None = None) -> ChatSession | None:
    query = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id)
    if source_id is not None:
        query = query.filter(ChatSession.source_id == source_id)
    return query.first()


def get_or_create_chat_session(db: Session, user_id: int, source_id: int, session_id: int | None = None) -> ChatSession:
    if session_id:
        session = get_chat_session(db, session_id, user_id, source_id)
        if session:
            return session
    return create_chat_session(db, user_id, source_id)


def get_recent_turns(db: Session, session_id: int, limit: int = 4) -> list[dict]:
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(
        ChatMessage.created_at.desc()
    ).limit(limit).all()
    return [
        {
            "question": message.question,
            "answer": message.answer,
        }
        for message in reversed(messages)
    ]


def add_chat_message(db: Session, session_id: int, question: str, answer: str,
                     start_time: float = None, end_time: float = None,
                     matched_text: str = None, confidence_score: float = None) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        question=question,
        answer=answer,
        start_time=start_time,
        end_time=end_time,
        matched_text=matched_text,
        confidence_score=confidence_score
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_user_chat_history(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    
    result = []
    for session in sessions:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(
            ChatMessage.created_at.asc()
        ).all()
        last_updated = max([session.created_at] + [message.created_at for message in messages])
        thumbnail_url = None
        if session.source and session.source.youtube_url and "youtube.com/watch" in session.source.youtube_url:
            video_id = session.source.youtube_url.split("v=", 1)[-1].split("&", 1)[0]
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        elif session.source and session.source.youtube_url and "youtu.be/" in session.source.youtube_url:
            video_id = session.source.youtube_url.rsplit("/", 1)[-1].split("?", 1)[0]
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        result.append({
            "session_id": session.id,
            "source_id": session.source_id,
            "source_title": session.source.title if session.source else None,
            "source_type": session.source.source_type if session.source else None,
            "source_thumbnail_url": thumbnail_url,
            "created_at": session.created_at.isoformat(),
            "last_updated": last_updated.isoformat(),
            "messages": [
                {
                    "id": m.id,
                    "question": m.question,
                    "answer": m.answer,
                    "start_time": m.start_time,
                    "end_time": m.end_time,
                    "matched_text": m.matched_text,
                    "confidence_score": m.confidence_score,
                    "created_at": m.created_at.isoformat()
                } for m in messages
            ]
        })
    
    return sorted(result, key=lambda item: item["last_updated"], reverse=True)[skip:skip + limit]


def delete_user_chat_history(db: Session, user_id: int) -> int:
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    count = len(sessions)
    
    for session in sessions:
        db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
        db.delete(session)
    
    db.commit()
    return count


def delete_chat_session(db: Session, session_id: int, user_id: int) -> bool:
    session = get_chat_session(db, session_id, user_id)
    if not session:
        return False
    db.query(ChatMessage).filter(ChatMessage.session_id == session.id).delete()
    db.delete(session)
    db.commit()
    return True
