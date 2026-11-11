"""
Agregador principal de routers para la API v1 de STV.
"""
from fastapi import APIRouter

from backend.app.api.v1.endpoints import plants, telemetry, alerts, ai_diagnostics

api_router = APIRouter()

api_router.include_router(plants.router, prefix="/plants", tags=["Plantas Fotovoltaicas"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["Telemetría IoT"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alertas del Sistema"])
api_router.include_router(ai_diagnostics.router, prefix="/ai", tags=["Diagnóstico Inteligente (IA)"])
