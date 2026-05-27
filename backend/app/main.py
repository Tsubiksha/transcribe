import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import logger
from app.database.db import engine
from app.database.migrations import ensure_dev_schema
from app.database.models import Base
from app.api.routes.auth import router as auth_router
from app.api.routes.profile import router as profile_router
from app.api.routes.upload import router as upload_router
from app.api.routes.youtube import router as youtube_router
from app.api.routes.chat import router as chat_router
from app.api.routes.sources import router as sources_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.TEMP_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PERSIST_PATH, exist_ok=True)

# Create database tables for demo/dev. Use Alembic migrations in larger deployments.
Base.metadata.create_all(bind=engine)
ensure_dev_schema(engine)

app = FastAPI(title="AI Audio/Video Q&A Assistant", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(upload_router)
app.include_router(youtube_router)
app.include_router(chat_router)
app.include_router(sources_router)
app.include_router(health_router)
app.include_router(jobs_router)


@app.on_event("startup")
def cleanup_interrupted_jobs():
    from app.services.job_service import mark_interrupted_jobs_failed

    count = mark_interrupted_jobs_failed()
    if count:
        logger.info("Cleaned up interrupted processing jobs count=%s", count)

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
def home():
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-store"})
    return {"message": "Backend running successfully", "version": "1.0.0"}


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})

    requested_file = frontend_dist / full_path
    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file, headers={"Cache-Control": "no-store"})

    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-store"})

    return JSONResponse(status_code=404, content={"detail": "Frontend build not found"})
