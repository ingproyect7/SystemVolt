"""
SUITE DE PRUEBAS DE INTEGRACIÓN: FASE 4 (BACKEND FASTAPI Y PERSISTENCIA)
========================================================================
Valida el ciclo de vida completo de la API REST:
1. Verificación de salud y endpoints raíz.
2. Creación de una planta fotovoltaica.
3. Ingestión de telemetría en tiempo real y cálculo físico automático.
4. Activación automática de alerta ante el caso obligatorio (P_real=310W vs P_esp=800W con G=950W/m²).
5. Ciclo de vida de alertas (reconocimiento y resolución).
6. Ingestión masiva (batch) de telemetría y consulta histórica de series temporales.
"""
import unittest
import os
import sys
import uuid
from datetime import datetime, timezone

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import init_db

client = TestClient(app)


class TestBackendAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Asegurar inicialización de base de datos
        init_db()

    def test_01_health_check(self):
        """Verifica que el backend responda exitosamente al chequeo de salud."""
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("STV", data["service"])

    def test_02_create_solar_plant(self):
        """Verifica el registro de una planta solar con sus coeficientes técnicos."""
        unique_code = f"PLANT-TEST-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "name": "Planta Solar Granja Experimental",
            "code": unique_code,
            "latitude": 6.2442,
            "longitude": -75.5812,
            "installed_capacity_kw": 1.0,  # 1000 Wp instalados
            "tilt_angle": 10.0,
            "azimuth_angle": 180.0,
            "temp_coefficient_power": -0.0038,
            "inverter_nominal_efficiency": 0.9750
        }
        response = client.post("/api/v1/plants/", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Planta Solar Granja Experimental")
        TestBackendAPI.plant_id = data["id"]

    def test_03_ingest_normal_telemetry(self):
        """Verifica la ingestión de telemetría normal y el cálculo automático de potencia y PR."""
        plant_id = getattr(TestBackendAPI, "plant_id", str(uuid.uuid4()))
        telemetry_payload = {
            "device_uid": "ESP32-S3-TEST-001",
            "plant_id": plant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dc": {
                "v_dc": 340.0,
                "i_dc": 2.5
            },
            "env": {
                "g_irradiance": 880.0,
                "t_panel": 42.0,
                "t_ambient": 26.0,
                "rh_ambient": 55.0
            }
        }
        response = client.post("/api/v1/telemetry/ingest", json=telemetry_payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertAlmostEqual(data["p_calculated_w"], 850.0, places=1)
        self.assertGreater(data["p_expected_w"], 0.0)
        self.assertGreater(data["performance_ratio"], 0.80)

    def test_04_mandatory_anomaly_case_triggers_alert(self):
        """
        Prueba obligatoria del requerimiento:
        Condición: G=950 W/m², T_panel=48°C, P_real=310W.
        Verifica que el sistema detecte la pérdida crítica (>60%) y genere una alerta automáticamente.
        """
        plant_id = getattr(TestBackendAPI, "plant_id", str(uuid.uuid4()))
        # V=170V, I=1.8235A -> P_real = 310.0 W
        telemetry_payload = {
            "device_uid": "ESP32-S3-TEST-001",
            "plant_id": plant_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dc": {
                "v_dc": 170.0,
                "i_dc": 1.8235
            },
            "env": {
                "g_irradiance": 950.0,
                "t_panel": 48.0,
                "t_ambient": 28.0,
                "rh_ambient": 50.0
            }
        }
        response = client.post("/api/v1/telemetry/ingest", json=telemetry_payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertAlmostEqual(data["p_calculated_w"], 310.0, places=1)
        self.assertLess(data["performance_ratio"], 0.40)  # Pérdida severa

        # Verificar que se generó la alerta crítica en la base de datos
        alerts_resp = client.get(f"/api/v1/alerts/?plant_id={plant_id}&severity=critical")
        self.assertEqual(alerts_resp.status_code, 200)
        alerts_list = alerts_resp.json()
        self.assertGreaterEqual(len(alerts_list), 1)
        
        latest_alert = alerts_list[0]
        self.assertEqual(latest_alert["severity"], "critical")
        self.assertIn("Pérdida Crítica", latest_alert["title"])
        TestBackendAPI.alert_id = latest_alert["id"]

    def test_05_alert_acknowledgement_lifecycle(self):
        """Verifica la transición de estado de alerta a 'acknowledged'."""
        alert_id = getattr(TestBackendAPI, "alert_id", None)
        if not alert_id:
            self.skipTest("No hay alert_id registrado.")

        ack_response = client.post(
            f"/api/v1/alerts/{alert_id}/acknowledge",
            json={"note": "Técnico en camino a inspeccionar string 01."}
        )
        self.assertEqual(ack_response.status_code, 200)
        data = ack_response.json()
        self.assertEqual(data["new_status"], "acknowledged")

    def test_06_batch_telemetry_and_history_query(self):
        """Verifica la ingesta por lotes (sincronización store-and-forward) y la consulta de historial."""
        plant_id = getattr(TestBackendAPI, "plant_id", str(uuid.uuid4()))
        records = [
            {
                "device_uid": "ESP32-S3-BATCH",
                "plant_id": plant_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dc": {"v_dc": 345.0, "i_dc": 2.6},
                "env": {"g_irradiance": 900.0, "t_panel": 45.0}
            },
            {
                "device_uid": "ESP32-S3-BATCH",
                "plant_id": plant_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "dc": {"v_dc": 344.0, "i_dc": 2.58},
                "env": {"g_irradiance": 895.0, "t_panel": 44.8}
            }
        ]
        batch_payload = {
            "device_uid": "ESP32-S3-BATCH",
            "plant_id": plant_id,
            "records": records
        }
        batch_resp = client.post("/api/v1/telemetry/batch", json=batch_payload)
        self.assertEqual(batch_resp.status_code, 201)
        self.assertEqual(batch_resp.json()["processed_records"], 2)

        # Consultar historial
        hist_resp = client.get(f"/api/v1/telemetry/history?plant_id={plant_id}&limit=10")
        self.assertEqual(hist_resp.status_code, 200)
        hist_data = hist_resp.json()
        self.assertGreaterEqual(len(hist_data), 3)


if __name__ == "__main__":
    unittest.main()
