"""SQLModel table definitions for persistent platform data."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, Index, String
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


class AnalysisMode(str, Enum):
    """Risk analysis execution mode."""

    rule = "rule"
    ml = "ml"


class RiskLevel(str, Enum):
    """Canonical risk classification labels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ApiKey(SQLModel, table=True):
    """API keys for service-to-service authentication."""

    __tablename__ = "api_keys"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(
        sa_column=Column(String(100), nullable=False, unique=True, index=True)
    )
    key_hash: str = Field(
        sa_column=Column(String(255), nullable=False, unique=True, index=True)
    )
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class RiskAnalysis(SQLModel, table=True):
    """Persisted risk analysis snapshot for a single symbol/window."""

    __tablename__ = "risk_analyses"
    __table_args__ = (Index("ix_risk_analyses_symbol_created_at", "symbol", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    symbol: str = Field(sa_column=Column(String(10), nullable=False, index=True))
    days: int = Field(nullable=False)
    mode: AnalysisMode = Field(
        sa_column=Column(SAEnum(AnalysisMode, name="analysis_mode"), nullable=False)
    )
    volatility: float = Field(nullable=False)
    max_drawdown: float = Field(nullable=False)
    mean_return: float = Field(nullable=False)
    risk_level: RiskLevel = Field(
        sa_column=Column(SAEnum(RiskLevel, name="risk_level"), nullable=False)
    )
    model_version: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class ModelRegistry(SQLModel, table=True):
    """Registered ML model artifacts and metadata."""

    __tablename__ = "model_registry"

    id: int | None = Field(default=None, primary_key=True)
    version: str = Field(
        sa_column=Column(String(100), nullable=False, unique=True, index=True)
    )
    run_id: str | None = Field(default=None, sa_column=Column(String(100), nullable=True))
    algorithm: str = Field(sa_column=Column(String(100), nullable=False))
    metrics_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False),
    )
    artifact_path: str = Field(sa_column=Column(String(500), nullable=False))
    is_current: bool = Field(default=False, nullable=False, index=True)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
