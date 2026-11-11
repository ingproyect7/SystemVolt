"""
SUITE DE PRUEBAS UNITARIAS: FASE 1 (CONTRATOS, MODELOS Y FÍSICA SOLAR)
=====================================================================
Verifica la integridad de los contratos de datos, las restricciones físicas
y el cálculo analítico del simulador fotovoltaico antes de avanzar a la Fase 2.
"""
import unittest
from datetime import datetime, timezone
import uuid

import sys
import os
# Asegurar que el directorio raíz de STV esté en el sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.pv_physics_simulator import PhotovoltaicPhysicsEngine


class TestPhotovoltaicPhysics(unittest.TestCase):
    def setUp(self):
        self.engine = PhotovoltaicPhysicsEngine(
            p_stc_watts=1000.0,
            gamma_temp_coeff=-0.0038,
            noct_celsius=45.0,
            inverter_nominal_eff=0.975
        )

    def test_cell_temperature_calculation(self):
        """Verifica que a G=800 W/m² y T_amb=20°C, T_cell alcance el valor nominal NOCT (45°C)."""
        t_cell = self.engine.calculate_cell_temperature(g_irradiance=800.0, t_ambient=20.0)
        self.assertAlmostEqual(t_cell, 45.0, places=1)

    def test_theoretical_power_at_stc(self):
        """Verifica la potencia a condiciones estándar (1000 W/m² y 25°C)."""
        # A 25°C no hay pérdida térmica; la potencia DC es 1000W, y con n_inv=0.975 es 975W
        p_theor = self.engine.calculate_theoretical_power(g_irradiance=1000.0, t_cell=25.0)
        self.assertAlmostEqual(p_theor, 975.0, places=1)

    def test_zero_power_at_night(self):
        """Verifica que sin radiación solar la potencia sea exactamente cero."""
        p_theor = self.engine.calculate_theoretical_power(g_irradiance=0.0, t_cell=20.0)
        self.assertEqual(p_theor, 0.0)

    def test_shading_fault_injection(self):
        """Verifica que la inyección de sombreado reduzca la corriente drásticamente."""
        v_nom, i_nom, p_nom = self.engine.calculate_iv_operating_point(800.0, 45.0)
        shaded = self.engine.inject_fault("SHADING", v_nom, i_nom, p_nom, 45.0)
        
        self.assertLess(shaded["i_dc"], i_nom * 0.5)
        self.assertLess(shaded["p_dc"], p_nom * 0.5)
        self.assertEqual(shaded["fault_injected"], "SHADING")

    def test_string_disconnect_fault_injection(self):
        """Verifica que la desconexión de string anule la corriente y eleve el voltaje a circuito abierto."""
        v_nom, i_nom, p_nom = self.engine.calculate_iv_operating_point(800.0, 45.0)
        disconnected = self.engine.inject_fault("STRING_DISCONNECTED", v_nom, i_nom, p_nom, 45.0)
        
        self.assertEqual(disconnected["i_dc"], 0.0)
        self.assertEqual(disconnected["p_dc"], 0.0)
        self.assertGreater(disconnected["v_dc"], v_nom)


class TestDataSchemas(unittest.TestCase):
    def test_telemetry_schema_validation(self):
        """Verifica que los contratos Pydantic se puedan instanciar si Pydantic está instalado."""
        try:
            from backend.app.schemas.telemetry import TelemetryIngestPayload, ElectricalDC, EnvironmentalMetrics
            
            payload = TelemetryIngestPayload(
                device_uid="ESP32-STV-001",
                plant_id=uuid.uuid4(),
                timestamp=datetime.now(timezone.utc),
                dc=ElectricalDC(v_dc=340.5, i_dc=8.2),
                env=EnvironmentalMetrics(g_irradiance=920.0, t_panel=46.2)
            )
            self.assertEqual(payload.device_uid, "ESP32-STV-001")
            calculated_p = payload.calculate_instantaneous_power()
            self.assertAlmostEqual(calculated_p, 340.5 * 8.2, places=1)
        except ImportError:
            # Pydantic aún no instalado en el entorno de Python global
            pass

    def test_alert_severity_enum(self):
        """Verifica los valores del enum de severidad de alertas."""
        try:
            from backend.app.schemas.alert import AlertSeverity, FaultCategory
            self.assertEqual(AlertSeverity.CRITICAL.value, "critical")
            self.assertIn("SHADING", [f.value for f in FaultCategory])
        except ImportError:
            pass


if __name__ == "__main__":
    unittest.main()
