"""
SUITE DE PRUEBAS DE INTEGRACIÓN: FASE 7 (INTEGRACIÓN TOTAL END-TO-END)
======================================================================
Valida que la ingestión de telemetría, el motor de IA, el watchdog de sensores
y el despachador de alertas operen sincronizados sin fallas en la tubería.
"""
import unittest
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import get_session, init_db
from backend.app.models.entities import IoTDevice
from backend.app.services.sensor_watchdog_service import SensorWatchdogService

client = TestClient(app)


class TestEndToEndIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.plant_id = str(uuid.uuid4())
        # Crear planta para pruebas
        client.post("/api/v1/plants/", json={
            "name": "Planta Solar Integración E2E",
            "code": f"E2E-{uuid.uuid4().hex[:6].upper()}",
            "latitude": 6.2442,
            "longitude": -75.5812,
            "installed_capacity_kw": 1.0,
            "temp_coefficient_power": -0.0038,
            "inverter_nominal_efficiency": 0.9750
        })

    def test_01_telemetry_triggers_ai_and_persists_diagnostic(self):
        """Verifica que cada muestra de telemetría genere un diagnóstico en la tabla ai_diagnostics."""
        telemetry = {
            "device_uid": "ESP32-E2E-TEST",
            "plant_id": self.plant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dc": {"v_dc": 340.0, "i_dc": 2.5},
            "env": {"g_irradiance": 850.0, "t_panel": 40.0, "t_ambient": 25.0}
        }
        resp = client.post("/api/v1/telemetry/ingest", json=telemetry)
        self.assertEqual(resp.status_code, 201)

        # Consultar si el endpoint de IA devuelve el diagnóstico guardado
        diag_resp = client.get(f"/api/v1/ai/latest?plant_id={self.plant_id}")
        self.assertEqual(diag_resp.status_code, 200)
        data = diag_resp.json()
        self.assertIn("fault_category", data)
        self.assertIn("confidence_level", data)

    def test_02_mandatory_case_full_dispatch(self):
        """Verifica que el caso obligatorio genere la alerta crítica vinculada al diagnóstico de IA."""
        fault_telemetry = {
            "device_uid": "ESP32-E2E-TEST",
            "plant_id": self.plant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dc": {"v_dc": 170.0, "i_dc": 1.8235},  # P = 310 W
            "env": {"g_irradiance": 950.0, "t_panel": 48.0, "t_ambient": 28.0}
        }
        resp = client.post("/api/v1/telemetry/ingest", json=fault_telemetry)
        self.assertEqual(resp.status_code, 201)

        # Consultar alertas generadas
        alerts = client.get(f"/api/v1/alerts/?plant_id={self.plant_id}&severity=critical").json()
        self.assertGreaterEqual(len(alerts), 1)
        latest_alert = alerts[0]
        self.assertIn("Pérdida Crítica", latest_alert["title"])
        self.assertGreater(latest_alert["evidence_metrics"]["loss_percentage"], 60.0)

    def test_03_watchdog_discriminates_sensor_failure(self):
        """Verifica que si un sensor falla (G=0 al mediodía con producción), no se culpe a los paneles."""
        sensor_fail_telemetry = {
            "device_uid": "ESP32-E2E-TEST",
            "plant_id": self.plant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dc": {"v_dc": 340.0, "i_dc": 2.5},  # Generando 850 W
            "env": {"g_irradiance": 0.0, "t_panel": 40.0, "t_ambient": 25.0}  # Radiación 0 a las 12:00
        }
        client.post("/api/v1/telemetry/ingest", json=sensor_fail_telemetry)

        # Debe generar alerta de advertencia de sensor, NO crítica de paneles
        warning_alerts = client.get(f"/api/v1/alerts/?plant_id={self.plant_id}&severity=warning").json()
        sensor_alert = [a for a in warning_alerts if "Piranómetro" in a["title"] or "Sensor" in a["title"]]
        self.assertGreaterEqual(len(sensor_alert), 1)
        self.assertIn("Piranómetro", sensor_alert[0]["title"])

    def test_04_watchdog_detects_offline_device(self):
        """Verifica que si un gateway IoT deja de transmitir, se genere alerta de comunicación."""
        db = get_session()
        dev_uid = f"ESP32-TIMEOUT-{uuid.uuid4().hex[:4]}"
        stale_time = datetime.now(timezone.utc) - timedelta(seconds=120)

        device = IoTDevice(
            plant_id=self.plant_id,
            hardware_uid=dev_uid,
            status="online",
            last_seen=stale_time
        )
        db.add(device)
        db.commit()

        # Ejecutar verificación de timeouts
        flagged = SensorWatchdogService.check_device_connectivity_timeouts(db, timeout_seconds=60)
        self.assertGreaterEqual(flagged, 1)

        # Verificar que el dispositivo fue marcado como 'offline'
        db.refresh(device)
        self.assertEqual(device.status, "offline")
        db.close()


if __name__ == "__main__":
    unittest.main()
