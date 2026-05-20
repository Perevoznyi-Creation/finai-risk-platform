"""API request/response schemas and validated parameter aliases."""

import datetime as dt
from enum import Enum
from typing import Annotated

from fastapi import Path, Query
from pydantic import BaseModel, Field

from app.domain.risk_level import RiskLevel  # noqa: F401


SymbolPathParam = Annotated[
    str,
    Path(
        min_length=1,
        max_length=10,
        pattern=r"^[A-Za-z][A-Za-z0-9.-]{0,9}$",
        description="Ticker symbol with up to 10 characters.",
    ),
]

DaysQueryParam = Annotated[
    int,
    Query(
        ge=1,
        le=3650,
        description="Number of trailing days used for analysis.",
    ),
]


class RiskProfileMode(str, Enum):
    """Risk profile generation mode options."""

    rule = "rule"
    ml = "ml"


class HealthResponse(BaseModel):
    """Liveness endpoint response schema."""

    status: str = Field(default="ok")


class PriceResponse(BaseModel):
    """Current market price response schema."""

    symbol: str = Field(description="Ticker symbol.")
    price: float = Field(description="Latest close price.")


class HistoryPoint(BaseModel):
    """Single historical close-price point."""

    date: dt.date = Field(description="Trading date.")
    close: float = Field(description="Close price.")


class HistoryResponse(BaseModel):
    """Historical prices endpoint response schema."""

    symbol: str = Field(description="Ticker symbol.")
    days: int = Field(ge=1, le=3650, description="Requested trailing day window.")
    prices: list[HistoryPoint] = Field(description="Historical close-price series.")


class RiskMetrics(BaseModel):
    """Numeric risk metric set."""

    volatility: float = Field(description="Standard deviation of returns.")
    max_drawdown: float = Field(description="Worst peak-to-trough decline ratio.")
    mean_return: float = Field(description="Average periodic return.")


class RiskResponse(BaseModel):
    """Risk metrics endpoint response schema."""

    symbol: str = Field(description="Ticker symbol.")
    days: int = Field(ge=1, le=3650, description="Requested trailing day window.")
    metrics: RiskMetrics = Field(description="Computed risk metrics.")


class RiskExplainResponse(BaseModel):
    """Risk explanation endpoint response schema."""

    symbol: str = Field(description="Ticker symbol.")
    days: int = Field(ge=1, le=3650, description="Requested trailing day window.")
    metrics: RiskMetrics = Field(description="Computed risk metrics.")
    risk_level: str = Field(description="Classified risk label.")
    explanation: str = Field(description="Plain-English LLM-generated risk explanation.")


class RiskSearchResult(BaseModel):
    """Single result item returned by the semantic risk search endpoint."""

    id: int = Field(description="Record ID.")
    symbol: str = Field(description="Ticker symbol.")
    days: int = Field(description="Trailing day window used for analysis.")
    risk_level: str = Field(description="Classified risk label.")
    volatility: float = Field(description="Standard deviation of returns.")
    max_drawdown: float = Field(description="Worst peak-to-trough decline ratio.")
    mean_return: float = Field(description="Average daily return.")
    created_at: str = Field(description="ISO-8601 timestamp of when the analysis was stored.")


class RiskSearchResponse(BaseModel):
    """Semantic risk search endpoint response schema."""

    query: str = Field(description="The original search query.")
    results: list[RiskSearchResult] = Field(description="Matched risk analyses, closest first.")


class RiskProfileData(BaseModel):
    """Risk profile values returned for a symbol."""

    volatility: float = Field(description="Standard deviation of returns.")
    max_drawdown: float = Field(description="Worst peak-to-trough decline ratio.")
    risk_level: RiskLevel = Field(description="Categorical risk class.")


class RiskProfileResponse(BaseModel):
    """Risk-profile endpoint response schema."""

    symbol: str = Field(description="Ticker symbol.")
    days: int = Field(ge=1, le=3650, description="Requested trailing day window.")
    mode: RiskProfileMode = Field(description="Rule-based or model-based classification mode.")
    profile: RiskProfileData = Field(description="Computed risk profile.")
