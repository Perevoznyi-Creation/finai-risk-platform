"""Pricing service utilities.

This module wraps calls to `yfinance` to retrieve current and
historical market prices used by the API handlers.
"""

import yfinance as yf
from typing import Any
from app.metrics.risk import compute_resurns, compute_volatility, compute_max_drawdown
from app.scoring.risk_scoring import classify_risk


def get_price(symbol: str) -> float:
    """Get the current market price of an asset.

    Parameters:
        symbol (str): Ticker symbol (e.g., "AAPL").

    Returns:
        float: Latest closing price for the symbol.

    Raises:
        ValueError: If no data is available for the provided symbol.
    """
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")

    if data.empty:
        raise ValueError(f"No data found for symbol {symbol}")

    return float(data["Close"].iloc[-1])


def get_price_history(symbol: str, days: int) -> Any:
    """Retrieve historical closing prices for the last `days` days.

    Parameters:
        symbol (str): Ticker symbol.
        days (int): Number of trailing days to request.

    Returns:
        pandas.DataFrame: DataFrame containing the `Close` column for
                          the specified period.

    Raises:
        ValueError: If no historical data exists for the symbol.
    """
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=f"{days}d")

    if data.empty:
        raise ValueError(f"No historical data for symbol {symbol}")

    return data[["Close"]]

def get_risk_metrics(symbol: str, days: int) -> dict:
    """Compute risk metrics for an asset based on historical prices.

    This function retrieves historical price data and computes
    returns, volatility, and maximum drawdown.

    Parameters:
        symbol (str): Ticker symbol.
        days (int): Number of trailing days to analyze.

    Returns:
        dict: A dictionary containing `symbol`, `volatility`, and
              `max_drawdown` metrics.

    Raises:
        ValueError: If no historical data exists for the symbol.
    """
    df = get_price_history(symbol, days)

    returns = compute_resurns(df)

    return {
        "volatility": compute_volatility(returns),
        "max_drawdown": compute_max_drawdown(df),
        "mean_return": float(returns.mean())
    }

def get_risk_profile(symbol: str, days: int) -> dict:
    """Get the risk profile of an asset based on historical price data.

    This function computes the volatility and maximum drawdown for
    the specified asset and classifies its risk level using the
    `classify_risk` function.

    Parameters:
        symbol (str): Ticker symbol.
        days (int): Number of trailing days to analyze.

    Returns:
        dict: A dictionary containing `symbol`, `volatility`,
              `max_drawdown`, and `risk_profile` keys.

    Raises:
        ValueError: If no historical data exists for the symbol.
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