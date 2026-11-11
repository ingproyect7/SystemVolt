"""
Endpoints REST para la ingestión y consulta histórica de telemetría fotovoltaica.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.telemetry import TelemetryIngestPayload, TelemetryBatchIngestPayload
from backend.app.services.telemetry_service import TelemetryService

router = APIRouter()


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_telemetry_point(payload: TelemetryIngestPayload, db: Session = Depends(get_db)):
    """
    Ingesta directa de una medición de telemetría vía HTTP REST.
    Valida la física del dato, calcula métricas de rendimiento y almacena en TimescaleDB.
    """
    try:
        record = TelemetryService.process_and_store_telemetry(db, payload)
        return {
            "status": "success",
            "telemetry_id": record.id,
            "p_calculated_w": record.p_dc,
            "p_expected_w": record.p_expected_model,
            "performance_ratio": record.performance_ratio,
            "timestamp": record.time.isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error procesando telemetría: {str(e)}")


@router.post("/batch", status_code=status.HTTP_201_CREATED)
def ingest_telemetry_batch(batch_payload: TelemetryBatchIngestPayload, db: Session = Depends(get_db)):
    """
    Ingesta por lotes (batch) utilizada al sincronizar el búfer offline tras un corte de red.
    """
    processed_count = 0
    errors = []

    for item in batch_payload.records:
        try:
            TelemetryService.process_and_store_telemetry(db, item)
            processed_count += 1
        except Exception as e:
            db.rollback()
            errors.append(str(e))

    return {
        "status": "success",
        "processed_records": processed_count,
        "failed_records": len(errors),
        "device_uid": batch_payload.device_uid
    }


@router.get("/history")
def get_telemetry_history(
    plant_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Consulta el historial de telemetría para visualización gráfica en el dashboard industrial.
    """
    records = TelemetryService.get_plant_telemetry_history(db, plant_id=plant_id, limit=limit)
    return [
        {
            "time": r.time.isoformat(),
            "v_dc": r.v_dc,
            "i_dc": r.i_dc,
            "p_dc": r.p_dc,
            "g_irradiance": r.g_irradiance,
            "t_panel": r.t_panel,
            "t_ambient": r.t_ambient,
            "p_expected": r.p_expected_model,
            "performance_ratio": r.performance_ratio
        }
        for r in records
    ]
