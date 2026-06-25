"""Metrics logging utility — save LLM call metrics to the database."""

from sqlmodel import Session

from app.repositories.metrics_repo import MetricsRepository
from app.repositories.session import get_engine


def log_llm_metric(
    operation: str,
    model: str,
    duration_ms: float,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    eval_score: int | None = None,
) -> None:
    """Log an LLM call metric to the database.

    This utility manages its own session, so it can be called from
    anywhere without passing a session around.

    Args:
        operation: e.g., "explain", "rag", "eval", "embed".
        model: Model name (e.g., "llama-3.1-8b-instant").
        duration_ms: Latency in milliseconds.
        input_tokens: Input token count, if available.
        output_tokens: Output token count, if available.
        total_tokens: Total token count, if available.
        eval_score: Evaluation score (1-5), if applicable.
    """
    try:
        with Session(get_engine()) as session:
            repo = MetricsRepository(session)
            repo.save_metric(
                operation=operation,
                model=model,
                duration_ms=duration_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                eval_score=eval_score,
            )
    except Exception as e:
        # Silently fail if metrics persist fails; don't break the business logic
        import structlog
        logger = structlog.get_logger()
        logger.warning("metrics.log_failed", error=str(e))
