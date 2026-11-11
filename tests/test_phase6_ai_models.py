"""
SUITE DE PRUEBAS UNITARIAS: FASE 6 (PIPELINE DE INTELIGENCIA ARTIFICIAL)
========================================================================
Valida la generación del dataset, el entrenamiento y evaluación de los modelos
y la resolución exacta del caso obligatorio mediante el motor de inferencia.
"""
import unittest
import os
import sys

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_engine.pipelines.dataset_generator import generate_pv_dataset
from ai_engine.pipelines.inference_engine import PVInferenceEngine
from backend.app.schemas.alert import FaultCategory


class TestAIModelsAndInference(unittest.TestCase):
    def test_01_dataset_generation_physics(self):
        """Verifica que el generador sintético cree registros coherentes con la física de semiconductores."""
        data = generate_pv_dataset(samples_per_category=20)
        self.assertEqual(len(data), 140)  # 7 categorías * 20
        
        # Verificar que en la categoría SHADING la corriente sea menor al 60% de la nominal
        shaded = [d for d in data if d["fault_category"] == "SHADING"][0]
        self.assertGreater(shaded["delta_p"], 0)
        self.assertLess(shaded["performance_ratio"], 0.65)

        # Verificar que en STRING_DISCONNECTED (1 de 2 strings desconectado) la corriente cae al 50%
        disconnected = [d for d in data if d["fault_category"] == "STRING_DISCONNECTED"][0]
        self.assertLessEqual(disconnected["i_dc"], 1.5)

        # Verificar que en INVERTER_FAULT la corriente total sea exactamente 0.0
        inv_fault = [d for d in data if d["fault_category"] == "INVERTER_FAULT"][0]
        self.assertEqual(inv_fault["i_dc"], 0.0)
        self.assertEqual(inv_fault["p_dc"], 0.0)

    def test_02_mandatory_case_inference_resolution(self):
        """
        Prueba obligatoria del requerimiento:
        G = 950 W/m², T_panel = 48.0 °C, P_esperada ~ 800-845 W, P_real = 310 W.
        """
        engine = PVInferenceEngine()
        
        # V=170V, I=1.8235A -> P_real = 310.0 W
        result = engine.diagnose_measurement(
            v_dc=170.0,
            i_dc=1.8235,
            g_irradiance=950.0,
            t_panel=48.0,
            t_ambient=28.0,
            hour_of_day=12.5
        )

        # 1. El sistema debe clasificarlo inequívocamente como anomalía
        self.assertTrue(result.is_anomaly)

        # 2. La potencia esperada debe ser > 800 W
        self.assertGreaterEqual(result.p_expected, 800.0)
        self.assertAlmostEqual(result.p_actual, 310.0, places=1)

        # 3. La pérdida calculada debe ser > 60% (alrededor de 61.25% - 63.3%)
        self.assertGreater(result.loss_percentage, 60.0)

        # 4. Diagnóstico de causa raíz probable y nivel de certeza > 80%
        self.assertIn(result.fault_category, [FaultCategory.SHADING, FaultCategory.STRING_DISCONNECTED])
        self.assertGreaterEqual(result.confidence_level, 0.80)

        # 5. La explicación y recomendación deben estar fundamentadas
        self.assertIn("pérdida", result.root_cause_explanation.lower())
        self.assertGreater(len(result.recommended_action), 20)
        self.assertIsNotNone(result.features_importance)


if __name__ == "__main__":
    unittest.main()
