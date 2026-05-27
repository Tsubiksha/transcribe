from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    source_id: int
    session_id: Optional[int] = None


class TimestampResponse(BaseModel):
    start: str
    end: str
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    timestamps: List[TimestampResponse] = Field(default_factory=list)
    source: Optional[str] = None
    source_id: Optional[int] = None
    session_id: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    matched_text: Optional[str] = None
    confidence_score: Optional[float] = None


class ChatMessageResponse(BaseModel):
    id: int
    question: str
    answer: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    matched_text: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: str
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    session_id: int
    source_id: Optional[int] = None
    source_title: Optional[str] = None
    created_at: str
    messages: List[ChatMessageResponse]
