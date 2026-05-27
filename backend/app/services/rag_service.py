from app.services.ollama_service import generate_with_ollama
from app.services.prompt_builder_service import build_rag_prompt
from app.services.retrieval_service import retrieve_relevant_chunks, select_answer_chunks
from app.utils.time_utils import seconds_to_timestamp

ASSISTANT_IDENTITY = (
    "I'm your AI Timestamp Assistant. I answer questions related to your uploaded media "
    "and processed YouTube videos using timestamp-based retrieval."
)
NOT_FOUND = "This information is not available in the processed media source."
GREETING_RESPONSE = (
    "Hi! I'm ready to help with this media source. Ask me for a summary, key points, "
    "definitions, steps, examples, or anything specific you want to find in the transcript."
)


def _is_identity_question(question: str) -> bool:
    normalized = question.strip().lower().rstrip("?.! ")
    return normalized in {"who are you", "what can you do"}


def _is_greeting(question: str) -> bool:
    normalized = question.strip().lower().rstrip("!. ")
    greetings = {
        "hi",
        "hello",
        "hey",
        "hii",
        "helo",
        "good morning",
        "good afternoon",
        "good evening",
        "namaste",
    }
    return normalized in greetings or normalized.startswith(("hi ", "hello ", "hey "))


def _wants_detailed_answer(question: str) -> bool:
    lowered = question.lower()
    return any(
        term in lowered
        for term in (
            "detail",
            "detailed",
            "deep",
            "fully",
            "complete",
            "comprehensive",
            "explain",
            "explanation",
            "step by step",
            "everything",
            "very long",
            "long answer",
        )
    )


def generate_answer(
    question: str,
    source_id: int,
    user_id: int,
    source_title: str,
    recent_history: list[dict] | None = None,
) -> dict:
    if _is_greeting(question):
        return {
            "answer": GREETING_RESPONSE,
            "timestamps": [],
            "source": source_title,
            "source_id": source_id,
            "start_time": None,
            "end_time": None,
            "matched_text": None,
            "confidence_score": 1.0,
        }

    detailed = _wants_detailed_answer(question)
    retrieved_chunks = retrieve_relevant_chunks(question, source_id, user_id, top_k=18 if detailed else 12)
    chunks = select_answer_chunks(retrieved_chunks, limit=8 if detailed else 5)

    if _is_identity_question(question):
        best_chunk = chunks[0] if chunks else {}
        return {
            "answer": ASSISTANT_IDENTITY,
            "timestamps": [],
            "source": source_title,
            "source_id": source_id,
            "start_time": best_chunk.get("start"),
            "end_time": best_chunk.get("end"),
            "matched_text": "\n\n".join(chunk["text"] for chunk in chunks[:3]) if chunks else None,
            "confidence_score": best_chunk.get("confidence_score", 1.0),
        }

    if not chunks:
        return {
            "answer": NOT_FOUND,
            "timestamps": [],
            "source": source_title,
            "source_id": source_id,
            "start_time": None,
            "end_time": None,
            "matched_text": None,
            "confidence_score": 0.0,
        }

    prompt = build_rag_prompt(question, chunks, source_title, recent_history)
    answer = generate_with_ollama(prompt)
    if NOT_FOUND.lower() in answer.lower():
        answer = NOT_FOUND

    best_chunk = chunks[0]
    timestamps = [{
        "start": seconds_to_timestamp(best_chunk["start"]),
        "end": seconds_to_timestamp(best_chunk["end"]),
        "start_seconds": best_chunk["start"],
        "end_seconds": best_chunk["end"],
    }]

    return {
        "answer": answer,
        "timestamps": timestamps,
        "source": source_title,
        "source_id": source_id,
        "start_time": best_chunk["start"],
        "end_time": best_chunk["end"],
        "matched_text": "\n\n".join(
            f"[{seconds_to_timestamp(chunk['start'])} - {seconds_to_timestamp(chunk['end'])}] {chunk['text']}"
            for chunk in chunks
        ),
        "confidence_score": best_chunk.get("confidence_score"),
    }
