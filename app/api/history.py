"""Historical price API endpoints.

Provides access to historical closing prices for requested
assets. Results are returned as a simple list of date/close
objects suitable for JSON serialization.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.errors import ErrorResponse
from app.schemas.risk import (
    DaysQueryParam,
    HistoryPoint,
    HistoryResponse,
    SymbolPathParam,
)
from app.services.pricing import get_price_history

router = APIRouter()


@router.get(
    "/history/{symbol}",
    response_model=HistoryResponse,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def history(symbol: SymbolPathParam, days: DaysQueryParam = 30) -> HistoryResponse:
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
    normalized_symbol = symbol.upper()

    try:
        df = get_price_history(normalized_symbol, days)

        prices = [
            HistoryPoint(
                date=index.date(),
                close=float(row["Close"]),
            )
            for index, row in  df.iterrows()
        ]

        return HistoryResponse(symbol=normalized_symbol, days=days, prices=prices)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
