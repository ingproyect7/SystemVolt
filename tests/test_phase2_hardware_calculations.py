"""
SUITE DE PRUEBAS UNITARIAS: FASE 2 (CÁLCULOS DE HARDWARE Y AISLAMIENTO)
=======================================================================
Valida que el diseño electrónico de acondicionamiento cumpla con los límites
de aislamiento galvánico, rangos lineales y márgenes de disipación térmica.
"""
import unittest
import os
import sys

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.hardware_calibration_calculator import (
    calculate_voltage_sensing_stage,
    calculate_current_sensing_stage
)


class TestHardwareElectricalDesign(unittest.TestCase):
    def test_voltage_sensing_safe_linear_range(self):
        """Verifica que a 1000V DC el amplificador de aislamiento AMC1301 no sature."""
        v_stage = calculate_voltage_sensing_stage(v_string_max=1000.0)
        
        # El AMC1301 tiene un rango lineal de ±250 mV. Con 249 Ω da 248.9 mV
        self.assertTrue(v_stage["amc1301_linear_limit_ok"])
        self.assertLessEqual(v_stage["v_in_amc1301_diff_volts"], 0.250)
        # La salida diferencial hacia el ADC debe estar dentro del rango PGA ±2.048V
        self.assertLessEqual(v_stage["v_out_diff_amc1301_volts"], 2.05)

    def test_resistor_thermal_dissipation_safety(self):
        """Verifica que la potencia disipada por los resistores cumpla márgenes de derating térmico."""
        v_stage = calculate_voltage_sensing_stage(v_string_max=1000.0)
        
        # Cada resistor superior es de 1W nominal. La disipación real debe ser < 0.5W (derating 50%)
        self.assertLess(v_stage["power_per_top_resistor_watts"], 0.50)
        # La corriente drenada del string debe ser despreciable (< 2 mA) para no alterar la generación
        self.assertLess(v_stage["current_drained_ma"], 2.0)

    def test_voltage_adc_resolution(self):
        """Verifica que la resolución del ADC ADS1115 permita medir variaciones menores a 0.05 V."""
        v_stage = calculate_voltage_sensing_stage(v_string_max=1000.0)
        self.assertLess(v_stage["adc_lsb_resolution_volts"], 0.05)

    def test_current_sensing_range_and_resolution(self):
        """Verifica que a 40A de corriente DC el sensor ACS758 no sobrepase el rango seguro del ADC (3.3V)."""
        i_stage = calculate_current_sensing_stage(i_max_amps=40.0)
        
        self.assertTrue(i_stage["adc_within_safe_range"])
        self.assertLessEqual(i_stage["v_adc_at_imax"], 3.30)
        # La resolución debe ser más fina que 10 mA
        self.assertLess(i_stage["current_resolution_ma"], 10.0)
        # La disipación Joule en el sensor debe ser menor a 0.2 W
        self.assertLess(i_stage["power_dissipation_joule_watts"], 0.20)

    def test_pin_definitions_header_exists(self):
        """Verifica la existencia del archivo de cabecera C++ con constantes de calibración."""
        header_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "firmware", "include", "pin_definitions.h")
        )
        self.assertTrue(os.path.exists(header_path))
        with open(header_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("PIN_I2C_SDA", content)
            self.assertIn("CALIB_VOLTAGE_SCALE", content)
            self.assertIn("CALIB_ACS758_SENS", content)


if __name__ == "__main__":
    unittest.main()
