from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class MediaSourceCreate(BaseModel):
    title: str
    source_type: str
    file_path: Optional[str] = None
    youtube_url: Optional[str] = None


class MediaSourceResponse(BaseModel):
    id: int
    title: str
    source_type: str
    youtube_url: Optional[str] = None
    duration: Optional[float] = None
    channel: Optional[str] = None
    thumbnail: Optional[str] = None
    status: str = "ready"
    transcript_status: str = "completed"
    chunks_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
