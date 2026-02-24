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
    """Return the latest market price for a given symbol.

    Parameters:
        symbol (str): Asset ticker symbol (e.g., "AAPL").

    Returns:
        dict: JSON object containing `symbol` and numeric `price`.

    Raises:
        HTTPException: 404 when the symbol has no available data.
    """
    try:
        value = get_price(symbol)
        return {
            "symbol": symbol,
            "price": value
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))