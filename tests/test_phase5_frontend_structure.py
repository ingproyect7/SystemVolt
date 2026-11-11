"""
SUITE DE PRUEBAS UNITARIAS: FASE 5 (ESTRUCTURA Y CONTRATOS DEL FRONTEND WEB)
===========================================================================
Valida la integridad de los componentes de la interfaz de usuario industrial,
su configuración y la congruencia de los tipos de datos TypeScript con el Backend.
"""
import unittest
import os
import sys

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestFrontendArchitecture(unittest.TestCase):
    def setUp(self):
        self.frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

    def test_01_configuration_files_exist(self):
        """Verifica la existencia de los archivos maestros de configuración del frontend."""
        config_files = ["package.json", "vite.config.ts", "tailwind.config.js", "postcss.config.js", "index.html"]
        for cf in config_files:
            file_path = os.path.join(self.frontend_dir, cf)
            self.assertTrue(os.path.exists(file_path), f"Archivo no encontrado: {cf}")

    def test_02_components_exist(self):
        """Verifica que todos los componentes modulares de visualización industrial existan."""
        components = [
            "Navbar.tsx",
            "KPICard.tsx",
            "TelemetryChart.tsx",
            "AIDiagnosticCard.tsx",
            "AlertTable.tsx"
        ]
        comp_dir = os.path.join(self.frontend_dir, "src", "components")
        for comp in components:
            full_path = os.path.join(comp_dir, comp)
            self.assertTrue(os.path.exists(full_path), f"Componente no encontrado: {comp}")

    def test_03_pages_exist(self):
        """Verifica que todos los módulos y vistas funcionales solicitados estén implementados."""
        pages = [
            "Dashboard.tsx",
            "Monitoring.tsx",
            "AIDiagnostics.tsx",
            "AlertsPage.tsx"
        ]
        page_dir = os.path.join(self.frontend_dir, "src", "pages")
        for page in pages:
            full_path = os.path.join(page_dir, page)
            self.assertTrue(os.path.exists(full_path), f"Página no encontrada: {page}")

    def test_04_typescript_type_definitions(self):
        """Verifica que los tipos TypeScript contengan las magnitudes físicas y de diagnóstico requeridas."""
        types_file = os.path.join(self.frontend_dir, "src", "types", "solar.ts")
        self.assertTrue(os.path.exists(types_file))
        
        with open(types_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("TelemetryPoint", content)
            self.assertIn("p_expected", content)
            self.assertIn("g_irradiance", content)
            self.assertIn("t_panel", content)
            self.assertIn("SystemAlert", content)
            self.assertIn("AIDiagnostic", content)
            self.assertIn("SHADING", content)
            self.assertIn("SOILING", content)

    def test_05_package_json_dependencies(self):
        """Verifica que package.json contenga las dependencias de React y utilidades industriales."""
        pkg_file = os.path.join(self.frontend_dir, "package.json")
        with open(pkg_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("react", content)
            self.assertIn("lucide-react", content)
            self.assertIn("tailwindcss", content)


if __name__ == "__main__":
    unittest.main()
