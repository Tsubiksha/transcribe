from pydantic import BaseModel, EmailStr
from typing import Optional


class ChatRequest(BaseModel):
    question: str
    source_id: int


class YouTubeRequest(BaseModel):
    url: str