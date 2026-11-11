"""
Endpoints REST para Inferencia bajo demanda y consulta de diagnósticos de IA.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.entities import AIDiagnostic
from backend.app.services.telemetry_service import get_ai_engine
from backend.app.schemas.alert import AIDiagnosticResult

router = APIRouter()


class DirectInferenceRequest(BaseModel):
    v_dc: float
    i_dc: float
    g_irradiance: float
    t_panel: float
    t_ambient: Optional[float] = 25.0
    rh_ambient: Optional[float] = 50.0
    hour_of_day: Optional[float] = 12.0
    plant_id: Optional[str] = "plant-01"


@router.post("/diagnose", response_model=AIDiagnosticResult)
def run_direct_ai_inference(req: DirectInferenceRequest):
    """
    Ejecuta el pipeline de IA en tiempo real sobre un vector de variables.
    Retorna si es anomalía, potencia esperada, porcentaje de pérdida, causa probable,
    certeza y acción prescriptiva recomendada.
    """
    ai = get_ai_engine()
    result = ai.diagnose_measurement(
        v_dc=req.v_dc,
        i_dc=req.i_dc,
        g_irradiance=req.g_irradiance,
        t_panel=req.t_panel,
        t_ambient=req.t_ambient,
        rh_ambient=req.rh_ambient,
        hour_of_day=req.hour_of_day,
        plant_id=req.plant_id
    )
    return result


@router.get("/latest")
def get_latest_diagnostic(plant_id: str, db: Session = Depends(get_db)):
    """Obtiene el diagnóstico de IA más reciente registrado para una planta solar."""
    diag = (
        db.query(AIDiagnostic)
        .filter(AIDiagnostic.plant_id == plant_id)
        .order_by(desc(AIDiagnostic.timestamp))
        .first()
    )
    if not diag:
        raise HTTPException(status_code=404, detail="No hay diagnósticos registrados para esta planta.")

    return {
        "id": diag.id,
        "plant_id": diag.plant_id,
        "timestamp": diag.timestamp.isoformat(),
        "is_anomaly": diag.anomaly_detected,
        "fault_category": diag.fault_category,
        "confidence_level": diag.confidence_level,
        "p_expected": diag.p_expected,
        "p_actual": diag.p_actual,
        "delta_power": diag.delta_power,
        "loss_percentage": diag.loss_percentage,
        "features_importance": diag.features_importance
    }


@router.get("/history")
def get_diagnostics_history(
    plant_id: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Consulta la evolución temporal de anomalías y diagnósticos de IA."""
    diags = (
        db.query(AIDiagnostic)
        .filter(AIDiagnostic.plant_id == plant_id)
        .order_by(desc(AIDiagnostic.timestamp))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": d.id,
            "timestamp": d.timestamp.isoformat(),
            "is_anomaly": d.anomaly_detected,
            "fault_category": d.fault_category,
            "confidence_level": d.confidence_level,
            "loss_percentage": d.loss_percentage,
            "p_expected": d.p_expected,
            "p_actual": d.p_actual
        }
        for d in diags
    ]
