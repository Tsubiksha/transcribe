import requests
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import logger


def generate_with_ollama(prompt: str, stream: bool = False) -> str:
    url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": stream,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Ollama request failed")
        detail = (
            f"Ollama request failed at {settings.OLLAMA_BASE_URL} using model "
            f"{settings.OLLAMA_MODEL}. Make sure Ollama is running and the model "
            "appears in `ollama list`."
        )
        if exc.response is not None:
            try:
                error_detail = exc.response.json().get("error")
            except ValueError:
                error_detail = exc.response.text
            if error_detail:
                detail = f"{detail} Ollama said: {error_detail}"
        raise HTTPException(
            status_code=503,
            detail=detail,
        ) from exc

    answer = response.json().get("response", "").strip()
    if not answer:
        return "I could not find this information in the uploaded content."
    return answer
