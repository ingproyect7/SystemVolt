import React from 'react';
import { Cpu, Brain, Network, ShieldAlert, BarChart3, HelpCircle } from 'lucide-react';
import { AIDiagnosticCard } from '../components/AIDiagnosticCard';

export const AIDiagnostics: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Cabecera del Módulo IA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Cpu className="h-5 w-5 text-amber-500" />
            MOTOR DE INTELIGENCIA ARTIFICIAL & DIAGNÓSTICO PREDICTIVO
          </h2>
          <p className="text-xs text-slate-400">Arquitectura Híbrida: Física de Semiconductores + Machine Learning + Explicabilidad XAI</p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20 px-3 py-1.5 rounded-lg">
          <Brain className="h-4 w-4" />
          <span>Inferencia Local & Edge Analytics Activa</span>
        </div>
      </div>

      {/* Diagnóstico Activo en la Planta Piloto (Caso Obligatorio) */}
      <AIDiagnosticCard
        isAnomaly={true}
        faultCategory="DESCONEXIÓN / SOMBRA CRÍTICA"
        confidence={0.885}
        expectedPower={800}
        actualPower={310}
        lossPercentage={61.25}
        explanation="Se detectó una discrepancia severa de potencia bajo alta radiación solar (950 W/m²) y temperatura de módulo de 48.0°C. La corriente medida colapsó a 1.82 A frente a 4.55 A esperados, mientras el voltaje permaneció en 170 V (reducción moderada por conducción de diodos de bypass). El Autoencoder arrojó un error de reconstrucción MSE = 0.42 (umbral normal: 0.15)."
        recommendation="1. Despachar cuadrilla técnica para inspección de sombras físicas en el String 01. 2. Verificar apriete y resistencia de contacto en conectores MC4. 3. Comprobar continuidad de fusibles gPV de la caja de combinación."
        shapFeatures={{
          "Déficit de Corriente DC (I)": 0.52,
          "Irradiancia Elevada (950 W/m²)": 0.26,
          "Tensión Operativa Nominal (V)": 0.15,
          "Temperatura Celular (48°C)": 0.07
        }}
      />

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
            <h4>2. Predictor XGBoost</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Modelo supervisado de gradiente que aprende no-linealidades atmosféricas, ángulo cenital solar y radiación difusa para predecir P_esperada.
          </p>
          <span className="mt-3 block text-[11px] font-mono text-emerald-400 font-bold">R² Score: 0.984</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm mb-2">
            <Network className="h-4 w-4" />
            <h4>3. Autoencoder Profundo</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Red neuronal no supervisada que detecta desviaciones multivariables del vector de telemetría sin depender de umbrales rígidos.
          </p>
          <span className="mt-3 block text-[11px] font-mono text-emerald-400 font-bold">F1-Score: 0.941</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
          <div className="flex items-center space-x-2 text-amber-400 font-semibold text-sm mb-2">
            <ShieldAlert className="h-4 w-4" />
            <h4>4. Clasificador Causal + XAI</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Discrimina entre sombreado, suciedad (soiling), desconexión de string, falla de inversor o hotspot térmico, entregando explicabilidad SHAP.
          </p>
          <span className="mt-3 block text-[11px] font-mono text-emerald-400 font-bold">Precisión: 92.8%</span>
        </div>
      </div>
    </div>
  );
};
