"""Metrics repository — persistence for LLM call metrics."""

from datetime import datetime, timedelta

from sqlalchemy import func, text
from sqlmodel import Session, select

from app.repositories.models import LLMCallMetric, RiskAnalysis


class MetricsRepository:
    """Manages persistence and aggregation of performance metrics."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_metric(
        self,
        operation: str,
        model: str,
        duration_ms: float,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        total_tokens: int | None = None,
        eval_score: int | None = None,
    ) -> LLMCallMetric:
        """Persist a single LLM call metric."""
        metric = LLMCallMetric(
            operation=operation,
            model=model,
            duration_ms=duration_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            eval_score=eval_score,
        )
        self._session.add(metric)
        self._session.commit()
        self._session.refresh(metric)
        return metric

    def get_avg_eval_score(self, days: int = 7) -> float | None:
        """Return the average eval score over the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = self._session.exec(
            select(func.avg(RiskAnalysis.eval_score)).where(
                RiskAnalysis.eval_score.is_not(None),  # type: ignore[union-attr]
                RiskAnalysis.created_at >= cutoff,
            )
        ).first()
        return float(result) if result else None

    def get_p95_latency_ms(self, operation: str | None = None, days: int = 7) -> float | None:
        """Return the 95th percentile latency in milliseconds."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        stmt = select(LLMCallMetric).where(LLMCallMetric.created_at >= cutoff)
        if operation:
            stmt = stmt.where(LLMCallMetric.operation == operation)

        rows = self._session.exec(stmt.order_by(LLMCallMetric.duration_ms)).all()
        if not rows:
            return None

        idx = int(len(rows) * 0.95)
        return rows[idx].duration_ms if idx < len(rows) else rows[-1].duration_ms

    def get_avg_tokens_by_model(self, days: int = 7) -> dict[str, dict[str, float]]:
        """Return average token consumption (input, output, total) by model."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = self._session.exec(
            select(
                LLMCallMetric.model,
                func.avg(LLMCallMetric.input_tokens).label("avg_input"),
                func.avg(LLMCallMetric.output_tokens).label("avg_output"),
                func.avg(LLMCallMetric.total_tokens).label("avg_total"),
            )
            .where(LLMCallMetric.created_at >= cutoff)
            .group_by(LLMCallMetric.model)
        ).all()

        result = {}
        for row in rows:
            model, avg_input, avg_output, avg_total = row
            result[model] = {
                "avg_input_tokens": float(avg_input) if avg_input else 0,
                "avg_output_tokens": float(avg_output) if avg_output else 0,
                "avg_total_tokens": float(avg_total) if avg_total else 0,
            }
        return result

    def get_operation_stats(self, days: int = 7) -> dict[str, dict[str, float]]:
        """Return latency stats (avg, p95) per operation."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = self._session.exec(
            select(
                LLMCallMetric.operation,
                func.avg(LLMCallMetric.duration_ms).label("avg_duration"),
                func.count(LLMCallMetric.id).label("call_count"),
            )
            .where(LLMCallMetric.created_at >= cutoff)
            .group_by(LLMCallMetric.operation)
        ).all()

        result = {}
        for row in rows:
            operation, avg_duration, call_count = row
            p95 = self.get_p95_latency_ms(operation=operation, days=days)
            result[operation] = {
                "avg_duration_ms": float(avg_duration) if avg_duration else 0,
                "p95_duration_ms": p95 or 0,
                "call_count": call_count,
            }
        return result
