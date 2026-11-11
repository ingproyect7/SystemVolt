"""
SUITE DE PRUEBAS UNITARIAS: FASE 8 (HISTÉRESIS, BALANCE ENERGÉTICO Y FINANZAS)
=============================================================================
Valida la efectividad del filtro de histéresis contra falsas alarmas,
la precisión del cálculo de energía en kWh y la estimación de pérdidas en USD.
"""
import unittest
import os
import sys

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.dynamic_day_simulation import DynamicDaySimulator


class TestHysteresisAndEnergySimulation(unittest.TestCase):
    def setUp(self):
        self.simulator = DynamicDaySimulator(
            nominal_capacity_kw=1.0,
            energy_tariff_usd_kwh=0.18,
            hysteresis_cycles_threshold=3
        )

    def test_01_simulation_completes_all_daytime_intervals(self):
        """Verifica que el ciclo diurno contemple exactamente 49 intervalos de 15 minutos."""
        report = self.simulator.simulate_24h_cycle()
        self.assertEqual(report["total_points"], 49)

    def test_02_hysteresis_filter_blocks_transient_cloud_false_alarm(self):
        """Verifica que el paso rápido de una nube transitoria no dispare alertas prematuras."""
        report = self.simulator.simulate_24h_cycle()
        
        # Debe haber al menos 1 falsa alarma descartada por falta de persistencia
        self.assertGreaterEqual(report["false_alarms_blocked_by_hysteresis"], 1)

    def test_03_persistent_faults_trigger_confirmed_alerts(self):
        """Verifica que anomalías persistentes (>3 ciclos) sí generen alertas confirmadas."""
        report = self.simulator.simulate_24h_cycle()
        
        self.assertGreater(report["confirmed_alerts_count"], 0)
        # Verificar que la categoría SHADING esté entre las alertas confirmadas
        categories = [a["category"] for a in report["alerts_summary"]]
        self.assertIn("SHADING", categories)

    def test_04_energy_integration_and_financial_loss_coherence(self):
        """Verifica la matemática de integración en kWh y cálculo de pérdida en USD."""
        report = self.simulator.simulate_24h_cycle()
        
        # La energía real debe ser estrictamente menor a la esperada debido a las fallas inyectadas
        self.assertLess(report["energy_actual_kwh"], report["energy_expected_kwh"])
        self.assertGreater(report["energy_loss_kwh"], 0.5)
        
        # Verificar coherencia matemática: Pérdida = (E_esp - E_real) * Tarifa
        expected_financial_loss = round(report["energy_loss_kwh"] * 0.18, 3)
        self.assertAlmostEqual(report["financial_loss_usd"], expected_financial_loss, places=2)
        
        # El PR debe estar en un rango coherente con las fallas inyectadas (50% a 80%)
        self.assertGreaterEqual(report["overall_performance_ratio_pct"], 50.0)
        self.assertLessEqual(report["overall_performance_ratio_pct"], 80.0)


if __name__ == "__main__":
    unittest.main()
