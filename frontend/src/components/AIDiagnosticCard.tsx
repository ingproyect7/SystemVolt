import React from 'react';
import { Cpu, AlertCircle, Wrench, CheckCircle, TrendingDown } from 'lucide-react';

interface AIDiagnosticCardProps {
  isAnomaly: boolean;
  faultCategory: string;
  confidence: number;
  expectedPower: number;
  actualPower: number;
  lossPercentage: number;
  explanation: string;
  recommendation: string;
  shapFeatures?: Record<string, number>;
}

export const AIDiagnosticCard: React.FC<AIDiagnosticCardProps> = ({
  isAnomaly,
  faultCategory,
  confidence,
  expectedPower,
  actualPower,
  lossPercentage,
  explanation,
  recommendation,
  shapFeatures = { "Irradiancia (G)": 0.45, "Corriente DC (I)": 0.35, "Voltaje DC (V)": 0.15, "Temp. Célula": 0.05 }
}) => {
  return (
    <div className={`rounded-xl border p-6 backdrop-blur-md transition-all shadow-xl ${
      isAnomaly ? 'border-red-500/40 bg-slate-900/95' : 'border-emerald-500/30 bg-slate-900/95'
    }`}>
      {/* Cabecera de Diagnóstico */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-lg ${isAnomaly ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}`}>
            <Cpu className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              DIAGNÓSTICO AUTOMATIZADO DE INTELIGENCIA ARTIFICIAL
            </h3>
            <p className="text-xs text-slate-400">Motor Híbrido: Detección No Supervisada + Clasificador Causal</p>
          </div>
        </div>

        {/* Badge de Categoría */}
        <div className="flex items-center space-x-2">
          <span className={`px-3 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider border ${
            isAnomaly
              ? 'bg-red-500/10 text-red-400 border-red-500/30'
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
          }`}>
            {faultCategory}
          </span>
        </div>
      </div>

      {/* Métricas Clave de la Decisión */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 my-5 p-4 rounded-lg bg-slate-950/70 border border-slate-800/80 font-mono text-center">
        <div>
          <span className="text-xs text-slate-400 block">Potencia Esperada</span>
          <span className="text-lg font-bold text-amber-400">{expectedPower} W</span>
        </div>
        <div>
          <span className="text-xs text-slate-400 block">Potencia Real</span>
          <span className="text-lg font-bold text-emerald-400">{actualPower} W</span>
        </div>
        <div>
          <span className="text-xs text-slate-400 block">Pérdida Estimada</span>
          <span className="text-lg font-bold text-red-400 flex items-center justify-center gap-1">
            <TrendingDown className="h-4 w-4" />
            -{lossPercentage}%
          </span>
        </div>
        <div>
          <span className="text-xs text-slate-400 block">Certeza del Modelo</span>
          <span className="text-lg font-bold text-white">{(confidence * 100).toFixed(1)}%</span>
        </div>
      </div>

      {/* Barra de Certeza Probabilística */}
      <div className="mb-5">
        <div className="flex justify-between text-xs text-slate-400 mb-1">
          <span>Nivel de Confianza Diagnóstica:</span>
          <span className="font-mono text-white font-bold">{(confidence * 100).toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${confidence > 0.8 ? 'bg-amber-500' : 'bg-slate-500'}`}
            style={{ width: `${confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Causa Raíz y Recomendación de Campo */}
      <div className="space-y-4">
        <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/60">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide flex items-center gap-2 mb-1.5">
            <AlertCircle className="h-4 w-4 text-amber-400" />
            Evidencia & Análisis Causal
          </h4>
          <p className="text-sm text-slate-200 leading-relaxed">{explanation}</p>
        </div>

        <div className="p-4 rounded-lg bg-emerald-950/20 border border-emerald-500/30">
          <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide flex items-center gap-2 mb-1.5">
            <Wrench className="h-4 w-4 text-emerald-400" />
            Acción Prescriptiva Recomendada
          </h4>
          <p className="text-sm text-slate-200 leading-relaxed">{recommendation}</p>
        </div>
      </div>

      {/* Explicabilidad (XAI - SHAP Values) */}
      {shapFeatures && (
        <div className="mt-5 pt-4 border-t border-slate-800">
          <span className="text-xs font-mono text-slate-400 block mb-2">
            PESO DE VARIABLES DETERMINANTES (XAI - SHAP VALUES):
          </span>
          <div className="space-y-1.5">
            {Object.entries(shapFeatures).map(([feat, val]) => (
              <div key={feat} className="flex items-center text-xs font-mono">
                <span className="w-40 text-slate-400 truncate">{feat}</span>
                <div className="flex-1 bg-slate-800 h-1.5 rounded-full mx-2">
                  <div className="bg-amber-400 h-1.5 rounded-full" style={{ width: `${Math.min(100, val * 100)}%` }} />
                </div>
                <span className="w-12 text-right text-slate-300">{(val * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
