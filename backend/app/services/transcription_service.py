from faster_whisper import WhisperModel
from pathlib import Path
from time import monotonic
from app.core.config import settings
from app.core.logging import logger
from app.utils.time_utils import seconds_to_timestamp

_model = None


def get_whisper_model() -> WhisperModel:
    global _model
    if _model is None:
        logger.info(
            "Loading faster-whisper model: %s device=%s compute_type=int8 cpu_threads=%s workers=%s",
            settings.WHISPER_MODEL,
            settings.WHISPER_DEVICE,
            settings.WHISPER_CPU_THREADS,
            settings.WHISPER_NUM_WORKERS,
        )
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type="int8",
            cpu_threads=settings.WHISPER_CPU_THREADS,
            num_workers=settings.WHISPER_NUM_WORKERS,
        )
    return _model


def transcribe_audio(audio_path: str, *, job_id: str | None = None, label: str = "media") -> list:
    path = Path(audio_path)
    if not path.exists() or path.stat().st_size == 0:
        raise ValueError("Whisper received a missing or empty audio file.")

    file_size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(
        "Transcription started label=%s job_id=%s file=%s size=%.1fMB",
        label,
        job_id or "-",
        path.name,
        file_size_mb,
    )
    started_at = monotonic()
    segments, info = get_whisper_model().transcribe(
        audio_path,
        beam_size=settings.WHISPER_BEAM_SIZE,
        best_of=1,
        temperature=0,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": settings.WHISPER_VAD_MIN_SILENCE_MS,
            "speech_pad_ms": settings.WHISPER_VAD_SPEECH_PAD_MS,
        },
    )
    
    transcript = []
    last_logged_second = 0.0
    for segment in segments:
        transcript.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })
        if segment.end - last_logged_second >= 300:
            last_logged_second = segment.end
            logger.info(
                "Transcribing label=%s job_id=%s reached=%s segments=%s elapsed=%.1fs",
                label,
                job_id or "-",
                seconds_to_timestamp(segment.end),
                len(transcript),
                monotonic() - started_at,
            )
    
    logger.info(
        "Transcription completed label=%s job_id=%s segments=%s language=%s duration=%s elapsed=%.1fs",
        label,
        job_id or "-",
        len(transcript),
        getattr(info, "language", None),
        seconds_to_timestamp(getattr(info, "duration", 0) or 0),
        monotonic() - started_at,
    )
    return transcript
