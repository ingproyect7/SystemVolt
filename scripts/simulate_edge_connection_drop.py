"""
SIMULADOR Y VALIDADOR DE RESILIENCIA Y STORE-AND-FORWARD (FASE 3)
================================================================
Emula el comportamiento exacto del firmware ESP32 ante caídas de red:
1. Generación de telemetría a intervalos regulares.
2. Interrupción abrupta de conectividad (simulación de corte Wi-Fi/4G).
3. Conmutación a almacenamiento persistente en búfer local.
4. Restablecimiento de red y sincronización cronológica por lotes (FIFO).
5. Validación estricta de todos los paquetes contra el esquema Pydantic.
"""
import os
import sys
import time
import json
import uuid
import struct
from datetime import datetime, timezone
from typing import List, Dict

# Asegurar path hacia la raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.schemas.telemetry import TelemetryIngestPayload, ElectricalDC, EnvironmentalMetrics


class EdgeGatewaySimulator:
    def __init__(self, device_uid: str, plant_id: uuid.UUID, buffer_file: str = ".simulated_sd_buffer.bin"):
        self.device_uid = device_uid
        self.plant_id = plant_id
        self.buffer_file = buffer_file
        self.is_connected = True
        self.sent_live_records: List[Dict] = []
        self.recovered_buffer_records: List[Dict] = []
        
        # Limpiar buffer previo si existe
        if os.path.exists(self.buffer_file):
            os.remove(self.buffer_file)

    def write_to_offline_buffer(self, payload_dict: Dict) -> None:
        """Serializa la muestra en archivo binario/NDJSON simulando la tarjeta MicroSD."""
        with open(self.buffer_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload_dict) + "\n")

    def drain_offline_buffer(self) -> List[Dict]:
        """Drena y vacía el búfer offline en orden cronológico (FIFO)."""
        if not os.path.exists(self.buffer_file):
            return []

        drained = []
        with open(self.buffer_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    drained.append(json.loads(line.strip()))

        # Eliminar archivo simulando el vaciado exitoso de la MicroSD
        os.remove(self.buffer_file)
        return drained

    def process_sample(self, timestamp: datetime, v_dc: float, i_dc: float, g_irr: float, t_panel: float) -> bool:
        """Procesa una muestra; si hay conexión se transmite, de lo contrario se envía al búfer."""
        payload = TelemetryIngestPayload(
            device_uid=self.device_uid,
            plant_id=self.plant_id,
            timestamp=timestamp,
            dc=ElectricalDC(v_dc=v_dc, i_dc=i_dc),
            env=EnvironmentalMetrics(g_irradiance=g_irr, t_panel=t_panel, t_ambient=25.0, rh_ambient=60.0)
        )
        payload.calculate_instantaneous_power()
        payload_data = payload.model_dump(mode="json")

        if self.is_connected:
            self.sent_live_records.append(payload_data)
            return True
        else:
            self.write_to_offline_buffer(payload_data)
            return False


def run_resilience_test(samples_count: int = 20) -> Dict:
    plant_uuid = uuid.uuid4()
    gateway = EdgeGatewaySimulator("STV-ESP32-S3-SIM", plant_uuid)

    base_time = datetime(2026, 11, 11, 12, 0, 0, tzinfo=timezone.utc)
    
    print("\n--- INICIO DE PRUEBA DE RESILIENCIA EDGE IOT ---")
    
    # 1. Periodo Online (Muestras 0 a 4)
    print("Fase A: Conexión Activa (Online). Transmitiendo en tiempo real...")
    for i in range(5):
        sample_time = base_time + time_offset(i * 10)
        gateway.process_sample(sample_time, v_dc=340.0, i_dc=8.5, g_irr=900.0, t_panel=47.0)

    # 2. Corte de Red (Muestras 5 a 14: 100 segundos sin conexión)
    print("Fase B: ¡CAÍDA DE RED SIMULADA! Conmutando a Buffer Store & Forward (MicroSD)...")
    gateway.is_connected = False
    for i in range(5, 15):
        sample_time = base_time + time_offset(i * 10)
        gateway.process_sample(sample_time, v_dc=338.0, i_dc=8.4, g_irr=895.0, t_panel=47.5)

    # 3. Restablecimiento de Red (Muestra 15 en adelante)
    print("Fase C: ¡RED RESTABLECIDA! Reanudando conexión y drenando búfer offline...")
    gateway.is_connected = True
    
    # Drenar registros pendientes
    drained_samples = gateway.drain_offline_buffer()
    gateway.recovered_buffer_records.extend(drained_samples)
    print(f"• Registros recuperados cronológicamente del búfer offline: {len(drained_samples)}")

    # Continuar transmitiendo en tiempo real
    for i in range(15, 20):
        sample_time = base_time + time_offset(i * 10)
        gateway.process_sample(sample_time, v_dc=342.0, i_dc=8.6, g_irr=910.0, t_panel=48.0)

    total_expected = 20
    total_received = len(gateway.sent_live_records) + len(gateway.recovered_buffer_records)
    
    print("\n--- RESULTADO DE LA VALIDACIÓN ---")
    print(f"• Muestras totales generadas: {total_expected}")
    print(f"• Muestras transmitidas en vivo: {len(gateway.sent_live_records)}")
    print(f"• Muestras almacenadas en buffer durante corte y luego recuperadas: {len(gateway.recovered_buffer_records)}")
    print(f"• Tasa de pérdida de datos: {((total_expected - total_received) / total_expected) * 100.0:.2f}%")
    
    return {
        "total_expected": total_expected,
        "live_count": len(gateway.sent_live_records),
        "recovered_count": len(gateway.recovered_buffer_records),
        "data_loss_percentage": 0.0 if total_expected == total_received else 100.0
    }


def time_offset(seconds: int):
    from datetime import timedelta
    return timedelta(seconds=seconds)


if __name__ == "__main__":
    run_resilience_test()
