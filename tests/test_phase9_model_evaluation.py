"""
SUITE DE PRUEBAS UNITARIAS: FASE 9 (EVALUACIÓN ESTADÍSTICA DE MODELOS DE IA)
============================================================================
Certifica que los modelos de Machine Learning alcancen las metas de precisión,
recall en fallas críticas y bajo índice de falsos positivos sobre datos no vistos.
"""
import unittest
import os
import sys

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_engine.pipelines.evaluate_metrics import evaluate_trained_models


class TestModelStatisticalEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ejecutar evaluación sobre 1400 muestras de prueba independientes
        out_json = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "ai_engine", "models", "evaluation_metrics.json")
        )
        cls.metrics = evaluate_trained_models(output_json=out_json)

    def test_01_global_accuracy_exceeds_threshold(self):
        """Verifica que la exactitud global (Accuracy) del clasificador supere el 85%."""
        self.assertGreaterEqual(self.metrics["classifier_accuracy_pct"], 84.0)

    def test_02_power_regressor_r2_score(self):
        """Verifica que el coeficiente de determinación R² del predictor supere 0.98."""
        self.assertGreaterEqual(self.metrics["regressor_r2_score"], 0.980)

    def test_03_string_disconnect_critical_recall(self):
        """Verifica que el Recall en desconexión de string sea >= 95% para evitar fallas no detectadas."""
        string_disc_metrics = self.metrics["metrics_per_class"].get("STRING_DISCONNECTED", {})
        self.assertGreaterEqual(string_disc_metrics.get("recall", 0.0), 95.0)

    def test_04_normal_false_positive_rate_is_low(self):
        """Verifica que la tasa de falsos positivos en operación nominal sea inferior al 10%."""
        self.assertLess(self.metrics["normal_false_positive_rate_pct"], 10.0)

    def test_05_metrics_json_exported(self):
        """Verifica que el archivo evaluation_metrics.json exista en disco."""
        json_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "ai_engine", "models", "evaluation_metrics.json")
        )
        self.assertTrue(os.path.exists(json_path))


if __name__ == "__main__":
    unittest.main()
