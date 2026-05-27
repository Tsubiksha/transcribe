import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import Callable, List
import chromadb
from app.core.config import settings
from app.services.embedding_service import estimate_token_count, generate_embedding
from app.core.logging import logger

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)
collection = client.get_or_create_collection(name=settings.CHROMA_COLLECTION_NAME)


def store_chunks(
    chunks: List[dict],
    source_id: int,
    user_id: int,
    progress_callback: Callable[[int, int], None] | None = None,
) -> int:
    if not chunks:
        logger.warning("No chunks supplied for storage source_id=%s user_id=%s", source_id, user_id)
        return 0

    records = []
    seen_fingerprints = set()
    for chunk in chunks:
        text = chunk.get("chunk_text") or chunk["text"]
        if not text.strip():
            continue
        fingerprint = " ".join(text.lower().split())
        if fingerprint in seen_fingerprints:
            logger.info(
                "Skipping duplicate chunk before embedding source_id=%s chunk_index=%s chars=%s",
                source_id,
                chunk.get("chunk_index"),
                len(text),
            )
            continue
        seen_fingerprints.add(fingerprint)
        records.append({
            "id": f"source_{source_id}_chunk_{chunk['chunk_index']}_{uuid.uuid4().hex}",
            "document": text,
            "metadata": {
                "source_id": str(source_id),
                "user_id": str(user_id),
                "start": str(chunk["start_time"]),
                "end": str(chunk["end_time"]),
                "chunk_index": int(chunk["chunk_index"]),
                "title": str(chunk.get("title") or ""),
                "transcript_source": str(chunk.get("transcript_source") or ""),
                "estimated_tokens": int(chunk.get("estimated_tokens") or estimate_token_count(text)),
            },
        })

    if not records:
        logger.warning("All chunks were empty source_id=%s user_id=%s", source_id, user_id)
        return 0

    total = len(records)
    write_batch_size = max(1, min(settings.EMBEDDING_WRITE_BATCH_SIZE, 16))
    concurrency = max(1, min(settings.EMBEDDING_CONCURRENCY, 6))
    log_every = max(1, settings.EMBEDDING_LOG_EVERY)
    lengths = [len(item["document"]) for item in records]
    token_estimates = [item["metadata"]["estimated_tokens"] for item in records]
    logger.info(
        "Generating and storing embeddings chunks=%s concurrency=%s write_batch_size=%s avg_chars=%s max_chars=%s avg_tokens=%s max_tokens=%s source_id=%s",
        total,
        concurrency,
        write_batch_size,
        round(sum(lengths) / len(lengths), 1),
        max(lengths),
        round(sum(token_estimates) / len(token_estimates), 1),
        max(token_estimates),
        source_id,
    )

    delete_source_chunks(source_id, user_id)

    stored = 0
    processed = 0
    failed = 0
    latency_samples: list[float] = []
    pending: list[dict] = []

    def flush_pending() -> None:
        nonlocal stored
        if not pending:
            return
        collection.add(
            ids=[item["id"] for item in pending],
            documents=[item["document"] for item in pending],
            embeddings=[item["embedding"] for item in pending],
            metadatas=[item["metadata"] for item in pending],
        )
        stored += len(pending)
        logger.info(
            "Stored embedding micro-batch source_id=%s batch_size=%s stored=%s processed=%s failed=%s total=%s",
            source_id,
            len(pending),
            stored,
            processed,
            failed,
            total,
        )
        pending.clear()

    def embed_record(record: dict) -> dict:
        started_at = time.perf_counter()
        embedding = generate_embedding(record["document"])
        latency_ms = round((time.perf_counter() - started_at) * 1000, 1)
        return {**record, "embedding": embedding, "latency_ms": latency_ms}

    next_index = 0
    next_write_index = 0
    active = {}
    completed_by_index = {}
    failed_indexes = set()

    def drain_completed() -> None:
        nonlocal next_write_index
        while next_write_index in failed_indexes:
            failed_indexes.remove(next_write_index)
            next_write_index += 1
        while next_write_index in completed_by_index:
            pending.append(completed_by_index.pop(next_write_index))
            next_write_index += 1
            if len(pending) >= write_batch_size:
                flush_pending()
            while next_write_index in failed_indexes:
                failed_indexes.remove(next_write_index)
                next_write_index += 1

    with ThreadPoolExecutor(max_workers=concurrency, thread_name_prefix="ollama-embed") as executor:
        while next_index < total or active:
            while next_index < total and len(active) < concurrency:
                future = executor.submit(embed_record, records[next_index])
                active[future] = next_index
                next_index += 1

            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                record_index = active.pop(future)
                processed += 1
                try:
                    completed = future.result()
                except Exception:
                    failed += 1
                    failed_indexes.add(record_index)
                    record = records[record_index]
                    logger.exception(
                        "Skipping failed chunk embedding source_id=%s chunk_index=%s chars=%s estimated_tokens=%s processed=%s total=%s",
                        source_id,
                        record["metadata"]["chunk_index"],
                        len(record["document"]),
                        record["metadata"]["estimated_tokens"],
                        processed,
                        total,
                    )
                    if progress_callback:
                        progress_callback(processed, total)
                    drain_completed()
                    continue

                completed_by_index[record_index] = completed
                latency_samples.append(completed["latency_ms"])
                if processed % log_every == 0 or processed == total:
                    recent = latency_samples[-log_every:]
                    logger.info(
                        "Embedding progress source_id=%s processed=%s stored=%s failed=%s total=%s avg_latency_ms=%s max_latency_ms=%s concurrency=%s",
                        source_id,
                        processed,
                        stored,
                        failed,
                        total,
                        round(sum(recent) / len(recent), 1),
                        max(recent),
                        concurrency,
                    )
                if progress_callback:
                    progress_callback(processed, total)

                drain_completed()

    drain_completed()

    flush_pending()

    logger.info(
        "Stored %s chunks in ChromaDB skipped_failed=%s source_id=%s avg_latency_ms=%s max_latency_ms=%s",
        stored,
        failed,
        source_id,
        round(sum(latency_samples) / len(latency_samples), 1) if latency_samples else 0,
        max(latency_samples) if latency_samples else 0,
    )
    stored_count = count_source_chunks(source_id, user_id)
    logger.info("Verified %s chunks in ChromaDB for source %s", stored_count, source_id)
    return stored_count


def search_chunks(question: str, source_id: int, user_id: int, top_k: int = 3) -> dict:
    query_embedding = generate_embedding(question)
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={
            "$and": [
                {"source_id": str(source_id)},
                {"user_id": str(user_id)}
            ]
        }
    )
    
    return results


def get_source_chunks(source_id: int, user_id: int) -> list[dict]:
    results = collection.get(
        where={
            "$and": [
                {"source_id": str(source_id)},
                {"user_id": str(user_id)}
            ]
        },
        include=["documents", "metadatas"],
    )
    documents = results.get("documents") or []
    metadatas = results.get("metadatas") or []
    chunks = []
    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        chunks.append({
            "text": document,
            "start": float(metadata.get("start", 0)),
            "end": float(metadata.get("end", 0)),
            "chunk_index": int(metadata.get("chunk_index", index)),
            "title": metadata.get("title", ""),
            "transcript_source": metadata.get("transcript_source", ""),
            "estimated_tokens": int(metadata.get("estimated_tokens", 0)),
        })
    return sorted(chunks, key=lambda item: item["chunk_index"])


def delete_source_chunks(source_id: int, user_id: int) -> None:
    all_chunks = collection.get(where={
        "$and": [{"source_id": str(source_id)}, {"user_id": str(user_id)}]
    })
    if all_chunks["ids"]:
        collection.delete(ids=all_chunks["ids"])
        logger.info(f"Deleted {len(all_chunks['ids'])} chunks for source {source_id}")


def count_source_chunks(source_id: int, user_id: int) -> int:
    all_chunks = collection.get(where={
        "$and": [{"source_id": str(source_id)}, {"user_id": str(user_id)}]
    })
    return len(all_chunks.get("ids") or [])
