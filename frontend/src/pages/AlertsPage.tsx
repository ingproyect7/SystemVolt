import React from 'react';
import { AlertTriangle, ShieldCheck, Download, RefreshCw } from 'lucide-react';
import { AlertTable } from '../components/AlertTable';
import { SystemAlert } from '../types/solar';

interface AlertsPageProps {
  alerts: SystemAlert[];
  onAcknowledge: (alertId: string) => void;
  onRefresh: () => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ alerts, onAcknowledge, onRefresh }) => {
  const criticalCount = alerts.filter(a => a.severity === 'critical' && a.status === 'pending').length;
  const warningCount = alerts.filter(a => a.severity === 'warning' && a.status === 'pending').length;

  return (
    <div className="space-y-6">
      {/* Cabecera del Centro de Notificaciones */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            CENTRO DE GESTIÓN DE ALERTAS & NOTIFICACIONES
          </h2>
          <p className="text-xs text-slate-400">Despacho Multicanal (Dashboard, Telegram Bot, Email SMTP y Webhooks)</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={onRefresh}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono border border-slate-700 transition-all"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Actualizar</span>
          </button>
        </div>
      </div>

      {/* Resumen Superior de Estados */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono text-center">
        <div className="bg-red-950/20 border border-red-500/30 rounded-xl p-4">
          <span className="text-xs text-red-300 block mb-1">Alertas Críticas Pendientes</span>
          <span className="text-2xl font-bold text-red-400">{criticalCount}</span>
        </div>
        <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl p-4">
          <span className="text-xs text-amber-300 block mb-1">Advertencias Moderadas</span>
          <span className="text-2xl font-bold text-amber-400">{warningCount}</span>
        </div>
        <div className="bg-emerald-950/20 border border-emerald-500/30 rounded-xl p-4">
          <span className="text-xs text-emerald-300 block mb-1">Alertas Atendidas / Resueltas</span>
          <span className="text-2xl font-bold text-emerald-400">
            {alerts.filter(a => a.status === 'acknowledged' || a.status === 'resolved').length}
          </span>
        </div>
      </div>

      {/* Tabla Principal de Alertas */}
      <AlertTable alerts={alerts} onAcknowledge={onAcknowledge} />
    </div>
  );
};
