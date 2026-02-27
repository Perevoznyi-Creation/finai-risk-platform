"""Pricing service utilities.

This module wraps calls to `yfinance` to retrieve current and
historical market prices used by the API handlers.
"""

import yfinance as yf
from typing import Any
from app.metrics.risk import compute_resurns, compute_volatility, compute_max_drawdown
from app.scoring.risk_scoring import classify_risk


def get_price(symbol: str) -> float:
    """Return the latest close price for a ticker symbol.

    Args:
        symbol: Asset ticker (for example, ``"AAPL"``).

    Returns:
        Latest close price from a 1-day history window.

    Raises:
        ValueError: No market data was returned for ``symbol``.
    """
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")

    if data.empty:
        raise ValueError(f"No data found for symbol {symbol}")

    return float(data["Close"].iloc[-1])


def get_price_history(symbol: str, days: int) -> Any:
    """Return trailing historical close prices for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing calendar days to request.

    Returns:
        DataFrame with a single ``Close`` column indexed by date.

    Raises:
        ValueError: No historical data was returned for ``symbol``.
    """
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=f"{days}d")

    if data.empty:
        raise ValueError(f"No historical data for symbol {symbol}")

    return data[["Close"]]

def get_risk_metrics(symbol: str, days: int) -> dict:
    """Compute aggregate risk metrics from price history.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used to compute metrics.

    Returns:
        Dictionary containing ``volatility``, ``max_drawdown``,
        and ``mean_return``.

    Raises:
        ValueError: Price history could not be loaded.
    """
    df = get_price_history(symbol, days)

    returns = compute_resurns(df)

    return {
        "volatility": compute_volatility(returns),
        "max_drawdown": compute_max_drawdown(df),
        "mean_return": float(returns.mean())
    }

def get_risk_profile(symbol: str, days: int) -> dict:
    """Classify ticker risk level from historical behavior.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used for feature extraction.

    Returns:
        Dictionary with ``volatility``, ``max_drawdown``, and
        categorical ``risk_level``.

    Raises:
        ValueError: Price history could not be loaded.
    """
    df = get_price_history(symbol, days)
    returns = compute_resurns(df)
    volatility = compute_volatility(returns)
    max_drawdown = compute_max_drawdown(df)

    risk_level = classify_risk(volatility, max_drawdown)

    return {
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "risk_level": risk_level
    }

def get_ml_risk_profile(symbol: str, days: int):
    """Predict risk level with the trained ML model.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used for feature extraction.

    Returns:
        Dictionary of computed features plus predicted ``risk_level``.
    """
    df = get_price_history(symbol, days)
    returns = compute_resurns(df)

    features = {
        "volatility": compute_volatility(returns),
        "max_drawdown": compute_max_drawdown(df),
        "mean_return": float(returns.mean())
    }

    return {
        **features,
        "risk_level": risk_model.predict(features)
    }
    
