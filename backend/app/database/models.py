from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    sources = relationship("MediaSource", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    theme_preference = Column(String, default="light")
    notification_enabled = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="profile")


class MediaSource(Base):
    __tablename__ = "media_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    youtube_url = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    channel = Column(String, nullable=True)
    thumbnail = Column(String, nullable=True)
    status = Column(String, default="ready", nullable=False)
    transcript_status = Column(String, default="completed", nullable=False)
    chunks_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sources")
    chat_sessions = relationship("ChatSession", back_populates="source")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("media_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_sessions")
    source = relationship("MediaSource", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    matched_text = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, index=True)
    job_id = Column(String, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_type = Column(String, nullable=False)
    source_type = Column(String, nullable=True)
    status = Column(String, default="pending", nullable=False)
    stage = Column(String, default="pending", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    percentage = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    source_id = Column(Integer, ForeignKey("media_sources.id"), nullable=True)
    input_value = Column(Text, nullable=True)
    title = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    channel = Column(String, nullable=True)
    chunks_count = Column(Integer, default=0, nullable=False)
    payload_json = Column(Text, nullable=True)
    cancel_requested = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
