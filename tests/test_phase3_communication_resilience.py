"""
SUITE DE PRUEBAS UNITARIAS: FASE 3 (RESILIENCIA IOT Y STORE-AND-FORWARD)
=======================================================================
Verifica que la estrategia de almacenamiento local ante caídas de red
no pierda ningún registro y garantice la continuidad temporal de la telemetría.
"""
import unittest
import os
import sys

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.simulate_edge_connection_drop import run_resilience_test
from backend.app.schemas.telemetry import TelemetryIngestPayload


class TestCommunicationResilience(unittest.TestCase):
    def test_zero_data_loss_during_network_outage(self):
        """Verifica que ante un corte prolongado de red la pérdida de telemetría sea 0.0%."""
        result = run_resilience_test(samples_count=20)
        
        self.assertEqual(result["total_expected"], 20)
        self.assertEqual(result["live_count"], 10)       # 5 antes del corte + 5 después
        self.assertEqual(result["recovered_count"], 10)  # 10 muestras generadas durante el corte
        self.assertEqual(result["data_loss_percentage"], 0.0)

    def test_firmware_files_and_platformio_integrity(self):
        """Verifica que todos los archivos fuente de C++ y configuración existan en firmware/."""
        firmware_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "firmware"))
        
        files_to_check = [
            "platformio.ini",
            os.path.join("include", "telemetry_types.h"),
            os.path.join("include", "pin_definitions.h"),
            os.path.join("src", "main.cpp"),
            os.path.join("src", "sensor_acquisition.cpp"),
            os.path.join("src", "storage_buffer.cpp"),
            os.path.join("src", "mqtt_manager.cpp")
        ]
        
        for rel_file in files_to_check:
            full_path = os.path.join(firmware_dir, rel_file)
            self.assertTrue(os.path.exists(full_path), f"Falta el archivo requerido: {rel_file}")


if __name__ == "__main__":
    unittest.main()
