from fastapi import APIRouter, HTTPException
from app.services.pricing import get_risk_profile

router = APIRouter()

@router.get("/risk-profile/{symbol}")
def risk_profile(symbol: str, days: int = 90):
    """ """
    pass