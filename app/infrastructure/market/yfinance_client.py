"""yfinance adapter — isolates all external market data I/O in one place."""

import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_price(symbol: str) -> float:
    """Return the latest close price for a ticker symbol.

    Args:
        symbol: Asset ticker (for example, ``"AAPL"``).

    Returns:
        Latest close price from a 1-day history window.

    Raises:
        ValueError: No market data was returned for ``symbol``.
    """
    logger.debug("Fetching latest price for %s", symbol)
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")

    if data.empty:
        logger.warning("No price data returned by yfinance for symbol %s", symbol)
        raise ValueError(f"No data found for symbol {symbol}")

    return float(data["Close"].iloc[-1])


def fetch_history(symbol: str, days: int) -> pd.DataFrame:
    """Return trailing historical close prices for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing calendar days to request.

    Returns:
        DataFrame with a single ``Close`` column indexed by date.

    Raises:
        ValueError: No historical data was returned for ``symbol``.
    """
    logger.debug("Fetching %d-day price history for %s", days, symbol)
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=f"{days}d")

    if data.empty:
        logger.warning(
            "No historical data returned by yfinance for symbol %s (days=%d)",
            symbol,
            days,
        )
        raise ValueError(f"No historical data for symbol {symbol}")

    return data[["Close"]]
