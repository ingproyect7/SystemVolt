import React from 'react';
import { Zap, Sun, Thermometer, AlertTriangle, Gauge, BatteryCharging, Radio, Terminal } from 'lucide-react';
import { KPICard } from '../components/KPICard';
import { TelemetryChart } from '../components/TelemetryChart';
import { AIDiagnosticCard } from '../components/AIDiagnosticCard';
import { PlantSummary, TelemetryPoint, AIDiagnostic } from '../types/solar';

interface DashboardProps {
  summary: PlantSummary;
  telemetry: TelemetryPoint[];
  diagnostic: AIDiagnostic | null;
  onNavigateToAlerts: () => void;
  onOpenBackdoor: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  summary,
  telemetry,
  diagnostic,
  onNavigateToAlerts,
  onOpenBackdoor
}) => {
  const hasTelemetry = telemetry.length > 0;
  const latest = hasTelemetry ? telemetry[telemetry.length - 1] : null;

  const isAnomaly =
    (diagnostic?.is_anomaly) ||
    (summary.performance_ratio !== null && summary.performance_ratio < 0.6) ||
    summary.active_alerts_count > 0;

  const expectedPower = diagnostic?.p_expected ?? latest?.p_expected ?? 0;
  const actualPower = diagnostic?.p_actual ?? summary.current_power_w;
  const lossPercent = diagnostic
    ? diagnostic.loss_percentage.toFixed(2)
    : (summary.performance_ratio !== null ? ((1 - summary.performance_ratio) * 100).toFixed(1) : '0.0');

  return (
    <div className="space-y-6">
      {/* Estado 1: Banner Crítico cuando hay anomalía inyectada/detectada */}
      {isAnomaly && (
        <div className="bg-red-950/40 border border-red-500/50 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-red-200 shadow-xl">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-500/20 rounded-lg text-red-400">
              <AlertTriangle className="h-5 w-5 animate-bounce" />
            </div>
            <div>
              <span className="font-bold text-sm block">ALERTA CRÍTICA: PÉRDIDA SEVERA DE GENERACIÓN ENERGÉTICA</span>
              <span className="text-xs text-red-300">
                Potencia medida: {actualPower.toFixed(0)} W frente a {expectedPower.toFixed(0)} W esperados (-{lossPercent}% de rendimiento).
              </span>
            </div>
          </div>
          <button
            onClick={onNavigateToAlerts}
            className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-500 text-white text-xs font-semibold font-mono transition-all whitespace-nowrap shadow-md"
          >
            VER DIAGNÓSTICO IA →
          </button>
        </div>
      )}

      {/* Estado 2: Banner de Estado Limpio de Producción cuando NO hay hardware conectado */}
      {!hasTelemetry && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-slate-300">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-slate-800 text-slate-400 rounded-lg">
              <Radio className="h-5 w-5 text-slate-400 animate-pulse" />
            </div>
            <div>
              <span className="font-bold text-sm text-white block">SISTEMA LISTO EN ESPERA DE TELEMETRÍA FOTOVOLTAICA</span>
              <span className="text-xs text-slate-400 block mt-0.5">
                La plataforma está configurada para recibir mediciones en tiempo real del Gateway ESP32 (MQTTS :8883).
              </span>
            </div>
          </div>
          <button
            onClick={onOpenBackdoor}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-lg bg-amber-500/15 hover:bg-amber-500/25 text-amber-300 border border-amber-500/30 text-xs font-mono font-semibold transition-all whitespace-nowrap"
          >
            <Terminal className="h-4 w-4" />
            <span>ABRIR PUERTA TRASERA (INYECCIÓN DE DATOS)</span>
          </button>
        </div>
      )}

      {/* Grid de KPIs Industriales (En 0 por defecto) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Potencia Generada Actual"
          value={Number.isInteger(summary.current_power_w) ? summary.current_power_w : summary.current_power_w.toFixed(1)}
          unit="W"
          icon={Zap}
          subtext="Capacidad instalada: 1.0 kWp"
          status={isAnomaly ? 'critical' : 'normal'}
        />
        <KPICard
          title="Irradiancia Incidente (G)"
          value={Number.isInteger(summary.current_irradiance_w_m2) ? summary.current_irradiance_w_m2 : summary.current_irradiance_w_m2.toFixed(0)}
          unit="W/m²"
          icon={Sun}
          subtext={hasTelemetry ? "Medición en plano" : "Sensor en espera"}
          trend={hasTelemetry ? "Activo" : undefined}
        />
        <KPICard
          title="Performance Ratio (PR)"
          value={summary.performance_ratio !== null ? `${(summary.performance_ratio * 100).toFixed(1)}%` : '--'}
          icon={Gauge}
          subtext="Esperado nominal: > 80.0%"
          status={summary.performance_ratio !== null && summary.performance_ratio < 0.6 ? 'critical' : 'normal'}
        />
        <KPICard
          title="Temperatura de Módulo"
          value={Number.isInteger(summary.current_t_panel_c) ? summary.current_t_panel_c : summary.current_t_panel_c.toFixed(1)}
          unit="°C"
          icon={Thermometer}
          subtext={hasTelemetry ? "Sonda PT100 activa" : "Sin lectura térmica"}
          status={summary.current_t_panel_c > 65 ? 'warning' : 'normal'}
        />
      </div>

      {/* Gráfica de Series Temporales */}
      <TelemetryChart
        data={telemetry}
        title={hasTelemetry ? "Curva Temporal: Potencia Real vs. Potencia Esperada" : "Monitoreo Temporal: En espera de telemetría de campo"}
      />

      {/* Resumen de Diagnóstico */}
      {hasTelemetry ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <AIDiagnosticCard
              isAnomaly={diagnostic ? diagnostic.is_anomaly : isAnomaly}
              faultCategory={diagnostic ? diagnostic.fault_category : (isAnomaly ? "DESCONEXIÓN / SOMBRA CRÍTICA" : "OPERACIÓN NORMAL")}
              confidence={diagnostic ? diagnostic.confidence_level : (isAnomaly ? 0.933 : 0.98)}
              expectedPower={expectedPower}
              actualPower={actualPower}
              lossPercentage={parseFloat(lossPercent)}
              explanation={
                diagnostic?.root_cause_explanation ??
                (isAnomaly
                  ? `Se registra caída significativa de generación (${actualPower} W vs ${expectedPower} W esperados). Compatible con sombreado parcial o apertura de string.`
                  : "La planta fotovoltaica opera con normalidad siguiendo la curva teórica de máxima potencia de Sandia.")
              }
              recommendation={
                diagnostic?.recommended_action ??
                (isAnomaly
                  ? "Inspeccionar físicamente la hilera de paneles en busca de sombras proyectadas o falla en el seccionador del string."
                  : "No se requiere mantenimiento. Mantener ciclo regular de supervisión.")
              }
              shapFeatures={diagnostic?.features_importance ?? {
                "Déficit Corriente DC": 0.50,
                "Irradiancia Incidente": 0.28,
                "Tensión Operativa": 0.14,
                "Gradiente Térmico": 0.08
              }}
            />
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col justify-between">
            <div>
              <h4 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2 mb-4">
                <BatteryCharging className="h-4 w-4 text-amber-500" />
                Estado Ciberfísico del Gateway
              </h4>
              <div className="space-y-3 text-xs font-mono">
                <div className="flex justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-400">Microcontrolador:</span>
                  <span className="text-emerald-400 font-bold">ESP32-S3 (Dual-Core)</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-400">Canal Aislado Tensión:</span>
                  <span className="text-slate-200">TI AMC1301 (5 kV RMS)</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-400">Canal Aislado Corriente:</span>
                  <span className="text-slate-200">Allegro ACS758 Hall</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-400">Buffer Store &amp; Forward:</span>
                  <span className="text-emerald-400">Activo (0 pte)</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80">
                  <span className="text-slate-400">Cifrado de Enlace:</span>
                  <span className="text-slate-200">TLS 1.3 / MQTTS</span>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-800/80 text-[11px] text-slate-500 font-mono text-center">
              Estado: Transmisión en curso
            </div>
          </div>
        </div>
      ) : (
        <div className="p-8 rounded-xl bg-slate-900/60 border border-slate-800 text-center font-mono text-slate-400 text-xs">
          <Terminal className="h-6 w-6 text-amber-500 mx-auto mb-2 opacity-80" />
          <span>MODO PRODUCCIÓN LIMPIO: Todos los indicadores eléctricos permanecen en 0 hasta recibir paquetes de campo.</span>
          <span className="block text-slate-500 mt-1">Utilice la opción &quot;Puerta Trasera&quot; en la barra superior para cargar un dataset de prueba o simular el caso de auditoría.</span>
        </div>
      )}
    </div>
  );
};
