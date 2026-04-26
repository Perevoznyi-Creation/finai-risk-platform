"""RiskAnalysis repository — encapsulates all database queries for risk analysis records."""

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
