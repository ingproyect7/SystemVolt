"""
DEMOSTRADOR END-TO-END DE INTEGRACIÓN HARDWARE -> BACKEND -> IA -> NOTIFICACIÓN (STV)
====================================================================================
Ejecuta la tubería ciberfísica completa:
1. Emulación de telemetría de campo desde el Gateway ESP32.
2. Recepción y validación estricta en el Backend FastAPI.
3. Inferencia predictiva mediante el pipeline de Inteligencia Artificial.
4. Generación y despacho multicanal de la alerta ante el caso obligatorio (P_real = 310 W vs P_esp = 800 W).
5. Prueba del Watchdog: Discriminación entre desconexión de red, sensor fallido y falla del panel.
"""
import os
import sys
import uuid
from datetime import datetime, timezone

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def run_complete_end_to_end_demo():
    print("=" * 75)
    print("DEMOSTRADOR DE INTEGRACIÓN END-TO-END: SISTEMA FOTOVOLTAICO INTELIGENTE")
    print("=" * 75)

    # 1. Registrar Planta Solar Piloto
    plant_code = f"PILOTO-{uuid.uuid4().hex[:6].upper()}"
    plant_resp = client.post("/api/v1/plants/", json={
        "name": "Planta Solar Granja Experimental (Piloto)",
        "code": plant_code,
        "latitude": 6.2442,
        "longitude": -75.5812,
        "installed_capacity_kw": 1.0,  # 1000 Wp
        "temp_coefficient_power": -0.0038,
        "inverter_nominal_efficiency": 0.9750
    })
    plant_id = plant_resp.json()["id"]
    print(f"\n1. Planta Solar Creada en Backend:")
    print(f"• ID: {plant_id} | Código: {plant_code} | Potencia: 1.0 kWp")

    # 2. Ingesta de Telemetría Nominal (Operación Normal a las 11:00)
    print("\n2. Transmitiendo Telemetría Normal desde Gateway ESP32 (11:00 AM):")
    normal_tele = {
        "device_uid": "STV-ESP32-S3-001",
        "plant_id": plant_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dc": {"v_dc": 342.0, "i_dc": 2.50},  # ~855 W
        "env": {"g_irradiance": 880.0, "t_panel": 42.0, "t_ambient": 26.0}
    }
    resp_nom = client.post("/api/v1/telemetry/ingest", json=normal_tele)
    print(f"• Ingesta: {resp_nom.json()['status']}")
    print(f"• Potencia Real: {resp_nom.json()['p_calculated_w']} W | Potencia Esperada: {resp_nom.json()['p_expected_w']} W")
    print(f"• Performance Ratio (PR): {resp_nom.json()['performance_ratio']}")

    # 3. Inyección del Caso Obligatorio del Usuario (12:30 PM: G=950, T=48, P=310)
    print("\n" + "-" * 75)
    print("3. INYECTANDO CASO OBLIGATORIO: PÉRDIDA CRÍTICA DE RENDIMIENTO (12:30 PM):")
    print("• Condiciones: Irradiancia = 950 W/m² | T_panel = 48.0 °C | V = 170 V | I = 1.8235 A (P = 310 W)")
    print("-" * 75)

    fault_tele = {
        "device_uid": "STV-ESP32-S3-001",
        "plant_id": plant_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dc": {"v_dc": 170.0, "i_dc": 1.8235},  # P = 310.0 W
        "env": {"g_irradiance": 950.0, "t_panel": 48.0, "t_ambient": 28.0}
    }
    resp_fault = client.post("/api/v1/telemetry/ingest", json=fault_tele)
    print(f"• Ingesta Procesada:")
    print(f"  - Potencia Medida: {resp_fault.json()['p_calculated_w']} W")
    print(f"  - Potencia Esperada por IA: {resp_fault.json()['p_expected_w']} W")
    print(f"  - Performance Ratio: {resp_fault.json()['performance_ratio']}")

    # 4. Consultar Diagnóstico de IA Generado en la Base de Datos
    print("\n4. Consultando Diagnóstico Automático emitido por el Motor de IA:")
    diag_resp = client.get(f"/api/v1/ai/latest?plant_id={plant_id}")
    diag = diag_resp.json()
    print(f"• ¿Anomalía Confirmada?: {diag['is_anomaly']}")
    print(f"• Categoría de Falla Diagnosticada: {diag['fault_category']}")
    print(f"• Certeza Probabilística: {diag['confidence_level'] * 100:.1f}%")
    print(f"• Pérdida Energética: {diag['loss_percentage']}% (-{diag['delta_power']} W)")

    # 5. Consultar Alerta Crítica Despachada
    print("\n5. Verificando Alerta Crítica en Centro de Notificaciones:")
    alerts_resp = client.get(f"/api/v1/alerts/?plant_id={plant_id}&severity=critical")
    alert = alerts_resp.json()[0]
    print(f"• Título: {alert['title']}")
    print(f"• Severidad: {alert['severity'].upper()}")
    print(f"• Explicación Causal: {alert['description']}")
    print(f"• Recomendación de Campo: {alert['recommended_action']}")

    # 6. Prueba Watchdog: Incoherencia de Sensor
    print("\n" + "-" * 75)
    print("6. PRUEBA WATCHDOG: DISCRIMINACIÓN DE FALLA DE SENSOR (Mediodía con G = 0 W/m²):")
    sensor_fault_tele = {
        "device_uid": "STV-ESP32-S3-001",
        "plant_id": plant_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dc": {"v_dc": 340.0, "i_dc": 2.5},  # Generando 850 W
        "env": {"g_irradiance": 0.0, "t_panel": 40.0, "t_ambient": 25.0}  # Radiación 0 al mediodía (Imposible)
    }
    client.post("/api/v1/telemetry/ingest", json=sensor_fault_tele)
    
    # Verificar que el sistema clasificó como Falla en Sensor y no como Falla en Celdas
    sensor_alerts = client.get(f"/api/v1/alerts/?plant_id={plant_id}&severity=warning").json()
    latest_sensor_alert = sensor_alerts[0]
    print(f"• Título Alerta Watchdog: {latest_sensor_alert['title']}")
    print(f"• Diagnóstico Instrumental: {latest_sensor_alert['description']}")
    print(f"• Acción Recomendada: {latest_sensor_alert['recommended_action']}")
    print("=" * 75)


if __name__ == "__main__":
    run_complete_end_to_end_demo()
