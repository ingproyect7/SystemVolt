import React from 'react';
import { Activity, Thermometer, CloudRain, ShieldCheck } from 'lucide-react';
import { TelemetryChart } from '../components/TelemetryChart';
import { PlantSummary, TelemetryPoint } from '../types/solar';

interface MonitoringProps {
  summary: PlantSummary;
  telemetry: TelemetryPoint[];
}

export const Monitoring: React.FC<MonitoringProps> = ({ summary, telemetry }) => {
  const latest = telemetry.length > 0 ? telemetry[telemetry.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Cabecera de Instrumentación */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Activity className="h-5 w-5 text-amber-500" />
            INSTRUMENTACIÓN Y TELEMETRÍA EN TIEMPO REAL
          </h2>
          <p className="text-xs text-slate-400">Planta Solar Piloto Granja Experimental • Medición Aislada</p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-slate-300">
          <span className={`h-2 w-2 rounded-full ${latest ? 'bg-emerald-400 animate-ping' : 'bg-slate-600'}`} />
          <span>{latest ? 'Frecuencia de muestreo: 1 Hz | Envío: 10 s' : 'Sin señal — esperando gateway'}</span>
        </div>
      </div>

      {/* Cuadrante de Instrumentación Eléctrica DC */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 font-mono">
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 text-center">
          <span className="text-xs text-slate-400 uppercase block mb-1">Voltaje DC String</span>
          <span className="text-2xl font-bold text-amber-400">{latest ? latest.v_dc.toFixed(1) : '0.0'}</span>
          <span className="text-xs text-slate-400 ml-1">V</span>
          <span className="text-[10px] text-slate-500 block mt-1">Aislador TI AMC1301</span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 text-center">
          <span className="text-xs text-slate-400 uppercase block mb-1">Corriente DC String</span>
          <span className="text-2xl font-bold text-emerald-400">{latest ? latest.i_dc.toFixed(2) : '0.00'}</span>
          <span className="text-xs text-slate-400 ml-1">A</span>
          <span className="text-[10px] text-slate-500 block mt-1">Efecto Hall ACS758</span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 text-center">
          <span className="text-xs text-slate-400 uppercase block mb-1">Irradiancia en Plano</span>
          <span className="text-2xl font-bold text-white">{latest ? latest.g_irradiance.toFixed(0) : '0'}</span>
          <span className="text-xs text-slate-400 ml-1">W/m²</span>
          <span className="text-[10px] text-slate-500 block mt-1">Piranómetro Modbus RS485</span>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 text-center">
          <span className="text-xs text-slate-400 uppercase block mb-1">Temperatura Célula</span>
          <span className="text-2xl font-bold text-amber-400">{latest ? latest.t_panel.toFixed(1) : '0.0'}</span>
          <span className="text-xs text-slate-400 ml-1">°C</span>
          <span className="text-[10px] text-slate-500 block mt-1">Sonda PT100 Backsheet</span>
        </div>
      </div>

      {/* Gráfica de Serie Temporal */}
      <TelemetryChart data={telemetry} title="Respuesta Dinámica: Curva I-V y Potencia en Generador" />

      {/* Detalles Secundarios de Microclima y Red */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs font-mono">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Thermometer className="h-5 w-5 text-slate-400" />
            <div>
              <span className="text-slate-400 block">Temperatura Ambiente</span>
              {/* FIX: mostrar 0 cuando no hay telemetría, no hardcodear 24 */}
              <span className="text-white text-base font-bold">
                {latest ? `${latest.t_ambient}°C` : '0.0°C'}
              </span>
            </div>
          </div>
          <span className="text-[10px] text-slate-500">SHT31 I2C</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <CloudRain className="h-5 w-5 text-slate-400" />
            <div>
              <span className="text-slate-400 block">Humedad Relativa</span>
              <span className="text-white text-base font-bold">
                {latest && latest.rh_ambient !== undefined ? `${latest.rh_ambient}%` : '--'}
              </span>
            </div>
          </div>
          <span className="text-[10px] text-slate-500">Garita Ventilada</span>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <ShieldCheck className="h-5 w-5 text-emerald-400" />
            <div>
              <span className="text-slate-400 block">Aislamiento Dieléctrico</span>
              <span className="text-emerald-400 text-base font-bold">&gt; 5000 V RMS</span>
            </div>
          </div>
          <span className="text-[10px] text-emerald-400">Verificado IPC</span>
        </div>
      </div>
    </div>
  );
};
