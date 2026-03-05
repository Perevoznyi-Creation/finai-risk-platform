from fastapi import APIRouter, HTTPException, Query
from app.schemas.errors import ErrorResponse
from app.schemas.risk import (
    DaysQueryParam,
    RiskProfileData,
    RiskProfileMode,
    RiskProfileResponse,
    SymbolPathParam,
)
from app.services.pricing import get_ml_risk_profile, get_risk_profile

router = APIRouter()


@router.get(
    "/risk-profile/{symbol}",
    response_model=RiskProfileResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def risk_profile(
    symbol: SymbolPathParam,
    days: DaysQueryParam = 90,
    mode: RiskProfileMode = Query(default=RiskProfileMode.rule),
) -> RiskProfileResponse:
    """Return the rule-based risk profile for a ticker.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days used for analysis.

    Returns:
        Response object with ticker metadata and computed profile.

    Raises:
        HTTPException: 400 when pricing data is unavailable or invalid.
    """
    normalized_symbol = symbol.upper()

    try:
        if mode == RiskProfileMode.ml:
            profile_data = get_ml_risk_profile(normalized_symbol, days)
        else:
            profile_data = get_risk_profile(normalized_symbol, days)

        profile = RiskProfileData(**profile_data)
        return RiskProfileResponse(
            symbol=normalized_symbol,
            days=days,
            mode=mode,
            profile=profile,
        )
    except ValueError as e:
        if mode == RiskProfileMode.ml:
            raise HTTPException(status_code=400, detail=str(e)) from e
        raise HTTPException(status_code=404, detail=str(e)) from e
