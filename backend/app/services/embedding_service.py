import re
import time

import requests

from app.core.config import settings
from app.core.logging import logger


MODEL_NAME = settings.OLLAMA_EMBEDDING_MODEL
CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
PARAGRAPH_BOUNDARY = re.compile(r"\n\s*\n+")
BULLET_BOUNDARY = re.compile(r"\n(?=\s*(?:[-*+]|\d+[.)])\s+)")


def _ollama_url(path: str) -> str:
    return f"{settings.OLLAMA_BASE_URL.rstrip('/')}{path}"


def estimate_token_count(text: str) -> int:
    if not text:
        return 0
    code_markers = len(re.findall(r"[{}()[\]=;]|=>|def |class |import |const |let |var ", text))
    divisor = 2.6 if CODE_FENCE.search(text) or code_markers >= 8 else 3.8
    return max(1, int(len(text) / divisor))


def _post_ollama(path: str, payload: dict) -> dict:
    try:
        response = requests.post(
            _ollama_url(path),
            json=payload,
            timeout=settings.OLLAMA_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        ollama_detail = ""
        if exc.response is not None:
            try:
                ollama_detail = exc.response.json().get("error") or exc.response.text
            except ValueError:
                ollama_detail = exc.response.text
        logger.exception(
            "Ollama embedding request failed model=%s path=%s detail=%s",
            MODEL_NAME,
            path,
            ollama_detail,
        )
        raise RuntimeError(
            f"Ollama embedding request failed at {settings.OLLAMA_BASE_URL} using model "
            f"{MODEL_NAME}. Make sure Ollama is running and the model appears in `ollama list`."
            f"{' Ollama said: ' + ollama_detail if ollama_detail else ''}"
        ) from exc


def _normalize_embeddings(value) -> list[list[float]]:
    if not value:
        return []
    if isinstance(value[0], (int, float)):
        return [value]
    return value


def _generate_single_with_embed_api(text: str) -> list[float]:
    started_at = time.perf_counter()
    data = _post_ollama("/api/embed", {"model": MODEL_NAME, "input": text})
    embeddings = _normalize_embeddings(data.get("embeddings") or data.get("embedding"))
    latency_ms = round((time.perf_counter() - started_at) * 1000, 1)
    if len(embeddings) != 1:
        raise RuntimeError(f"Ollama returned {len(embeddings)} embeddings for one input.")
    logger.debug(
        "Ollama embedding completed model=%s chars=%s estimated_tokens=%s latency_ms=%s",
        MODEL_NAME,
        len(text),
        estimate_token_count(text),
        latency_ms,
    )
    return embeddings[0]


def _clean_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", (text or "").strip())


def _protected_blocks(text: str) -> list[str]:
    blocks = []
    cursor = 0
    for match in CODE_FENCE.finditer(text):
        before = text[cursor:match.start()]
        blocks.extend(_split_non_code(before))
        blocks.append(match.group(0).strip())
        cursor = match.end()
    blocks.extend(_split_non_code(text[cursor:]))
    return [block for block in blocks if block.strip()]


def _split_non_code(text: str) -> list[str]:
    blocks = []
    for paragraph in PARAGRAPH_BOUNDARY.split(text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        bullet_parts = [part.strip() for part in BULLET_BOUNDARY.split(paragraph) if part.strip()]
        if len(bullet_parts) > 1:
            blocks.extend(bullet_parts)
        else:
            blocks.append(paragraph)
    return blocks


def _semantic_split(text: str) -> list[str]:
    text = _clean_text(text)
    if not text:
        return []

    blocks = _protected_blocks(text)
    pieces = []
    for block in blocks:
        if CODE_FENCE.fullmatch(block) or BULLET_BOUNDARY.search("\n" + block):
            pieces.append(block)
            continue
        sentences = [sentence.strip() for sentence in SENTENCE_BOUNDARY.split(block) if sentence.strip()]
        pieces.extend(sentences if len(sentences) > 1 else [block])
    return pieces


def _split_by_token_limit(text: str, token_limit: int) -> list[str]:
    clean = _clean_text(text)
    if estimate_token_count(clean) <= token_limit:
        return [clean]

    pieces = _semantic_split(clean)
    if len(pieces) <= 1:
        lines = [line.rstrip() for line in clean.splitlines() if line.strip()]
        if len(lines) > 1:
            grouped_lines = []
            current_lines = []
            for line in lines:
                candidate = "\n".join(current_lines + [line])
                if current_lines and estimate_token_count(candidate) > token_limit:
                    grouped_lines.append("\n".join(current_lines))
                    current_lines = [line]
                else:
                    current_lines.append(line)
            if current_lines:
                grouped_lines.append("\n".join(current_lines))
            return [
                part
                for group in grouped_lines
                for part in _split_by_token_limit(group, max(settings.EMBEDDING_MIN_RETRY_TOKEN_LIMIT, int(token_limit * 0.75)))
                if part.strip()
            ]

        midpoint = len(clean) // 2
        split_at = clean.rfind(" ", 0, midpoint)
        if split_at <= 0:
            split_at = clean.find(" ", midpoint)
        if split_at <= 0:
            split_at = midpoint
        return [
            part
            for half in (clean[:split_at], clean[split_at:])
            for part in _split_by_token_limit(half, max(settings.EMBEDDING_MIN_RETRY_TOKEN_LIMIT, token_limit // 2))
            if part.strip()
        ]

    grouped = []
    current = []
    for piece in pieces:
        candidate = _clean_text(" ".join(current + [piece]))
        if current and estimate_token_count(candidate) > token_limit:
            grouped.append(_clean_text(" ".join(current)))
            current = [piece]
        else:
            current.append(piece)
    if current:
        grouped.append(_clean_text(" ".join(current)))

    safe_parts = []
    smaller_limit = max(settings.EMBEDDING_MIN_RETRY_TOKEN_LIMIT, int(token_limit * 0.75))
    for part in grouped:
        if estimate_token_count(part) > token_limit and smaller_limit < token_limit:
            safe_parts.extend(_split_by_token_limit(part, smaller_limit))
        else:
            safe_parts.append(part)
    return [part for part in safe_parts if part]


def _average_embeddings(embeddings: list[list[float]]) -> list[float]:
    if not embeddings:
        return []
    dimensions = len(embeddings[0])
    if dimensions == 0:
        return []
    return [
        sum(vector[index] for vector in embeddings if len(vector) > index) / len(embeddings)
        for index in range(dimensions)
    ]


def _embed_single_safe(text: str, token_limit: int | None = None, depth: int = 0) -> list[float]:
    token_limit = token_limit or max(240, settings.EMBEDDING_SAFE_TOKEN_LIMIT)
    clean = _clean_text(text)
    parts = _split_by_token_limit(clean, token_limit)

    if len(parts) > 1:
        logger.warning(
            "Embedding input split for token safety chars=%s estimated_tokens=%s parts=%s token_limit=%s depth=%s",
            len(clean),
            estimate_token_count(clean),
            len(parts),
            token_limit,
            depth,
        )
        return _average_embeddings([_embed_single_safe(part, token_limit, depth + 1) for part in parts])

    try:
        return _generate_single_with_embed_api(clean)
    except RuntimeError:
        next_limit = max(settings.EMBEDDING_MIN_RETRY_TOKEN_LIMIT, int(token_limit * 0.65))
        if next_limit >= token_limit or depth >= 5:
            logger.exception(
                "Embedding failed after overflow retries chars=%s estimated_tokens=%s token_limit=%s depth=%s",
                len(clean),
                estimate_token_count(clean),
                token_limit,
                depth,
            )
            raise
        logger.warning(
            "Retrying failed embedding with smaller token limit chars=%s estimated_tokens=%s old_limit=%s new_limit=%s depth=%s",
            len(clean),
            estimate_token_count(clean),
            token_limit,
            next_limit,
            depth,
        )
        return _embed_single_safe(clean, next_limit, depth + 1)


def generate_embedding(text: str) -> list:
    clean = _clean_text(text)
    logger.debug(
        "Generating single embedding chars=%s estimated_tokens=%s model=%s",
        len(clean),
        estimate_token_count(clean),
        MODEL_NAME,
    )
    return _embed_single_safe(clean)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    clean_texts = [_clean_text(text) for text in texts]
    token_estimates = [estimate_token_count(text) for text in clean_texts]
    logger.debug(
        "Generating embeddings count=%s avg_chars=%s max_chars=%s avg_tokens=%s max_tokens=%s batch_size=%s model=%s",
        len(clean_texts),
        round(sum(len(text) for text in clean_texts) / len(clean_texts), 1),
        max(len(text) for text in clean_texts),
        round(sum(token_estimates) / len(token_estimates), 1),
        max(token_estimates),
        settings.EMBEDDING_BATCH_SIZE,
        MODEL_NAME,
    )

    embeddings = []
    for index, text in enumerate(clean_texts):
        try:
            embeddings.append(_embed_single_safe(text))
        except RuntimeError:
            logger.exception(
                "Single-text embedding failed index=%s chars=%s estimated_tokens=%s model=%s",
                index,
                len(text),
                estimate_token_count(text),
                MODEL_NAME,
            )
            raise
    if len(embeddings) != len(clean_texts):
        raise RuntimeError(
            f"Ollama returned {len(embeddings)} embeddings for {len(clean_texts)} transcript chunks."
        )
    return embeddings
