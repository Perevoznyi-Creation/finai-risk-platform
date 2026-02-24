"""Application entrypoint for the FinAI Risk Platform API.

This module creates the FastAPI application instance and mounts
API routers for price and history endpoints. It also exposes a
simple health check endpoint used by orchestration and monitoring
systems.
"""

from fastapi import FastAPI
from app.api.price import router as price_router
from app.api.history import router as history_router
from app.api.risk import router as risk_router

app = FastAPI(title="FinAI Risk Platform")

app.include_router(price_router)
app.include_router(history_router)
app.include_router(risk_router)


@app.get("/health")
def health():
    """Return a minimal health check for the service.

    Returns:
        dict: A JSON object containing the service status.
    """
    return {"status": "ok"}

