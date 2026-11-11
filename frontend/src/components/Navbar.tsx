import React from 'react';
import { Sun, Activity, AlertTriangle, Cpu, ShieldCheck, Terminal, Radio } from 'lucide-react';

interface NavbarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
  activeAlertsCount: number;
  onOpenBackdoor: () => void;
  hasActiveTelemetry: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  activeAlertsCount,
  onOpenBackdoor,
  hasActiveTelemetry
}) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard Principal', icon: Sun },
    { id: 'monitoring', label: 'Monitoreo en Tiempo Real', icon: Activity },
    { id: 'ai', label: 'Diagnóstico IA', icon: Cpu },
    { id: 'alerts', label: 'Alertas del Sistema', icon: AlertTriangle, badge: activeAlertsCount },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo y Nombre de Producto */}
          <div className="flex items-center space-x-3">
            <div className="bg-amber-500/10 p-2 rounded-lg border border-amber-500/30">
              <Sun className={`h-6 w-6 text-amber-500 ${hasActiveTelemetry ? 'animate-pulse' : ''}`} />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
                STV <span className="text-xs bg-amber-500/20 text-amber-400 font-mono px-2 py-0.5 rounded border border-amber-500/30">SYSTEMVOLT</span>
              </span>
              <p className="text-xs text-slate-400">Supervisión Predictiva Fotovoltaica Industrial</p>
            </div>
          </div>

          {/* Navegación por Pestañas */}
          <nav className="flex space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = currentTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden md:inline">{tab.label}</span>
                  {tab.badge && tab.badge > 0 ? (
                    <span className="ml-1.5 px-1.5 py-0.5 text-xs font-mono font-bold bg-red-500 text-white rounded-full">
                      {tab.badge}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </nav>

          {/* Estado de Conectividad Industrial & Puerta Trasera */}
          <div className="flex items-center space-x-2 text-xs">
            {/* Botón Discreto de Puerta Trasera (Laboratorio de Calibración / Inyección) */}
            <button
              onClick={onOpenBackdoor}
              title="Abrir Laboratorio de Calibración / Puerta Trasera para inyectar datos de prueba"
              className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-mono transition-all text-xs"
            >
              <Terminal className="h-3.5 w-3.5 text-amber-400" />
              <span className="hidden sm:inline">PUERTA TRASERA</span>
            </button>

            {/* Píldora de Estado */}
            <div className={`hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-full border ${
              hasActiveTelemetry
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-slate-800/60 text-slate-400 border-slate-700/50'
            }`}>
              <Radio className={`h-3 w-3 ${hasActiveTelemetry ? 'text-emerald-400 animate-pulse' : 'text-slate-500'}`} />
              <span className="font-mono text-[11px]">
                {hasActiveTelemetry ? 'TELEMETRÍA EN VIVO' : 'SIN DISPOSITIVO (EN ESPERA)'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
