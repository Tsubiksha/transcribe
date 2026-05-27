import os
import re
import shutil
import uuid
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

from yt_dlp import DownloadError, YoutubeDL

from app.core.config import settings
from app.core.logging import logger
from app.utils.file_utils import PROCESSED_DIR, TEMP_DIR

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


class YouTubeProcessingError(Exception):
    def __init__(self, public_message: str, *, log_message: str | None = None):
        super().__init__(public_message)
        self.public_message = public_message
        self.log_message = log_message or public_message


YOUTUBE_HOST_RE = re.compile(r"(^|\.)youtube\.com$|(^|\.)youtu\.be$", re.IGNORECASE)
VTT_TIMESTAMP_RE = re.compile(
    r"(?P<start>(?:\d+:)?\d{2}:\d{2}\.\d{3})\s+-->\s+"
    r"(?P<end>(?:\d+:)?\d{2}:\d{2}\.\d{3})"
)
TAG_RE = re.compile(r"<[^>]+>")


def validate_youtube_url(url: str) -> str:
    value = (url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise YouTubeProcessingError("Enter a valid YouTube URL.")
    if not YOUTUBE_HOST_RE.search(parsed.netloc.lower()):
        raise YouTubeProcessingError("Only YouTube URLs are supported.")
    if parsed.netloc.lower().endswith("youtu.be") and not parsed.path.strip("/"):
        raise YouTubeProcessingError("The YouTube short URL is missing a video id.")
    if "youtube.com" in parsed.netloc.lower() and not (parsed.query or parsed.path.strip("/")):
        raise YouTubeProcessingError("The YouTube URL is missing a video id.")
    return value


def ensure_ffmpeg_available() -> None:
    if settings.FFMPEG_LOCATION:
        ffmpeg_dir = Path(settings.FFMPEG_LOCATION)
        if (ffmpeg_dir / "ffmpeg.exe").exists() and (ffmpeg_dir / "ffprobe.exe").exists():
            return
        if (ffmpeg_dir / "bin" / "ffmpeg.exe").exists() and (ffmpeg_dir / "bin" / "ffprobe.exe").exists():
            return

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise YouTubeProcessingError(
            "FFmpeg is not available. Install FFmpeg and make sure ffmpeg and ffprobe are in PATH, or set FFMPEG_LOCATION to your FFmpeg folder.",
            log_message="ffmpeg or ffprobe not found in PATH or FFMPEG_LOCATION",
        )


def resolve_ffmpeg_binary(name: str) -> str | None:
    if settings.FFMPEG_LOCATION:
        ffmpeg_dir = Path(settings.FFMPEG_LOCATION)
        candidates = [
            ffmpeg_dir / f"{name}.exe",
            ffmpeg_dir / "bin" / f"{name}.exe",
            ffmpeg_dir / name,
            ffmpeg_dir / "bin" / name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
    return shutil.which(name)


def youtube_cookiefile() -> str | None:
    cookiefile = (settings.YTDLP_COOKIES_FILE or "").strip()
    if not cookiefile:
        return None
    path = Path(cookiefile)
    if path.exists() and path.is_file():
        return str(path)
    logger.warning("YTDLP_COOKIES_FILE is configured but not found: %s", cookiefile)
    return None


def get_youtube_metadata(url: str) -> dict:
    safe_url = validate_youtube_url(url)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    cookiefile = youtube_cookiefile()
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    elif settings.YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts["cookiesfrombrowser"] = (settings.YTDLP_COOKIES_FROM_BROWSER,)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(safe_url, download=False)
    except DownloadError as exc:
        error_text = str(exc)
        if "Sign in to confirm" in error_text or "not a bot" in error_text:
            raise YouTubeProcessingError(
                "YouTube blocked automated access. Configure cookies.txt or upload the video/audio file directly.",
                log_message=error_text,
            ) from exc
        raise YouTubeProcessingError("Could not fetch YouTube metadata.", log_message=error_text) from exc

    metadata = {
        "title": (info or {}).get("title") or "YouTube video",
        "channel": (info or {}).get("channel") or (info or {}).get("uploader"),
        "duration": (info or {}).get("duration"),
        "thumbnail": (info or {}).get("thumbnail"),
        "webpage_url": (info or {}).get("webpage_url") or safe_url,
    }
    logger.info("YouTube metadata fetched title=%s channel=%s duration=%s", metadata["title"], metadata["channel"], metadata["duration"])
    return metadata


def _timestamp_to_seconds(value: str) -> float:
    parts = value.split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def _clean_caption_text(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_vtt(path: Path) -> list[dict]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    transcript = []
    index = 0

    while index < len(lines):
        match = VTT_TIMESTAMP_RE.search(lines[index])
        if not match:
            index += 1
            continue

        start = _timestamp_to_seconds(match.group("start"))
        end = _timestamp_to_seconds(match.group("end"))
        index += 1
        text_lines = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index].strip())
            index += 1

        text = _clean_caption_text(" ".join(text_lines))
        if text and end > start:
            if transcript and transcript[-1]["text"] == text and abs(transcript[-1]["end"] - start) <= 1.0:
                transcript[-1]["end"] = round(end, 2)
            else:
                transcript.append({
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "text": text,
                })

        index += 1

    return transcript


def _download_caption_file(url: str, *, automatic: bool, languages: list[str]) -> tuple[Path | None, dict]:
    stem = f"captions_{uuid.uuid4().hex}"
    output_template = str(Path(TEMP_DIR) / stem)
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "writesubtitles": not automatic,
        "writeautomaticsub": automatic,
        "subtitleslangs": languages,
        "subtitlesformat": "vtt/best",
        "outtmpl": {"default": output_template},
    }
    cookiefile = youtube_cookiefile()
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    elif settings.YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts["cookiesfrombrowser"] = (settings.YTDLP_COOKIES_FROM_BROWSER,)

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    matches = sorted(Path(TEMP_DIR).glob(f"{stem}*.vtt"), key=lambda item: item.stat().st_size, reverse=True)
    return (matches[0] if matches else None), info or {}


def extract_youtube_captions(url: str) -> tuple[list[dict], str, dict] | None:
    safe_url = validate_youtube_url(url)
    last_info: dict = {}
    caption_language_sets = []
    preferred_languages = settings.YOUTUBE_CAPTION_LANGS or []
    if preferred_languages:
        caption_language_sets.append(preferred_languages)
    caption_language_sets.append(["all", "-live_chat"])

    for languages in caption_language_sets:
        for automatic in (False, True):
            source_name = "automatic captions" if automatic else "captions"
            try:
                caption_path, info = _download_caption_file(safe_url, automatic=automatic, languages=languages)
                last_info = info or last_info
            except DownloadError as exc:
                logger.warning("Could not fetch YouTube %s langs=%s: %s", source_name, ",".join(languages), exc)
                continue

            if not caption_path:
                logger.info("No YouTube %s file found langs=%s", source_name, ",".join(languages))
                continue

            transcript = _parse_vtt(caption_path)
            if transcript:
                title = (last_info or {}).get("title") or "YouTube video"
                title = title.replace("/", "_").replace("\\", "_")[:140]
                metadata = {
                    "channel": (last_info or {}).get("channel") or (last_info or {}).get("uploader"),
                    "duration": (last_info or {}).get("duration"),
                    "thumbnail": (last_info or {}).get("thumbnail"),
                    "webpage_url": (last_info or {}).get("webpage_url") or safe_url,
                    "transcript_source": source_name,
                    "caption_file": str(caption_path),
                    "caption_languages": languages,
                }
                logger.info(
                    "Using YouTube %s transcript segments=%s langs=%s file=%s",
                    source_name,
                    len(transcript),
                    ",".join(languages),
                    caption_path.name,
                )
                return transcript, title, metadata

            logger.info("YouTube %s file was empty after parsing: %s", source_name, caption_path)

    return None


def dependency_status() -> dict:
    ffmpeg = resolve_ffmpeg_binary("ffmpeg")
    ffprobe = resolve_ffmpeg_binary("ffprobe")
    cookiefile = youtube_cookiefile()

    try:
        from yt_dlp.version import __version__ as ytdlp_version
        ytdlp_available = True
    except Exception:
        ytdlp_version = None
        ytdlp_available = False

    return {
        "ffmpeg": {"available": bool(ffmpeg), "configured": bool(settings.FFMPEG_LOCATION)},
        "ffprobe": {"available": bool(ffprobe), "configured": bool(settings.FFMPEG_LOCATION)},
        "yt_dlp": {"available": ytdlp_available, "version": ytdlp_version},
        "cookies_file": {
            "configured": bool(settings.YTDLP_COOKIES_FILE),
            "available": bool(cookiefile),
        },
    }


def classify_ytdlp_error(error_text: str) -> str:
    lowered = error_text.lower()
    if "sign in to confirm" in lowered or "not a bot" in lowered or "confirm you are not a bot" in lowered:
        return "YouTube blocked automated access with bot verification. Configure cookies.txt or upload the media file directly."
    if "cookies" in lowered or "cookie" in lowered:
        return "YouTube requires cookies for this video. Configure YTDLP_COOKIES_FILE or upload the media file directly."
    if "ffmpeg" in lowered and ("not found" in lowered or "not installed" in lowered):
        return "FFmpeg is missing. Install FFmpeg and make sure ffmpeg and ffprobe are available."
    if "immediate exit requested" in lowered or "signal 2" in lowered or "interrupted" in lowered:
        return "The download or FFmpeg conversion was interrupted. Run the backend without --reload for long processing jobs."
    if "timed out" in lowered or "timeout" in lowered:
        return "The YouTube download timed out. Try again on a stable connection or upload the file directly."
    if "file is larger than max-filesize" in lowered or "too large" in lowered:
        return "This video is too large for the configured processing limit."
    if "private video" in lowered or "unavailable" in lowered or "copyright" in lowered:
        return "This YouTube video is unavailable to download. It may be private, region restricted, removed, or copyright blocked."
    return "Could not download audio from YouTube. See backend logs for the exact yt-dlp error."


def _find_downloaded_file(stem: str) -> str:
    search_dirs = [Path(PROCESSED_DIR), Path(TEMP_DIR)]
    for directory in search_dirs:
        preferred = directory / f"{stem}.mp3"
        if preferred.exists() and preferred.stat().st_size > 0:
            return str(preferred)

    matches = []
    for directory in search_dirs:
        matches.extend(directory.glob(f"{stem}.*"))
    matches = sorted(matches, key=lambda item: item.stat().st_mtime, reverse=True)
    for candidate in matches:
        if candidate.is_file() and candidate.stat().st_size > 0:
            return str(candidate)

    raise YouTubeProcessingError(
        "YouTube audio download completed, but the audio file could not be found.",
        log_message=f"No downloaded audio found for stem {stem}",
    )


def download_youtube_audio(url: str, progress_hook=None) -> tuple[str, str, dict]:
    safe_url = validate_youtube_url(url)
    ensure_ffmpeg_available()

    stem = f"yt_{uuid.uuid4().hex}"
    output_template = str(Path(TEMP_DIR) / f"{stem}.%(ext)s")

    logger.info(
        "Starting YouTube download transcode_audio=%s quality=%s",
        settings.YOUTUBE_TRANSCODE_AUDIO,
        settings.YOUTUBE_AUDIO_QUALITY,
    )
    ydl_opts = {
        "format": settings.YOUTUBE_AUDIO_FORMAT,
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "restrictfilenames": True,
        "paths": {"home": TEMP_DIR, "temp": TEMP_DIR},
        "keepvideo": False,
        "outtmpl": {"default": output_template, "pl_thumbnail": ""},
    }
    if settings.YOUTUBE_TRANSCODE_AUDIO:
        ydl_opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": settings.YOUTUBE_AUDIO_QUALITY,
                "nopostoverwrites": False,
            }
        ]
        ydl_opts["postprocessor_args"] = ["-vn"]
        ydl_opts["final_ext"] = "mp3"
    if progress_hook:
        ydl_opts["progress_hooks"] = [progress_hook]
    if settings.YOUTUBE_TRANSCODE_AUDIO:
        ydl_opts["postprocessor_hooks"] = [
            lambda data: progress_hook(data) if progress_hook else None
        ]
    ydl_opts["paths"]["home"] = PROCESSED_DIR
    if settings.FFMPEG_LOCATION:
        ydl_opts["ffmpeg_location"] = settings.FFMPEG_LOCATION
    cookiefile = youtube_cookiefile()
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    elif settings.YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts["cookiesfrombrowser"] = (settings.YTDLP_COOKIES_FROM_BROWSER,)

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(safe_url, download=True)
    except DownloadError as exc:
        logger.exception("yt-dlp failed while downloading YouTube audio")
        error_text = str(exc)
        raise YouTubeProcessingError(classify_ytdlp_error(error_text), log_message=error_text) from exc
    except Exception as exc:
        logger.exception("Unexpected YouTube download error")
        raise YouTubeProcessingError(
            "YouTube audio download failed.",
            log_message=str(exc),
        ) from exc

    file_path = _find_downloaded_file(stem)
    logger.info("YouTube audio downloaded: %s", file_path)
    title = (info or {}).get("title") or "YouTube video"
    title = title.replace("/", "_").replace("\\", "_")[:140]
    metadata = {
        "channel": (info or {}).get("channel") or (info or {}).get("uploader"),
        "duration": (info or {}).get("duration"),
        "thumbnail": (info or {}).get("thumbnail"),
        "webpage_url": (info or {}).get("webpage_url") or safe_url,
    }

    logger.info("YouTube audio ready: title=%s size=%s bytes", title, os.path.getsize(file_path))
    return file_path, title, metadata
