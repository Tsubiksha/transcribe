import os
from pathlib import Path
import ffmpeg
from app.core.config import settings
from app.core.logging import logger
from app.utils.file_utils import PROCESSED_DIR, UPLOAD_DIR

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _ffmpeg_command(name: str) -> str:
    if not settings.FFMPEG_LOCATION:
        return name

    base = Path(settings.FFMPEG_LOCATION)
    candidates = [
        base / f"{name}.exe",
        base / "bin" / f"{name}.exe",
        base / name,
        base / "bin" / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return name


def extract_audio(video_path: str) -> str:
    logger.info(f"Extracting audio from: {video_path}")
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        raise ValueError("Uploaded video file is missing or empty.")
    filename = os.path.splitext(os.path.basename(video_path))[0]
    output_audio_path = os.path.join(PROCESSED_DIR, f"{filename}.whisper.wav")

    try:
        ffmpeg.input(video_path).output(
            output_audio_path,
            format="wav",
            acodec="pcm_s16le",
            ac=1,
            ar=16000,
            vn=None,
        ).run(cmd=_ffmpeg_command("ffmpeg"), overwrite_output=True, quiet=True)
    except ffmpeg.Error as exc:
        logger.exception("FFmpeg audio extraction failed")
        stderr = (exc.stderr or b"").decode(errors="ignore") if hasattr(exc, "stderr") else ""
        if "Immediate exit requested" in stderr or "signal 2" in stderr.lower():
            raise ValueError("FFmpeg conversion was interrupted. Run the backend without --reload for long processing jobs.") from exc
        raise ValueError("Audio extraction failed. Check that FFmpeg is installed and the video file is valid.") from exc

    if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
        raise ValueError("Audio extraction failed. FFmpeg did not create a valid mp3 file.")

    logger.info(f"Audio extracted to: {output_audio_path}")
    return output_audio_path


def prepare_audio_for_whisper(audio_path: str) -> str:
    if not settings.WHISPER_PREPARE_AUDIO:
        return audio_path
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise ValueError("Audio file is missing or empty.")

    source = Path(audio_path)
    if source.suffix.lower() == ".wav" and source.name.endswith(".whisper.wav"):
        return audio_path

    output_audio_path = os.path.join(PROCESSED_DIR, f"{source.stem}.whisper.wav")
    output = Path(output_audio_path)
    if output.exists() and output.stat().st_size > 0 and output.stat().st_mtime >= source.stat().st_mtime:
        return output_audio_path

    logger.info("Preparing audio for Whisper: %s", audio_path)
    try:
        ffmpeg.input(audio_path).output(
            output_audio_path,
            format="wav",
            acodec="pcm_s16le",
            ac=1,
            ar=16000,
            vn=None,
        ).run(cmd=_ffmpeg_command("ffmpeg"), overwrite_output=True, quiet=True)
    except ffmpeg.Error as exc:
        logger.exception("FFmpeg Whisper audio preparation failed")
        stderr = (exc.stderr or b"").decode(errors="ignore") if hasattr(exc, "stderr") else ""
        if "Immediate exit requested" in stderr or "signal 2" in stderr.lower():
            raise ValueError("FFmpeg conversion was interrupted. Run the backend without --reload for long processing jobs.") from exc
        raise ValueError("Audio preparation failed. Check that FFmpeg is installed and the audio file is valid.") from exc

    if not output.exists() or output.stat().st_size == 0:
        raise ValueError("Audio preparation failed. FFmpeg did not create a valid audio file.")

    logger.info("Whisper-ready audio created: %s", output_audio_path)
    return output_audio_path


def get_audio_duration(file_path: str) -> float:
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        raise ValueError("Audio/video file is missing or empty.")
    probe = ffmpeg.probe(file_path, cmd=_ffmpeg_command("ffprobe"))
    return float(probe["format"]["duration"])
