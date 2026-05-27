from pathlib import Path
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR_PATH = BASE_DIR.parent / "storage"
UPLOADS_DIR_PATH = STORAGE_DIR_PATH / "uploads"
TEMP_DIR_PATH = STORAGE_DIR_PATH / "temp"
PROCESSED_DIR_PATH = STORAGE_DIR_PATH / "processed"
CHROMA_STORAGE_DIR_PATH = BASE_DIR.parent / "chroma_storage"


def _backend_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # File Upload / Processing Storage
    STORAGE_DIR: str = str(STORAGE_DIR_PATH)
    UPLOAD_DIR: str | None = None
    TEMP_DIR: str | None = None
    PROCESSED_DIR: str | None = None
    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_EXTENSIONS: List[str] = ["mp3", "wav", "m4a", "aac", "flac", "mp4", "mov", "mkv", "webm"]

    # ChromaDB
    CHROMA_PERSIST_PATH: str = str(CHROMA_STORAGE_DIR_PATH)
    CHROMA_COLLECTION_NAME: str = "video_transcripts_nomic_embed_text"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    OLLAMA_REQUEST_TIMEOUT_SECONDS: int = 120
    EMBEDDING_BATCH_SIZE: int = 8
    EMBEDDING_CONCURRENCY: int = 3
    EMBEDDING_WRITE_BATCH_SIZE: int = 8
    EMBEDDING_LOG_EVERY: int = 25
    EMBEDDING_SAFE_TOKEN_LIMIT: int = 480
    EMBEDDING_MIN_RETRY_TOKEN_LIMIT: int = 160

    # FFmpeg / yt-dlp
    FFMPEG_LOCATION: str | None = None
    YOUTUBE_AUDIO_QUALITY: str = "96"
    YOUTUBE_AUDIO_FORMAT: str = "worstaudio[abr<=64]/worstaudio/bestaudio"
    YOUTUBE_TRANSCODE_AUDIO: bool = False
    YOUTUBE_CAPTION_LANGS: List[str] = ["ta.*", "ta", "en.*", "en"]
    YTDLP_COOKIES_FILE: str | None = None
    YTDLP_COOKIES_FROM_BROWSER: str | None = None

    # Whisper
    WHISPER_MODEL: str = "tiny"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_CPU_THREADS: int = 8
    WHISPER_NUM_WORKERS: int = 2
    WHISPER_BEAM_SIZE: int = 1
    WHISPER_PREPARE_AUDIO: bool = True
    WHISPER_VAD_MIN_SILENCE_MS: int = 500
    WHISPER_VAD_SPEECH_PAD_MS: int = 200

    # Chunking
    CHUNK_DURATION_SECONDS: int = 90
    CHUNK_OVERLAP_SECONDS: int = 5
    CHUNK_TARGET_MIN_CHARACTERS: int = 700
    CHUNK_TARGET_MAX_CHARACTERS: int = 900
    CHUNK_OVERLAP_CHARACTERS: int = 150
    CHUNK_CONVERSATIONAL_TARGET_MAX: int = 1100
    CHUNK_CONVERSATIONAL_OVERLAP: int = 120

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", "ALLOWED_EXTENSIONS", "YOUTUBE_CAPTION_LANGS", mode="before")
    @classmethod
    def split_csv(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def normalize_paths(self):
        storage_dir = _backend_path(self.STORAGE_DIR)
        upload_dir = _backend_path(self.UPLOAD_DIR) if self.UPLOAD_DIR else storage_dir / "uploads"
        temp_dir = _backend_path(self.TEMP_DIR) if self.TEMP_DIR else storage_dir / "temp"
        processed_dir = _backend_path(self.PROCESSED_DIR) if self.PROCESSED_DIR else storage_dir / "processed"
        chroma_dir = _backend_path(self.CHROMA_PERSIST_PATH)

        for directory in (storage_dir, upload_dir, temp_dir, processed_dir, chroma_dir):
            directory.mkdir(parents=True, exist_ok=True)

        self.STORAGE_DIR = str(storage_dir)
        self.UPLOAD_DIR = str(upload_dir)
        self.TEMP_DIR = str(temp_dir)
        self.PROCESSED_DIR = str(processed_dir)
        self.CHROMA_PERSIST_PATH = str(chroma_dir)
        return self

    class Config:
        env_file = str(BASE_DIR / ".env.local")
        case_sensitive = True


settings = Settings()
