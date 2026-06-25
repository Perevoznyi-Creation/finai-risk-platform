"""Embeddings service — generates vector embeddings locally via sentence-transformers."""

from functools import lru_cache
import time
import structlog

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"

logger = structlog.get_logger()


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load and cache the embedding model (downloaded once on first call)."""
    return SentenceTransformer(_MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """Generate a 384-dimensional embedding vector for the given text.

    Uses the ``all-MiniLM-L6-v2`` model locally — no API key required.

    Args:
        text: The text to embed. Typically an LLM-generated explanation.

    Returns:
        List of 384 floats representing the semantic embedding.
    """
    model = _get_model()
    start = time.time()
    vec = model.encode(text, normalize_embeddings=True).tolist()
    duration = time.time() - start
    logger.debug("embedding.generate", text_len=len(text), duration_seconds=round(duration, 3))
    return vec
