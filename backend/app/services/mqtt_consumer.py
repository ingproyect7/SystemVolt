"""
Consumidor MQTT en segundo plano para ingestión masiva de telemetría IoT.
"""
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_session
from backend.app.schemas.telemetry import TelemetryIngestPayload
from backend.app.services.telemetry_service import TelemetryService

logger = logging.getLogger("stv.mqtt_consumer")


def on_message_received(payload_str: str) -> bool:
    """
    Función de callback invocada al recibir un mensaje MQTT en el tópico 'stv/v1/+/+/telemetry'.
    Valida el JSON con Pydantic y lo delega al servicio de persistencia y análisis.
    """
    db: Session = get_session()
    try:
        data = json.loads(payload_str)
        payload = TelemetryIngestPayload(**data)
        record = TelemetryService.process_and_store_telemetry(db, payload)
        logger.info(f"Telemetría ingestada con éxito: Planta {record.plant_id} | Potencia: {record.p_dc} W")
        return True
    except Exception as e:
        logger.error(f"Error al procesar mensaje MQTT entrante: {e}")
        return False
    finally:
        db.close()
