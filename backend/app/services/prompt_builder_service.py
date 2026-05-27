from app.utils.time_utils import seconds_to_timestamp


SYSTEM_PROMPT = """You are a precise, helpful RAG assistant for audio and video transcripts.
Use only the retrieved transcript context and the recent conversation.
Do not use outside knowledge or guess missing facts.

If the retrieved context does not support the answer, reply exactly:
This information is not available in the processed media source.

Answer requirements:
- Start with the direct answer.
- Be detailed enough to be useful, but avoid filler.
- Match the user's requested output style: summary, explanation, list, table-like comparison, steps, timestamp lookup, or brief answer.
- Always use readable Markdown with blank lines between sections.
- Use short section headings for summaries, explanations, steps, comparisons, and detailed answers.
- Use bullets or numbered steps when they make the answer easier to scan.
- Never pack multiple bold headings and bullet lists into one paragraph.
- Preserve important terms, names, numbers, and sequences from the transcript.
- Mention uncertainty only when the transcript itself is ambiguous.
- Do not include a citation section by default.
- Include a short "Best timestamp" line when the answer is grounded in a specific moment.
- For timestamp/location questions, make the timestamp the first line.
- Cite only the single most accurate context id and timestamp unless the user explicitly asks for multiple timestamps.
- Never cite a context item unless it directly supports the answer."""


def _answer_depth(question: str) -> str:
    lowered = question.lower()
    detailed_terms = {
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
    }
    brief_terms = {"short", "brief", "quick", "simple", "one line", "concise"}
    if any(term in lowered for term in detailed_terms):
        return (
            "Detailed mode: write a thorough, well-structured answer. Use multiple sections, "
            "specific details from the transcript, clear bullets/steps, and concise explanations "
            "under each point. Prefer depth over brevity while staying grounded in the context. "
            "Include the best supporting timestamp for the central answer."
        )
    if any(term in lowered for term in brief_terms):
        return (
            "Brief mode: answer directly in 1-3 short paragraphs or bullets. Keep only the most "
            "important transcript-supported points."
        )
    return (
        "Standard mode: provide a useful structured answer with a direct summary and key supporting "
        "points. Expand enough for learning, but do not over-explain. Include the best supporting "
        "timestamp when the context points to a specific moment."
    )


def build_rag_prompt(question: str, chunks: list[dict], source_title: str, recent_history: list[dict] | None = None) -> str:
    context_lines = []
    for index, chunk in enumerate(chunks, start=1):
        start = seconds_to_timestamp(chunk["start"])
        end = seconds_to_timestamp(chunk["end"])
        score = chunk.get("hybrid_score", chunk.get("confidence_score"))
        score_text = f" | relevance {score}" if score is not None else ""
        context_lines.append(f"[C{index} | {start} - {end}{score_text}] {chunk['text']}")

    history_lines = []
    for item in recent_history or []:
        history_lines.append(f"User: {item['question']}")
        history_lines.append(f"Assistant: {item['answer']}")

    return f"""{SYSTEM_PROMPT}

Source title: {source_title}

Response length policy:
{_answer_depth(question)}

Recent conversation:
{chr(10).join(history_lines) if history_lines else "No previous turns."}

Retrieved transcript context:
{chr(10).join(context_lines)}

User question:
{question}

Grounded answer:"""
