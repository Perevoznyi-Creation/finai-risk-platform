"""Price API endpoints.

This module exposes HTTP endpoints related to current market
prices for assets. It delegates data retrieval to the
`app.services.pricing` module.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.errors import ErrorResponse
from app.schemas.risk import PriceResponse, SymbolPathParam
from app.services.pricing import get_price

router = APIRouter()


@router.get(
    "/price/{symbol}",
    response_model=PriceResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def price(symbol: SymbolPathParam) -> PriceResponse:
    """Return the latest market price for a ticker.

    Args:
        symbol: Asset ticker symbol (for example, ``"AAPL"``).

    Returns:
        Response object containing ``symbol`` and ``price``.

    Raises:
        HTTPException: 404 when the ticker has no available data.
    """
    normalized_symbol = symbol.upper()

    try:
        value = get_price(normalized_symbol)
        return PriceResponse(symbol=normalized_symbol, price=value)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
