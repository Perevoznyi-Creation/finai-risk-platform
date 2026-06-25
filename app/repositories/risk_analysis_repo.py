"""RiskAnalysis repository — encapsulates all database queries for risk analysis records."""

from sqlalchemy import text
from sqlmodel import Session, select

from app.repositories.models import RiskAnalysis


class RiskAnalysisRepository:
    """Manages persistence and lookup of risk analysis snapshots."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, analysis: RiskAnalysis) -> RiskAnalysis:
        """Persist a new risk analysis record and return the refreshed row."""
        self._session.add(analysis)
        self._session.commit()
        self._session.refresh(analysis)
        return analysis

    def get_by_symbol(self, symbol: str) -> list[RiskAnalysis]:
        """Return all risk analysis records for a given ticker symbol."""
        return list(
            self._session.exec(
                select(RiskAnalysis).where(RiskAnalysis.symbol == symbol)
            ).all()
        )

    def search_by_embedding(
        self, embedding: list[float], limit: int = 5
    ) -> list[RiskAnalysis]:
        """Return the closest risk analyses to the given embedding vector.

        Uses pgvector cosine distance operator ``<=>`` for nearest-neighbor
        lookup. Only rows that have a stored embedding are considered.

        Args:
            embedding: Query vector (384 dimensions).
            limit: Maximum number of results to return.

        Returns:
            List of RiskAnalysis rows ordered by similarity (closest first).
        """
        vector_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        rows = self._session.exec(
            select(RiskAnalysis)
            .where(RiskAnalysis.embedding.is_not(None))  # type: ignore[union-attr]
            .order_by(text(f"embedding <=> '{vector_literal}'::vector"))
            .limit(limit)
        ).all()
        return list(rows)
