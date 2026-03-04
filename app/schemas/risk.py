"""API request/response schemas and validated parameter aliases."""

import datetime as dt
from enum import Enum
from typing import Annotated

from fastapi import Path, Query
from pydantic import BaseModel, Field


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


class RiskLevel(str, Enum):
    """Supported categorical risk labels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


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
