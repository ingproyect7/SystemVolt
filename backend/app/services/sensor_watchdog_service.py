"""
SERVICIO WATCHDOG PARA DISCRIMINACIÓN DE FALLAS DE HARDWARE Y COMUNICACIÓN
==========================================================================
Distingue de forma rigurosa entre:
1. Falla Real del Panel Solar (Sombreado, Desconexión, Hotspot, Suciedad).
2. Falla del Sensor de Medición (Cable suelto, valor fuera de escala, radiación nula al mediodía).
3. Pérdida Total de Comunicación con el Gateway IoT (Corte de enlace Wi-Fi, Ethernet o 4G).
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models.entities import IoTDevice, SystemAlert, PlantTelemetry


class SensorWatchdogService:
    @staticmethod
    def check_device_connectivity_timeouts(db: Session, timeout_seconds: int = 60) -> int:
        """
        Revisa los dispositivos IoT activos. Si alguno no reporta telemetría
        en más de `timeout_seconds`, lo marca como 'offline' y genera una alerta
        de COMUNICACIÓN (no una falsa falla física del panel).
        """
        now = datetime.now(timezone.utc)
        threshold_time = now - timedelta(seconds=timeout_seconds)

        devices = db.query(IoTDevice).filter(IoTDevice.status == "online").all()
        flagged_count = 0

        for dev in devices:
            if dev.last_seen and dev.last_seen.replace(tzinfo=timezone.utc) < threshold_time:
                dev.status = "offline"
                flagged_count += 1

                # Generar alerta técnica de pérdida de enlace
                alert = SystemAlert(
                    plant_id=dev.plant_id or "default-plant",
                    severity="warning",
                    title="Pérdida de Comunicación con Gateway IoT",
                    description=(
                        f"El dispositivo {dev.hardware_uid} dejó de transmitir telemetría hace más de "
                        f"{timeout_seconds} segundos. La instalación fotovoltaica puede estar operando con normalidad, "
                        f"pero el enlace de red (Wi-Fi/4G) está caído."
                    ),
                    recommended_action="Revisar alimentación del gateway ESP32, cobertura de señal y router local.",
                    evidence_metrics={
                        "device_uid": dev.hardware_uid,
                        "last_seen": dev.last_seen.isoformat(),
                        "timeout_seconds": timeout_seconds
                    },
                    status="pending"
                )
                db.add(alert)

        if flagged_count > 0:
            db.commit()

        return flagged_count

    @staticmethod
    def validate_sensor_physical_plausibility(
        v_dc: float,
        i_dc: float,
        g_irr: float,
        t_panel: float,
        hour_of_day: float
    ) -> Optional[Dict[str, Any]]:
        """
        Detecta si una anomalía corresponde a una falla instrumental de sensor
        antes de culpar al generador solar.
        """
        # Caso A: Irradiancia 0 a pleno mediodía con tensión o corriente activa
        if (10.0 <= hour_of_day <= 14.5) and g_irr < 5.0 and (v_dc > 50.0 or i_dc > 0.5):
            return {
                "sensor_fault": True,
                "sensor_name": "Piranómetro / Célula Solar Calibrada",
                "diagnosis": "Lectura de radiación nula (0 W/m²) a mediodía con generación eléctrica activa.",
                "action": "Verificar conexión RS-485 del piranómetro y suciedad en el domo óptico."
            }

        # Caso B: Temperatura fuera de rango físico terrestre (-20°C a +120°C)
        if t_panel > 115.0 or t_panel < -15.0:
            return {
                "sensor_fault": True,
                "sensor_name": "Sonda Térmica PT100 / DS18B20",
                "diagnosis": f"Temperatura de módulo inverosímil ({t_panel}°C). Lectura fuera de escala física.",
                "action": "Comprobar integridad del cable de la sonda PT100 y módulo MAX31865 (posible circuito abierto)."
            }

        return None
