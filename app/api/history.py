"""Historical price API endpoints.

Provides access to historical closing prices for requested
assets. Results are returned as a simple list of date/close
objects suitable for JSON serialization.
"""

from fastapi import APIRouter, HTTPException
from app.services.pricing import get_price_history

router = APIRouter()


@router.get("/history/{symbol}")
def history(symbol: str, days: int = 30):
    """Return trailing close-price history for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days to retrieve.

    Returns:
        Response object with ``symbol``, ``days``, and serialized
        ``prices`` entries.

    Raises:
        HTTPException: 404 when historical data is unavailable.
    """
    try:
        df = get_price_history(symbol, days)

        prices = [
            {
                "date": index.strftime("%Y-%m-%d"),
                "close": float(row["Close"])
            }
            for index, row in  df.iterrows()
        ]

        return {
            "symbol": symbol,
            "days": days,
            "prices": prices
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
