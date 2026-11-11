"""
Servicio de negocio para el procesamiento, validación y consulta de telemetría.
Integra el motor de inferencia de IA, el discriminador de sensores y el despachador de alertas.
"""
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.entities import PlantTelemetry, SolarPlant, SystemAlert, AIDiagnostic
from backend.app.schemas.telemetry import TelemetryIngestPayload
from backend.app.services.alert_dispatcher import AlertDispatcher
from backend.app.services.sensor_watchdog_service import SensorWatchdogService
from ai_engine.pipelines.inference_engine import PVInferenceEngine

# Instancia singleton del motor de inferencia
_ai_engine = None

def get_ai_engine():
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = PVInferenceEngine()
    return _ai_engine


class TelemetryService:
    @staticmethod
    def process_and_store_telemetry(db: Session, payload: TelemetryIngestPayload) -> PlantTelemetry:
        """
        Tubería unificada de extremo a extremo:
        1. Valida potencia calculada P = V * I.
        2. Discriminación Watchdog: ¿Es una falla de sensor físico o de panel?
        3. Ejecución del motor de inferencia de IA (Física Sandia + XGBoost + Isolation Forest + Clasificador Causal).
        4. Persistencia de Telemetría e Hipertabla TimescaleDB.
        5. Persistencia del Diagnóstico de IA en `ai_diagnostics`.
        6. Despacho automatizado de alertas multicanal si se detecta anomalía.
        """
        p_dc_calc = payload.calculate_instantaneous_power()
        plant_id_str = str(payload.plant_id)

        # 1. Discriminar fallas de sensores físicos antes de invocar la IA de celdas
        hour = payload.timestamp.hour + payload.timestamp.minute / 60.0
        sensor_issue = SensorWatchdogService.validate_sensor_physical_plausibility(
            v_dc=payload.dc.v_dc,
            i_dc=payload.dc.i_dc,
            g_irr=payload.env.g_irradiance,
            t_panel=payload.env.t_panel,
            hour_of_day=hour
        )

        # 2. Ejecutar Inferencia de Inteligencia Artificial
        ai = get_ai_engine()
        diag_result = ai.diagnose_measurement(
            v_dc=payload.dc.v_dc,
            i_dc=payload.dc.i_dc,
            g_irradiance=payload.env.g_irradiance,
            t_panel=payload.env.t_panel,
            t_ambient=payload.env.t_ambient or 25.0,
            rh_ambient=payload.env.rh_ambient or 50.0,
            hour_of_day=hour,
            plant_id=plant_id_str,
            device_uid=payload.device_uid
        )

        # Si el watchdog detectó falla de sensor, ajustar el diagnóstico
        if sensor_issue:
            diag_result.is_anomaly = True
            diag_result.root_cause_explanation = sensor_issue["diagnosis"]
            diag_result.recommended_action = sensor_issue["action"]
            diag_result.confidence_level = 0.99

        # 3. Persistir Telemetría
        record = PlantTelemetry(
            time=payload.timestamp,
            plant_id=plant_id_str,
            device_uid=payload.device_uid,
            string_id=str(payload.string_id) if payload.string_id else None,
            v_dc=payload.dc.v_dc,
            i_dc=payload.dc.i_dc,
            p_dc=p_dc_calc,
            v_ac=payload.ac.v_ac if payload.ac else None,
            i_ac=payload.ac.i_ac if payload.ac else None,
            p_ac=payload.ac.p_ac if payload.ac else None,
            frequency=payload.ac.frequency if payload.ac else None,
            g_irradiance=payload.env.g_irradiance,
            t_panel=payload.env.t_panel,
            t_ambient=payload.env.t_ambient,
            rh_ambient=payload.env.rh_ambient,
            p_expected_model=diag_result.p_expected,
            performance_ratio=round(p_dc_calc / max(1.0, diag_result.p_expected), 4) if diag_result.p_expected > 15.0 else None
        )
        db.add(record)

        # 4. Persistir Registro de Diagnóstico de IA
        ai_diag_db = AIDiagnostic(
            plant_id=plant_id_str,
            timestamp=payload.timestamp,
            anomaly_detected=diag_result.is_anomaly,
            anomaly_score=diag_result.anomaly_score,
            fault_category=diag_result.fault_category.value if hasattr(diag_result.fault_category, "value") else str(diag_result.fault_category),
            confidence_level=diag_result.confidence_level,
            p_expected=diag_result.p_expected,
            p_actual=diag_result.p_actual,
            delta_power=diag_result.delta_power,
            loss_percentage=diag_result.loss_percentage,
            features_importance=diag_result.features_importance
        )
        db.add(ai_diag_db)
        db.flush()

        # 5. Generación y Despacho de Alertas si es Anomalía
        if diag_result.is_anomaly and (diag_result.loss_percentage > 20.0 or sensor_issue):
            severity = "critical" if diag_result.loss_percentage > 40.0 else "warning"
            if sensor_issue:
                severity = "warning"
                title = f"Falla en {sensor_issue['sensor_name']}"
            else:
                title = f"Pérdida Crítica de Rendimiento ({diag_result.loss_percentage}% Pérdida)"

            alert = SystemAlert(
                plant_id=plant_id_str,
                diagnostic_id=ai_diag_db.id,
                severity=severity,
                title=title,
                description=diag_result.root_cause_explanation,
                recommended_action=diag_result.recommended_action,
                evidence_metrics={
                    "p_actual": p_dc_calc,
                    "p_expected": diag_result.p_expected,
                    "loss_percentage": diag_result.loss_percentage,
                    "g_irradiance": payload.env.g_irradiance,
                    "t_panel": payload.env.t_panel,
                    "confidence": diag_result.confidence_level
                },
                status="pending"
            )
            db.add(alert)
            db.flush()

            # 6. Despacho Multicanal (Telegram, Email, Webhook)
            AlertDispatcher.dispatch_alert({
                "id": alert.id,
                "plant_id": plant_id_str,
                "severity": severity,
                "title": title,
                "description": diag_result.root_cause_explanation,
                "recommended_action": diag_result.recommended_action,
                "evidence_metrics": alert.evidence_metrics,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_plant_telemetry_history(
        db: Session,
        plant_id: str,
        limit: int = 100
    ) -> List[PlantTelemetry]:
        return (
            db.query(PlantTelemetry)
            .filter(PlantTelemetry.plant_id == plant_id)
            .order_by(desc(PlantTelemetry.time))
            .limit(limit)
            .all()
        )
