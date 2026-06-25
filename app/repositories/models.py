"""SQLModel table definitions for persistent platform data."""

from datetime import datetime, timezone
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, Enum as SAEnum, Index, Integer, String
from sqlmodel import Field, SQLModel

from app.domain.risk_level import AnalysisMode, RiskLevel  # noqa: F401


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


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
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(384), nullable=True),
    )
    eval_score: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="LLM-as-judge rating (1-5) of explanation quality. Higher is better.",
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class Document(SQLModel, table=True):
    """Uploaded document (PDF or plain text) stored for RAG queries."""

    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    filename: str = Field(sa_column=Column(String(500), nullable=False))
    content_text: str = Field(sa_column=Column(String, nullable=False))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )


class DocumentChunk(SQLModel, table=True):
    """Fixed-size text chunk from a document, with its embedding vector."""

    __tablename__ = "document_chunks"
    __table_args__ = (Index("ix_document_chunks_document_id", "document_id"),)

    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(nullable=False, foreign_key="documents.id")
    chunk_index: int = Field(nullable=False)
    chunk_text: str = Field(sa_column=Column(String, nullable=False))
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(384), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
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


class LLMCallMetric(SQLModel, table=True):
    """Tracks LLM API call performance and token usage."""

    __tablename__ = "llm_call_metrics"
    __table_args__ = (Index("ix_llm_call_metrics_created_at", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    operation: str = Field(
        sa_column=Column(String(50), nullable=False), description="e.g., 'explain', 'rag', 'eval'"
    )
    model: str = Field(sa_column=Column(String(100), nullable=False))
    duration_ms: float = Field(nullable=False, description="Latency in milliseconds.")
    input_tokens: int | None = Field(default=None)
    output_tokens: int | None = Field(default=None)
    total_tokens: int | None = Field(default=None)
    eval_score: int | None = Field(default=None, description="If eval operation, the score (1-5).")
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
