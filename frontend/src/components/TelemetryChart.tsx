import React from 'react';
import { TelemetryPoint } from '../types/solar';

interface TelemetryChartProps {
  data: TelemetryPoint[];
  title?: string;
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  data,
  title = "Curva Temporal: Potencia Real vs. Potencia Esperada vs. Irradiancia"
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-8 shadow-xl text-center">
        <div className="flex items-center justify-center space-x-2 text-slate-400 text-xs font-mono mb-2">
          <span className="h-2 w-2 rounded-full bg-slate-500 animate-pulse" />
          <span>CANAL DE TELEMETRÍA EN ESPERA DE SEÑAL</span>
        </div>
        <p className="text-slate-500 text-xs font-mono">
          La gráfica de series temporales se trazará automáticamente en cuanto comience la transmisión del Gateway.
        </p>
      </div>
    );
  }

  // Dimensiones del canvas SVG
  const width = 800;
  const height = 300;
  const padding = 45;

  const maxPower = Math.max(...data.map(d => Math.max(d.p_expected || 0, d.p_dc || 0)), 1000);
  const maxIrr = Math.max(...data.map(d => d.g_irradiance || 0), 1000);

  const getX = (index: number) => {
    return padding + (index / (data.length - 1)) * (width - 2 * padding);
  };

  const getYPower = (val: number) => {
    return height - padding - (val / maxPower) * (height - 2 * padding);
  };

  // Construir paths SVG
  const pathRealPower = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYPower(d.p_dc)}`).join(' ');
  const pathExpectedPower = data.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYPower(d.p_expected)}`).join(' ');

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-2">
        <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          {title}
        </h3>
        {/* Leyenda de colores */}
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 bg-emerald-400" />
            <span className="text-slate-300">Potencia Real (W)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 border-t-2 border-dotted border-amber-400" />
            <span className="text-slate-300">Potencia Esperada (W)</span>
          </div>
        </div>
      </div>

      <div className="relative mt-4 overflow-x-auto">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto min-w-[600px]">
          {/* Rejilla de Fondo */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = height - padding - pct * (height - 2 * padding);
            const val = Math.round(pct * maxPower);
            return (
              <g key={idx}>
                <line x1={padding} y1={y} x2={width - padding} y2={y} stroke="#1e293b" strokeDasharray="3 3" />
                <text x={padding - 8} y={y + 4} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="monospace">
                  {val}W
                </text>
              </g>
            );
          })}

          {/* Línea de Potencia Esperada (Dotted Amber) */}
          <path
            d={pathExpectedPower}
            fill="none"
            stroke="#fbbf24"
            strokeWidth="2.5"
            strokeDasharray="5 4"
            opacity="0.85"
          />

          {/* Línea de Potencia Real (Solid Emerald) */}
          <path
            d={pathRealPower}
            fill="none"
            stroke="#10b981"
            strokeWidth="3"
          />

          {/* Puntos y Nodos */}
          {data.map((d, i) => {
            const x = getX(i);
            const yReal = getYPower(d.p_dc);
            const yExp = getYPower(d.p_expected);
            const isAnomaly = d.p_expected > 200 && (d.p_dc / d.p_expected) < 0.6;

            return (
              <g key={i} className="cursor-pointer group">
                {/* Marcador de anomalía si hay pérdida crítica */}
                {isAnomaly && (
                  <circle cx={x} cy={yReal} r="7" fill="#ef4444" opacity="0.4" className="animate-ping" />
                )}
                <circle
                  cx={x}
                  cy={yReal}
                  r={isAnomaly ? "5" : "3.5"}
                  fill={isAnomaly ? "#ef4444" : "#10b981"}
                  stroke="#0f172a"
                  strokeWidth="2"
                />
                {/* Etiquetas de eje X (hora) cada ciertas muestras */}
                {i % Math.ceil(data.length / 8) === 0 && (
                  <text x={x} y={height - 15} fill="#64748b" fontSize="10" textAnchor="middle" fontFamily="monospace">
                    {d.time}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400 font-mono">
        <span>Frecuencia de agregación: 15 min</span>
        <span className="text-amber-400/90">Modelo: Sandia PV + XGBoost Baseline</span>
      </div>
    </div>
  );
};
