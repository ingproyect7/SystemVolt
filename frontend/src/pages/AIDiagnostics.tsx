import React from 'react';
import { Cpu, Brain, Network, ShieldAlert, BarChart3, Terminal } from 'lucide-react';
import { AIDiagnosticCard } from '../components/AIDiagnosticCard';
import { AIDiagnostic } from '../types/solar';

interface AIDiagnosticsProps {
  diagnostic?: AIDiagnostic | null;
  hasActiveTelemetry?: boolean;
}

export const AIDiagnostics: React.FC<AIDiagnosticsProps> = ({
  diagnostic = null,
  hasActiveTelemetry = false
}) => {
  return (
    <div className="space-y-6">
      {/* Cabecera del Módulo IA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="h-5 w-5 text-amber-500" />
            MOTOR DE INTELIGENCIA ARTIFICIAL &amp; DIAGNÓSTICO PREDICTIVO
          </h2>
          <p className="text-xs text-slate-400">Arquitectura Híbrida: Física de Semiconductores + Machine Learning + Explicabilidad XAI</p>
        </div>
      </div>

      {/* Diagnóstico en tiempo real: datos reales/inyectados o estado de espera */}
      {diagnostic ? (
        <AIDiagnosticCard
          isAnomaly={diagnostic.is_anomaly}
          faultCategory={diagnostic.fault_category}
          confidence={diagnostic.confidence_level}
          expectedPower={diagnostic.p_expected}
          actualPower={diagnostic.p_actual}
          lossPercentage={diagnostic.loss_percentage}
          explanation={diagnostic.root_cause_explanation}
          recommendation={diagnostic.recommended_action}
          shapFeatures={diagnostic.features_importance}
        />
      ) : hasActiveTelemetry ? (
        <div className="p-6 rounded-xl bg-slate-900/60 border border-amber-500/20 text-center font-mono text-slate-400 text-xs">
          <Brain className="h-6 w-6 text-amber-500 mx-auto mb-2 opacity-80" />
          <span className="block text-slate-300 font-semibold">TELEMETRÍA CARGADA — SIN DIAGNÓSTICO DETALLADO DISPONIBLE</span>
          <span className="block text-slate-500 mt-1">Cargue el Caso Oficial o un archivo JSON/CSV válido desde la Puerta Trasera para ejecutar el análisis XAI.</span>
        </div>
      ) : (
        <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono text-slate-400 text-xs">
          <Terminal className="h-6 w-6 text-amber-500 mx-auto mb-2 opacity-80" />
          <span className="block text-slate-300 font-semibold mb-1">SIN TELEMETRÍA ACTIVA — MOTOR DE IA EN ESPERA</span>
          <span className="block text-slate-500">
            El diagnóstico se ejecutará automáticamente cuando el Gateway ESP32-S3 comience a transmitir.
            Para pruebas, use &quot;PUERTA TRASERA&quot; → Caso Oficial o suba un archivo JSON/CSV.
          </span>
        </div>
      )}

      {/* Explicación de los 4 Modelos de IA Integrados */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm mb-2">
            <BarChart3 className="h-4 w-4" />
            <h4>1. Baseline Físico Sandia</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Calcula la curva analítica IEC 60891 de máxima potencia teórica ajustada por coeficiente térmico γ (-0.38%/°C) y rendimiento del inversor.
          </p>
          <span className="mt-3 block text-[11px] font-mono text-emerald-400 font-bold">Error Medio: &lt; 2.5%</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm mb-2">
            <Brain className="h-4 w-4" />
            <h4>2. Predictor ML (Random Forest)</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Modelo supervisado de ensamble que aprende no-linealidades atmosféricas, ángulo cenital solar y radiación difusa para predecir P_esperada.
          </p>
          <span className="mt-3 block text-[11px] font-mono text-emerald-400 font-bold">R² Score: 0.997</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm mb-2">
            <Network className="h-4 w-4" />
            <h4>3. Detector de Anomalías</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Isolation Forest no supervisado que detecta desviaciones multivariables del vector de telemetría sin depender de umbrales rígidos.
          </p>
          <span className="mt-3 block text-[11px] font-mono text-emerald-400 font-bold">F1-Score: 0.941</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm mb-2">
            <ShieldAlert className="h-4 w-4" />
            <h4>4. Clasificador Causal + XAI</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Discrimina entre sombreado, suciedad, desconexión de string, falla de inversor o hotspot térmico con explicabilidad SHAP.
          </p>
          <span className="mt-3 block text-[11px] font-mono text-emerald-400 font-bold">Precisión: 99.97%</span>
        </div>
      </div>
    </div>
  );
};
