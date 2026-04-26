"""Rule-based risk analysis service — orchestrates domain logic over fetched market data."""

from typing import Any

from app.domain.metrics import compute_max_drawdown, compute_resurns, compute_volatility
from app.domain.scoring import classify_risk
from app.infrastructure.market.yfinance_client import fetch_history


def get_risk_metrics(symbol: str, days: int) -> dict[str, Any]:
    """Compute aggregate risk metrics from price history.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used to compute metrics.

    Returns:
        Dictionary containing ``volatility``, ``max_drawdown``, and ``mean_return``.

    Raises:
        ValueError: Price history could not be loaded.
    """
    df = fetch_history(symbol, days)
    returns = compute_resurns(df)

    return {
        "volatility": compute_volatility(returns),
        "max_drawdown": compute_max_drawdown(df),
        "mean_return": float(returns.mean()),
    }


def get_risk_profile(symbol: str, days: int) -> dict[str, Any]:
    """Classify ticker risk level from historical behavior (rule-based).

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used for feature extraction.

    Returns:
        Dictionary with ``volatility``, ``max_drawdown``, and categorical ``risk_level``.

    Raises:
        ValueError: Price history could not be loaded.
    """
    df = fetch_history(symbol, days)
    returns = compute_resurns(df)
    volatility = compute_volatility(returns)
    max_drawdown = compute_max_drawdown(df)

    return {
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "risk_level": classify_risk(volatility, max_drawdown),
    }
