import React, { useState } from 'react';
import { AlertTriangle, Info, AlertOctagon, CheckCircle2 } from 'lucide-react';
import { SystemAlert } from '../types/solar';

interface AlertTableProps {
  alerts: SystemAlert[];
  onAcknowledge: (alertId: string) => void;
}

export const AlertTable: React.FC<AlertTableProps> = ({ alerts, onAcknowledge }) => {
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');

  const filteredAlerts = alerts.filter(a => {
    if (filter === 'all') return true;
    return a.severity === filter;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-red-500/15 text-red-400 border border-red-500/30">
            <AlertOctagon className="h-3.5 w-3.5" /> CRÍTICO
          </span>
        );
      case 'warning':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="h-3.5 w-3.5" /> ADVERTENCIA
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30">
            <Info className="h-3.5 w-3.5" /> INFORMATIVO
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Barra de Filtros */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-400" />
          Bandeja de Eventos y Alarmas ({filteredAlerts.length})
        </h3>
        <div className="flex space-x-1.5 text-xs font-mono">
          {(['all', 'critical', 'warning', 'info'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1.5 rounded-md uppercase transition-all ${
                filter === tab
                  ? 'bg-slate-700 text-white font-bold'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950 text-slate-400 uppercase font-mono tracking-wider border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Severidad</th>
              <th className="py-3 px-4">Evento / Título</th>
              <th className="py-3 px-4 hidden md:table-cell">Evidencia Eléctrica</th>
              <th className="py-3 px-4">Fecha / Hora</th>
              <th className="py-3 px-4">Estado</th>
              <th className="py-3 px-4 text-right">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {filteredAlerts.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 font-mono">
                  No hay alertas registradas con este criterio de filtro.
                </td>
              </tr>
            ) : (
              filteredAlerts.map(alert => (
                <tr key={alert.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    {getSeverityBadge(alert.severity)}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="font-semibold text-white block">{alert.title}</span>
                    <span className="text-slate-400 text-xs line-clamp-1">{alert.description}</span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-xs hidden md:table-cell text-slate-300">
                    {alert.evidence_metrics.p_actual !== undefined && (
                      <div>P_real: <span className="text-emerald-400">{alert.evidence_metrics.p_actual}W</span> / P_esp: <span className="text-amber-400">{alert.evidence_metrics.p_expected}W</span></div>
                    )}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-400 whitespace-nowrap">
                    {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-medium ${
                      alert.status === 'pending'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {alert.status.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    {alert.status === 'pending' ? (
                      <button
                        onClick={() => onAcknowledge(alert.id)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-all"
                      >
                        Reconocer
                      </button>
                    ) : (
                      <span className="text-slate-500 flex items-center justify-end gap-1 text-xs">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Atendida
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
