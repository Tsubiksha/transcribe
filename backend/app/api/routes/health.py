from fastapi import APIRouter
from app.services.youtube_service import dependency_status

router = APIRouter(prefix="/api/health", tags=["Health"])


@router.get("")
def health_check():
    checks = dependency_status()
    required_ok = checks["ffmpeg"]["available"] and checks["ffprobe"]["available"] and checks["yt_dlp"]["available"]
    return {
        "status": "healthy" if required_ok else "degraded",
        "message": "Backend is running",
        "checks": checks,
    }
