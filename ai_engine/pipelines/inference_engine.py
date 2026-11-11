"""
MOTOR DE INFERENCIA Y DIAGNÓSTICO PREDICTIVO EN TIEMPO REAL (STV)
=================================================================
Ejecuta la tubería híbrida:
1. Modelo Físico Sandia + Regresor ML para Potencia Esperada.
2. Cálculo de Pérdida Porcentual y Delta P.
3. Detector de Anomalías No Supervisado (Isolation Forest).
4. Clasificador Causal Multiclase con Certeza Probabilística y Explicabilidad (XAI).
5. Generación de Explicaciones Prescriptivas y Recomendaciones de Campo.
"""
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import numpy as np
try:
    import joblib
except ImportError:
    joblib = None

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.pv_physics_simulator import PhotovoltaicPhysicsEngine
from backend.app.schemas.alert import AIDiagnosticResult, FaultCategory


class PVInferenceEngine:
    def __init__(self, models_dir: str = ""):
        if not models_dir:
            models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
        
        self.models_dir = models_dir
        self.physics_engine = PhotovoltaicPhysicsEngine(p_stc_watts=1000.0, gamma_temp_coeff=-0.0038)
        
        self.regressor = None
        self.anomaly_detector = None
        self.classifier_bundle = None
        self.load_models()

    def load_models(self):
        """Carga los modelos entrenados desde disco si existen."""
        if joblib is None:
            return
        reg_file = os.path.join(self.models_dir, "pv_power_regressor.joblib")
        iso_file = os.path.join(self.models_dir, "pv_anomaly_detector.joblib")
        clf_file = os.path.join(self.models_dir, "pv_fault_classifier.joblib")

        if os.path.exists(reg_file):
            self.regressor = joblib.load(reg_file)
        if os.path.exists(iso_file):
            self.anomaly_detector = joblib.load(iso_file)
        if os.path.exists(clf_file):
            self.classifier_bundle = joblib.load(clf_file)

    def diagnose_measurement(
        self,
        v_dc: float,
        i_dc: float,
        g_irradiance: float,
        t_panel: float,
        t_ambient: float = 25.0,
        rh_ambient: float = 55.0,
        hour_of_day: float = 12.0,
        plant_id: str = "plant-01",
        device_uid: str = "STV-ESP32-S3-001"
    ) -> AIDiagnosticResult:
        """
        Ejecuta el diagnóstico integral sobre un vector de telemetría instantáneo.
        """
        p_actual = round(v_dc * i_dc, 2)

        # 1. Potencia esperada física y por Machine Learning
        p_physical = self.physics_engine.calculate_theoretical_power(g_irradiance, t_panel)
        
        if self.regressor is not None and g_irradiance > 10.0:
            reg_input = np.array([[g_irradiance, t_panel, t_ambient, rh_ambient, hour_of_day]])
            p_ml = float(self.regressor.predict(reg_input)[0])
            p_expected = round((p_physical * 0.4) + (p_ml * 0.6), 2)  # Ensamble híbrido física + ML
        else:
            p_expected = p_physical

        # 2. Cálculo de Pérdida
        delta_p = round(max(0.0, p_expected - p_actual), 2)
        loss_pct = 0.0
        if p_expected > 15.0:
            loss_pct = round((delta_p / p_expected) * 100.0, 2)
        pr = round(p_actual / max(1.0, p_expected), 4)

        # 3. Detección de Anomalía (Isolation Forest)
        is_anomaly = False
        anomaly_score = 0.0
        if self.anomaly_detector is not None:
            iso_vec = np.array([[g_irradiance, t_panel, v_dc, i_dc, p_actual, delta_p]])
            iso_pred = self.anomaly_detector.predict(iso_vec)[0]  # 1 = normal, -1 = anomalía
            anomaly_score = float(self.anomaly_detector.decision_function(iso_vec)[0])
            is_anomaly = (iso_pred == -1) or (loss_pct > 25.0 and g_irradiance >= 300.0)
        else:
            is_anomaly = loss_pct > 25.0 and g_irradiance >= 300.0

        # 4. Clasificación Causal de Falla
        fault_cat = FaultCategory.NORMAL
        confidence = 0.95
        explanation = "La instalación opera dentro de su curva de rendimiento nominal."
        recommendation = "No se requiere intervención técnica. Mantener ciclo regular de monitoreo."
        shap_weights = {"Irradiancia (G)": 0.40, "Voltaje (V)": 0.30, "Corriente (I)": 0.30}

        if is_anomaly:
            if self.classifier_bundle is not None:
                clf = self.classifier_bundle["model"]
                classes = self.classifier_bundle["classes"]
                clf_vec = np.array([[g_irradiance, t_panel, v_dc, i_dc, p_actual, delta_p, pr]])
                
                probs = clf.predict_proba(clf_vec)[0]
                best_idx = int(np.argmax(probs))
                best_class = classes[best_idx]
                confidence = float(probs[best_idx])
                
                # Mapear al enum de FaultCategory
                try:
                    fault_cat = FaultCategory(best_class)
                except ValueError:
                    fault_cat = FaultCategory.SHADING

                shap_weights = self.classifier_bundle.get("feature_importances", {})
            else:
                # Reglas analíticas auxiliares si aún no se han entrenado los pesos
                if i_dc < 0.1:
                    fault_cat = FaultCategory.STRING_DISCONNECTED
                    confidence = 0.98
                elif loss_pct > 50.0:
                    fault_cat = FaultCategory.SHADING
                    confidence = 0.88
                else:
                    fault_cat = FaultCategory.SOILING
                    confidence = 0.80

            # 5. Generación prescriptiva según categoría
            if fault_cat == FaultCategory.SHADING:
                explanation = f"Se detecta generación significativamente inferior a la esperada (-{loss_pct}% de pérdida). Caída severa en corriente DC ({i_dc} A) mientras la tensión permanece moderadamente alta ({v_dc} V), compatible con sombra sobre sub-módulos y activación de diodos de bypass."
                recommendation = "Inspeccionar visualmente sombras proyectadas de árboles, postes o vegetación sobre el arreglo. Comprobar diodos de bypass en la caja de conexiones."
            elif fault_cat == FaultCategory.SOILING:
                explanation = f"Disminución homogénea de corriente con tensión nominal estable. Compatible con acumulación progresiva de polvo o suciedad atmosférica (pérdida del {loss_pct}%)."
                recommendation = "Programar jornada de limpieza y lavado de módulos con agua desmineralizada al amanecer o atardecer."
            elif fault_cat == FaultCategory.STRING_DISCONNECTED:
                explanation = f"Corriente en 0.0 A con voltaje elevado a tensión de circuito abierto ({v_dc} V). Desconexión completa del string."
                recommendation = "Verificar inmediatamente fusible gPV en string box, seccionador bajo carga y conectores MC4."
            elif fault_cat == FaultCategory.INVERTER_FAULT:
                explanation = f"Inversor sin inyección AC ni absorción de corriente DC a pesar de alta radiación ({g_irradiance} W/m²)."
                recommendation = "Revisar código de alarma en pantalla del inversor, magnetotérmico AC y protecciones de red."
            elif fault_cat == FaultCategory.HOTSPOT:
                explanation = f"Temperatura de módulo excesivamente alta ({t_panel}°C) con gradiente térmico anormal respecto al ambiente."
                recommendation = "Efectuar inspección termográfica IR urgente para descartar rotura de célula o punto caliente que pueda dañar el laminado."
            elif fault_cat == FaultCategory.SENSOR_FAULT:
                explanation = "Incoherencia física severa detectada entre las lecturas de los sensores."
                recommendation = "Inspeccionar cableado de señal, bus I2C/RS-485 y calibración del piranómetro."

        return AIDiagnosticResult(
            plant_id=uuid.UUID(plant_id) if isinstance(plant_id, str) and len(plant_id) == 36 else uuid.uuid4(),
            device_uid=device_uid,
            timestamp=datetime.now(timezone.utc),
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            p_expected=p_expected,
            p_actual=p_actual,
            delta_power=delta_p,
            loss_percentage=loss_pct,
            fault_category=fault_cat,
            confidence_level=confidence,
            root_cause_explanation=explanation,
            recommended_action=recommendation,
            features_importance=shap_weights
        )


if __name__ == "__main__":
    engine = PVInferenceEngine()
    
    print("=" * 70)
    print("EJECUTANDO DIAGNÓSTICO SOBRE EL CASO OBLIGATORIO DEL USUARIO:")
    print("G = 950 W/m² | T_panel = 48.0 °C | V = 170 V | I = 1.8235 A (P = 310 W)")
    print("=" * 70)
    
    res = engine.diagnose_measurement(
        v_dc=170.0,
        i_dc=1.8235,
        g_irradiance=950.0,
        t_panel=48.0,
        t_ambient=28.0,
        hour_of_day=12.5
    )
    
    print(f"\n• ¿Es anomalía?: {res.is_anomaly}")
    print(f"• Potencia Esperada: {res.p_expected} W")
    print(f"• Potencia Real: {res.p_actual} W")
    print(f"• Pérdida Energética: {res.loss_percentage}% (-{res.delta_power} W)")
    print(f"• Categoría de Falla Diagnostica: {res.fault_category.value}")
    print(f"• Certeza Probabilística: {res.confidence_level * 100:.1f}%")
    print(f"• Causa Raíz Explicada: {res.root_cause_explanation}")
    print(f"• Recomendación Prescriptiva: {res.recommended_action}")
    print("=" * 70)
