"""
Endpoints REST para la supervisión y gestión del ciclo de vida de Alertas del Sistema.
"""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.entities import SystemAlert

router = APIRouter()


class AlertActionPayload(BaseModel):
    user_id: Optional[str] = None
    note: Optional[str] = None


@router.get("/")
def list_system_alerts(
    plant_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, description="pending, acknowledged, resolved"),
    severity: Optional[str] = Query(None, description="info, warning, critical"),
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Consulta la lista de alertas activas o históricas del sistema fotovoltaico."""
    query = db.query(SystemAlert)
    if plant_id:
        query = query.filter(SystemAlert.plant_id == plant_id)
    if status_filter:
        query = query.filter(SystemAlert.status == status_filter)
    if severity:
        query = query.filter(SystemAlert.severity == severity)

    alerts = query.order_by(desc(SystemAlert.created_at)).limit(limit).all()
    return [
        {
            "id": a.id,
            "plant_id": a.plant_id,
            "severity": a.severity,
            "title": a.title,
            "description": a.description,
            "recommended_action": a.recommended_action,
            "evidence_metrics": a.evidence_metrics,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
            "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
        }
        for a in alerts
    ]


@router.post("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, action: AlertActionPayload, db: Session = Depends(get_db)):
    """Marca una alerta como 'reconocida' por el operador técnico."""
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")

    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return {"status": "success", "alert_id": alert.id, "new_status": alert.status}


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str, action: AlertActionPayload, db: Session = Depends(get_db)):
    """Marca una alerta como 'resuelta' tras una intervención o mantenimiento."""
    alert = db.query(SystemAlert).filter(SystemAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada.")

    alert.status = "resolved"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return {"status": "success", "alert_id": alert.id, "new_status": alert.status}
