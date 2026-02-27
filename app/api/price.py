"""Price API endpoints.

This module exposes HTTP endpoints related to current market
prices for assets. It delegates data retrieval to the
`app.services.pricing` module.
"""

from fastapi import APIRouter, HTTPException
from app.services.pricing import get_price

router = APIRouter()


@router.get("/price/{symbol}")
def price(symbol: str):
    """Return the latest market price for a ticker.

    Args:
        symbol: Asset ticker symbol (for example, ``"AAPL"``).

    Returns:
        Response object containing ``symbol`` and ``price``.

    Raises:
        HTTPException: 404 when the ticker has no available data.
    """
    try:
        value = get_price(symbol)
        return {
            "symbol": symbol,
            "price": value
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
