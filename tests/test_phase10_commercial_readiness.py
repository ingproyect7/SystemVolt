"""
SUITE DE PRUEBAS UNITARIAS: FASE 10 (PREPARACIÓN COMERCIAL Y EMPAQUETADO SAAS)
=============================================================================
Verifica que la documentación de negocio, arquitectura de despliegue industrial
y esquemas multi-tenant estén completos para explotación comercial.
"""
import unittest
import os
import sys

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestCommercialReadiness(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_01_saas_business_model_documentation(self):
        """Verifica que el plan de negocio SaaS contenga los tiers de precios y márgenes operativos."""
        doc_path = os.path.join(self.base_dir, "docs", "commercial_saas_business_model.md")
        self.assertTrue(os.path.exists(doc_path))
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("PLAN RESIDENCIAL", content)
            self.assertIn("PLAN COMERCIAL", content)
            self.assertIn("Margen Bruto", content)
            self.assertIn("Modbus SunSpec", content)

    def test_02_production_deployment_guide(self):
        """Verifica la guía de despliegue, aprovisionamiento de gateways y ciberseguridad IEC 62443."""
        doc_path = os.path.join(self.base_dir, "docs", "production_deployment_guide.md")
        self.assertTrue(os.path.exists(doc_path))
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("REVERSE PROXY", content)
            self.assertIn("TLS 1.3", content)
            self.assertIn("IEC 62443", content)
            self.assertIn("RPO", content)

    def test_03_verification_script_exists(self):
        """Verifica que el script maestro de certificación de ingeniería esté presente."""
        script_path = os.path.join(self.base_dir, "scripts", "verify_stv_system.py")
        self.assertTrue(os.path.exists(script_path))


if __name__ == "__main__":
    unittest.main()
