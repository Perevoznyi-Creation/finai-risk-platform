"""Metrics API — monitoring and observability endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.repositories.metrics_repo import MetricsRepository
from app.repositories.session import get_session

router = APIRouter()


class OperationStats(BaseModel):
    """Stats for a single operation."""

    avg_duration_ms: float = Field(description="Average latency in milliseconds.")
    p95_duration_ms: float = Field(description="95th percentile latency.")
    call_count: int = Field(description="Number of calls in the period.")


class TokenStats(BaseModel):
    """Token consumption stats for a model."""

    avg_input_tokens: float = Field(description="Average input tokens per call.")
    avg_output_tokens: float = Field(description="Average output tokens per call.")
    avg_total_tokens: float = Field(description="Average total tokens per call.")


class MetricsResponse(BaseModel):
    """AI system metrics and observability data."""

    period_days: int = Field(10, description="Metrics are aggregated over the last N days.")
    avg_eval_score: float | None = Field(description="Average explanation quality score (1-5).")
    operations: dict[str, OperationStats] = Field(description="Latency stats by operation.")
    token_usage: dict[str, TokenStats] = Field(description="Token stats by LLM model.")


@router.get(
    "/metrics",
    response_model=MetricsResponse,
)
def get_metrics(
    days: int = 7,
    session: Session = Depends(get_session),
) -> MetricsResponse:
    """Return aggregated AI system metrics and observability data.

    This endpoint exposes:
    - Average explanation eval score (quality)
    - P95 latency by operation
    - Token usage per model

    Args:
        days: Lookback window in days (default 7).
        session: Injected database session.

    Returns:
        Aggregated metrics across all LLM operations.
    """
    repo = MetricsRepository(session)

    avg_score = repo.get_avg_eval_score(days=days)
    ops = repo.get_operation_stats(days=days)
    tokens = repo.get_avg_tokens_by_model(days=days)

    # Convert dicts to appropriate model types
    op_stats = {
        op_name: OperationStats(**op_data) for op_name, op_data in ops.items()
    }
    token_stats = {
        model: TokenStats(**data) for model, data in tokens.items()
    }

    return MetricsResponse(
        period_days=days,
        avg_eval_score=avg_score,
        operations=op_stats,
        token_usage=token_stats,
    )
