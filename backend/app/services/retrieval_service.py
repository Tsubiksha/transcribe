import math
import re
from collections import Counter

from app.services.vector_store_service import get_source_chunks, search_chunks


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text or "") if len(token) > 1]


def _bm25_scores(question: str, chunks: list[dict]) -> dict[int, float]:
    query_terms = _tokens(question)
    if not query_terms or not chunks:
        return {}

    doc_tokens = [_tokens(chunk["text"]) for chunk in chunks]
    doc_freq = Counter()
    for tokens in doc_tokens:
        doc_freq.update(set(tokens))

    avg_len = sum(len(tokens) for tokens in doc_tokens) / max(1, len(doc_tokens))
    query_counts = Counter(query_terms)
    scores = {}
    k1 = 1.5
    b = 0.75

    for chunk, tokens in zip(chunks, doc_tokens):
        if not tokens:
            continue
        counts = Counter(tokens)
        score = 0.0
        for term, query_weight in query_counts.items():
            tf = counts.get(term, 0)
            if not tf:
                continue
            idf = math.log(1 + (len(chunks) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5))
            denom = tf + k1 * (1 - b + b * (len(tokens) / max(1, avg_len)))
            score += query_weight * idf * ((tf * (k1 + 1)) / denom)
        if score:
            scores[chunk["chunk_index"]] = score
    return scores


def _normalize(values: dict[int, float], reverse: bool = False) -> dict[int, float]:
    if not values:
        return {}
    if reverse:
        values = {key: -value for key, value in values.items()}
    low = min(values.values())
    high = max(values.values())
    if high == low:
        return {key: 1.0 for key in values}
    return {key: (value - low) / (high - low) for key, value in values.items()}


def retrieve_relevant_chunks(question: str, source_id: int, user_id: int, top_k: int = 8) -> list[dict]:
    vector_limit = max(top_k * 3, 12)
    results = search_chunks(question, source_id, user_id, top_k=vector_limit)
    documents = results.get("documents", [[]])[0] or []
    metadatas = results.get("metadatas", [[]])[0] or []
    distances = results.get("distances", [[]])[0] or []

    vector_chunks = []
    vector_distances = {}
    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        chunk_index = int(metadata.get("chunk_index", index))
        vector_distances[chunk_index] = distance if isinstance(distance, (int, float)) else 1.0
        vector_chunks.append({
            "text": document,
            "start": float(metadata.get("start", 0)),
            "end": float(metadata.get("end", 0)),
            "chunk_index": chunk_index,
            "distance": distance,
            "confidence_score": round(max(0, 1 - distance), 2) if isinstance(distance, (int, float)) else None,
        })

    source_chunks = get_source_chunks(source_id, user_id)
    source_by_index = {chunk["chunk_index"]: chunk for chunk in source_chunks}
    keyword_scores = _bm25_scores(question, source_chunks)
    normalized_vector = _normalize(vector_distances, reverse=True)
    normalized_keyword = _normalize(keyword_scores)

    candidate_indexes = set(normalized_vector) | set(normalized_keyword)
    for index in list(candidate_indexes):
        if index - 1 in source_by_index:
            candidate_indexes.add(index - 1)
        if index + 1 in source_by_index:
            candidate_indexes.add(index + 1)

    ranked = []
    for chunk_index in candidate_indexes:
        source_chunk = source_by_index.get(chunk_index)
        if not source_chunk:
            continue
        vector_score = normalized_vector.get(chunk_index, 0.0)
        keyword_score = normalized_keyword.get(chunk_index, 0.0)
        neighbor_boost = 0.08 if chunk_index not in normalized_vector and chunk_index not in normalized_keyword else 0.0
        score = (0.68 * vector_score) + (0.32 * keyword_score) + neighbor_boost
        distance = vector_distances.get(chunk_index)
        ranked.append({
            **source_chunk,
            "distance": distance,
            "keyword_score": round(keyword_score, 3),
            "hybrid_score": round(score, 3),
            "confidence_score": round(score, 2),
        })

    return sorted(ranked, key=lambda item: item["hybrid_score"], reverse=True)[:top_k]


def select_answer_chunks(chunks: list[dict], limit: int = 5) -> list[dict]:
    if not chunks:
        return []

    selected = []
    seen_indexes = set()
    for chunk in chunks:
        chunk_index = chunk.get("chunk_index")
        if chunk_index in seen_indexes:
            continue
        selected.append(chunk)
        seen_indexes.add(chunk_index)
        if len(selected) >= limit:
            break
    return selected
