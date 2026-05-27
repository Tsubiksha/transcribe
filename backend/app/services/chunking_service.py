import re
from statistics import mean
from typing import List

from app.core.config import settings
from app.core.logging import logger


SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
MARKDOWN_BOUNDARY = re.compile(r"\n\s*\n+")
CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
BULLET_LINE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+", re.MULTILINE)
TIMESTAMP_TEXT = re.compile(r"(?:\d{1,2}:)?\d{1,2}:\d{2}(?:\.\d{1,3})?")


def _clean_inline(text: str) -> str:
    return re.sub(r"[ \t]+", " ", (text or "").strip())


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    code_weight = 2.6 if _is_code_heavy(text) else 3.8
    return max(1, int(len(text) / code_weight))


def _is_code_heavy(text: str) -> bool:
    if CODE_FENCE.search(text):
        return True
    code_markers = len(re.findall(r"[{}()[\]=;]|=>|def |class |import |const |let |var ", text))
    return code_markers >= 8 or code_markers / max(1, len(text)) > 0.035


def _is_structured(text: str) -> bool:
    return bool(CODE_FENCE.search(text) or BULLET_LINE.search(text) or TIMESTAMP_TEXT.search(text))


def _adaptive_limits(text: str) -> tuple[int, int, int]:
    target_min = max(500, settings.CHUNK_TARGET_MIN_CHARACTERS)
    target_max = max(target_min + 100, settings.CHUNK_TARGET_MAX_CHARACTERS)
    overlap = max(120, min(180, settings.CHUNK_OVERLAP_CHARACTERS))

    if _is_code_heavy(text):
        return 650, 850, max(150, overlap)
    if _is_structured(text):
        return 650, 850, max(150, overlap)
    conversational_max = max(target_max, settings.CHUNK_CONVERSATIONAL_TARGET_MAX)
    conversational_min = max(target_min, conversational_max - 200)
    conversational_overlap = max(120, min(180, settings.CHUNK_CONVERSATIONAL_OVERLAP))
    return conversational_min, conversational_max, conversational_overlap


def _make_unit(text: str, start: float, end: float) -> dict:
    return {
        "text": _clean_inline(text),
        "start": float(start),
        "end": float(end),
        "tokens": _estimate_tokens(text),
    }


def _split_plain_text(text: str) -> list[str]:
    text = _clean_inline(text)
    if not text:
        return []
    if CODE_FENCE.search(text):
        return [text]

    paragraphs = [part.strip() for part in MARKDOWN_BOUNDARY.split(text) if part.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    if BULLET_LINE.search(text):
        return [text]

    sentences = [part.strip() for part in SENTENCE_BOUNDARY.split(text) if part.strip()]
    if len(sentences) > 1:
        return sentences

    return [text]


def _split_long_unit(unit: dict, max_chars: int, safe_tokens: int) -> list[dict]:
    text = unit["text"]
    if len(text) <= max_chars and unit["tokens"] <= safe_tokens:
        return [unit]

    pieces = _split_plain_text(text)
    if len(pieces) == 1:
        logger.warning(
            "Oversized indivisible transcript unit kept intact chars=%s tokens=%s start=%s end=%s",
            len(text),
            _estimate_tokens(text),
            unit["start"],
            unit["end"],
        )
        return [unit]

    total_chars = sum(len(piece) for piece in pieces) or 1
    duration = max(0.01, unit["end"] - unit["start"])
    elapsed = 0.0
    split_units = []
    for piece in pieces:
        part_duration = duration * (len(piece) / total_chars)
        split_units.append(_make_unit(piece, unit["start"] + elapsed, min(unit["end"], unit["start"] + elapsed + part_duration)))
        elapsed += part_duration
    return split_units


def _transcript_to_units(transcript: list[dict]) -> list[dict]:
    units = []
    for segment in transcript:
        text = _clean_inline(segment.get("text", ""))
        if not text:
            continue
        start = float(segment.get("start", 0))
        end = float(segment.get("end", start))
        paragraphs = _split_plain_text(text)
        if len(paragraphs) == 1:
            units.append(_make_unit(text, start, end))
            continue

        total_chars = sum(len(part) for part in paragraphs) or 1
        duration = max(0.01, end - start)
        elapsed = 0.0
        for paragraph in paragraphs:
            part_duration = duration * (len(paragraph) / total_chars)
            units.append(_make_unit(paragraph, start + elapsed, min(end, start + elapsed + part_duration)))
            elapsed += part_duration
    return units


def _overlap_units(units: list[dict], overlap_chars: int) -> list[dict]:
    if not units:
        return []
    selected = []
    total = 0
    for unit in reversed(units):
        if selected and total + len(unit["text"]) > overlap_chars:
            break
        selected.append(unit)
        total += len(unit["text"])
    return list(reversed(selected))


def _append_chunk(
    chunks: list[dict],
    units: list[dict],
    source_id: int,
    user_id: int,
    metadata: dict,
) -> None:
    if not units:
        return
    joiner = "\n\n" if any(_is_structured(unit["text"]) for unit in units) else " "
    text = _clean_inline(joiner.join(unit["text"] for unit in units))
    if not text:
        return
    start = min(unit["start"] for unit in units)
    end = max(unit["end"] for unit in units)
    chunks.append({
        "chunk_text": text,
        "text": text,
        "start_time": round(start, 2),
        "end_time": round(end, 2),
        "start": round(start, 2),
        "end": round(end, 2),
        "source_id": source_id,
        "user_id": user_id,
        "chunk_index": len(chunks),
        "title": metadata.get("title") or "",
        "transcript_source": metadata.get("transcript_source") or metadata.get("source") or "",
        "estimated_tokens": _estimate_tokens(text),
    })


def create_chunks(
    transcript: List[dict],
    source_id: int,
    user_id: int,
    metadata: dict | None = None,
) -> List[dict]:
    if not transcript:
        return []

    metadata = metadata or {}
    raw_units = _transcript_to_units(transcript)
    target_min, target_max, overlap_chars = _adaptive_limits(" ".join(unit["text"] for unit in raw_units[:20]))
    units = []
    safe_tokens = max(240, settings.EMBEDDING_SAFE_TOKEN_LIMIT)
    for unit in raw_units:
        units.extend(_split_long_unit(unit, target_max, safe_tokens))

    chunks = []
    current = []
    current_chars = 0
    current_tokens = 0
    for unit in units:
        unit_chars = len(unit["text"])
        would_exceed_chars = current and current_chars + 1 + unit_chars > target_max
        would_exceed_tokens = current and current_tokens + unit["tokens"] > safe_tokens
        strong_boundary = current and unit["start"] > current[-1]["end"] + max(0, settings.CHUNK_OVERLAP_SECONDS)

        if current and (would_exceed_chars or would_exceed_tokens or strong_boundary) and current_chars >= target_min:
            _append_chunk(chunks, current, source_id, user_id, metadata)
            current = _overlap_units(current, overlap_chars)
            current_chars = sum(len(item["text"]) for item in current)
            current_tokens = sum(item["tokens"] for item in current)

        current.append(unit)
        current_chars += unit_chars + (1 if current_chars else 0)
        current_tokens += unit["tokens"]

    _append_chunk(chunks, current, source_id, user_id, metadata)

    deduped = []
    seen = set()
    for chunk in chunks:
        fingerprint = re.sub(r"\W+", "", chunk["text"].lower())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        chunk["chunk_index"] = len(deduped)
        deduped.append(chunk)

    sizes = [len(chunk["text"]) for chunk in deduped]
    token_estimates = [chunk["estimated_tokens"] for chunk in deduped]
    logger.info(
        "Semantic chunks created count=%s avg_chars=%s min_chars=%s max_chars=%s avg_tokens=%s max_tokens=%s overlap_chars=%s source_id=%s transcript_source=%s",
        len(deduped),
        round(mean(sizes), 1) if sizes else 0,
        min(sizes) if sizes else 0,
        max(sizes) if sizes else 0,
        round(mean(token_estimates), 1) if token_estimates else 0,
        max(token_estimates) if token_estimates else 0,
        overlap_chars,
        source_id,
        metadata.get("transcript_source") or metadata.get("source") or "",
    )
    return deduped
