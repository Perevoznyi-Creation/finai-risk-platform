"""RAG service — Retrieval Augmented Generation over uploaded documents."""

from openai import OpenAI
import time
import structlog

from app.core.config import get_settings
from app.repositories.document_repo import DocumentRepository
from app.repositories.models import DocumentChunk
from app.services.embeddings import embed_text
from app.services.metrics_logger import log_llm_metric

logger = structlog.get_logger()

_TOP_K = 5           # number of chunks to retrieve
_MAX_CONTEXT_CHARS = 3000  # cap total context injected into the prompt

_SYSTEM_PROMPT = """\
You are a financial analyst assistant. You answer questions strictly based on
the provided document excerpts. If the answer cannot be found in the excerpts,
say "I could not find this information in the provided document."
Do not make up facts. Do not give investment advice.
"""


def _build_context(chunks: list[DocumentChunk]) -> str:
    """Concatenate retrieved chunks into a single context string.

    Chunks are numbered so the model can refer to them as sources.
    Total length is capped to avoid exceeding the model's context window.
    """
    parts: list[str] = []
    total = 0
    for i, chunk in enumerate(chunks, start=1):
        entry = f"[{i}] {chunk.chunk_text.strip()}"
        if total + len(entry) > _MAX_CONTEXT_CHARS:
            break
        parts.append(entry)
        total += len(entry)
    return "\n\n".join(parts)


def answer_question(
    question: str,
    document_id: int,
    repo: DocumentRepository,
) -> tuple[str, list[str]]:
    """Answer a question using RAG over a specific document.

    Steps:
    1. Embed the question locally.
    2. Retrieve the top-k most similar chunks from the document.
    3. Inject the chunks as context into a Groq LLM prompt.
    4. Return the answer and the source chunk texts.

    Args:
        question: The user's question about the document.
        document_id: ID of the document to search within.
        repo: DocumentRepository bound to an active session.

    Returns:
        Tuple of ``(answer_text, source_chunks)`` where ``source_chunks``
        is the list of raw chunk texts used to build the context.

    Raises:
        ValueError: If no chunks are found for the document, or Groq key missing.
    """
    settings = get_settings()

    if not settings.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file to use this endpoint."
        )

    query_embedding = embed_text(question)

    chunks = repo.search_chunks_by_embedding(
        embedding=query_embedding,
        document_id=document_id,
        limit=_TOP_K,
    )

    if not chunks:
        raise ValueError(
            f"No embedded chunks found for document {document_id}. "
            "Make sure the document was uploaded and ingested successfully."
        )

    context = _build_context(chunks)
    sources = [c.chunk_text.strip() for c in chunks]

    user_message = (
        f"Document excerpts:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer based only on the excerpts above."
    )

    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    start = time.time()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=500,
        temperature=0.2,
    )
    duration = time.time() - start

    answer = response.choices[0].message.content.strip()

    usage = None
    try:
        usage = getattr(response, "usage", None) or response.get("usage")
    except Exception:
        usage = None

    logger.info(
        "rag.answer",
        document_id=document_id,
        question_len=len(question),
        chunks_retrieved=len(chunks),
        model=settings.groq_model,
        duration_seconds=round(duration, 3),
        answer_length=len(answer),
        usage=usage,
    )

    log_llm_metric(
        operation="rag",
        model=settings.groq_model,
        duration_ms=duration * 1000,
        input_tokens=usage.get("prompt_tokens") if usage else None,
        output_tokens=usage.get("completion_tokens") if usage else None,
        total_tokens=usage.get("total_tokens") if usage else None,
    )

    return answer, sources
