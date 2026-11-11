import React, { useState } from 'react';
import { Upload, X, Check, AlertCircle, RefreshCw, FileText, Sparkles, Terminal } from 'lucide-react';
import { apiService } from '../services/api';
import { TelemetryPoint, SystemAlert, AIDiagnostic } from '../types/solar';

interface BackdoorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDataChanged: () => void;
}

export const BackdoorModal: React.FC<BackdoorModalProps> = ({ isOpen, onClose, onDataChanged }) => {
  const [feedback, setFeedback] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  // --- OPCIÓN 1: CARGAR CASO OFICIAL DEL REQUERIMIENTO (950 W/m², 48°C, 310W) ---
  const handleLoadOfficialCase = () => {
    const points: TelemetryPoint[] = [];
    const now = new Date();

    // Crear una curva previa y el punto crítico a mediodía
    for (let i = 12; i >= 0; i--) {
      const t = new Date(now.getTime() - i * 15 * 60 * 1000);
      const isCritical = i === 0;

      const g = isCritical ? 950 : 880 - i * 20;
      const tPanel = isCritical ? 48.0 : 42.0 - i * 0.5;
      const pExpected = isCritical ? 800 : Math.round(g * 0.88);
      const pActual = isCritical ? 310 : Math.round(pExpected * 0.97);
      const v = isCritical ? 170.0 : 342.0;
      const curr = isCritical ? 1.82 : 2.50;

      points.push({
        time: t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        v_dc: v,
        i_dc: curr,
        p_dc: pActual,
        g_irradiance: g,
        t_panel: tPanel,
        t_ambient: 26.0,
        p_expected: pExpected,
        performance_ratio: +(pActual / pExpected).toFixed(3)
      });
    }

    const alert: SystemAlert = {
      id: 'alert-mandatory-01',
      plant_id: 'plant-01',
      severity: 'critical',
      title: 'Pérdida Crítica de Generación (61.25% Pérdida)',
      description: 'Bajo irradiancia de 950 W/m² y 48.0°C en panel, la potencia real registrada es de 310 W frente a 800 W esperados (-61.25%). Descenso severo de corriente con tensión atenuada por diodos de bypass.',
      recommended_action: 'Inspeccionar sombreado físico severo sobre hilera 01 o falla en conectores MC4/diodos de bypass.',
      evidence_metrics: {
        p_actual: 310,
        p_expected: 800,
        loss_percentage: 61.25,
        g_irradiance: 950,
        t_panel: 48.0
      },
      status: 'pending',
      created_at: new Date().toISOString()
    };

    const diagnostic: AIDiagnostic = {
      id: 'diag-01',
      plant_id: 'plant-01',
      timestamp: new Date().toISOString(),
      is_anomaly: true,
      anomaly_score: -0.42,
      fault_category: 'SHADING',
      confidence_level: 0.933,
      p_expected: 800,
      p_actual: 310,
      delta_power: 490,
      loss_percentage: 61.25,
      root_cause_explanation: 'Se detecta generación significativamente inferior a la esperada (-61.25%). Caída severa en corriente DC (1.82 A) mientras la tensión permanece en 170.0 V, compatible con sombra sobre sub-módulos y activación de diodos de bypass.',
      recommended_action: 'Inspeccionar visualmente sombras proyectadas de árboles, postes o vegetación sobre el arreglo. Comprobar diodos de bypass en la caja de conexiones.',
      features_importance: {
        'Déficit de Corriente DC (I)': 0.52,
        'Irradiancia Elevada (950 W/m²)': 0.26,
        'Tensión Operativa Nominal (V)': 0.15,
        'Temperatura Celular (48°C)': 0.07
      }
    };

    apiService.setInjectedData(points, [alert], diagnostic);
    setFeedback('¡Caso Oficial de Prueba inyectado con éxito! (G=950 W/m², P_real=310W, Pérdida=61.25%)');
    setErrorMsg(null);
    onDataChanged();
  };

  // --- OPCIÓN 2: CARGAR ARCHIVO EXTERNO (JSON O CSV) ---
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        let points: TelemetryPoint[] = [];

        if (file.name.endsWith('.json')) {
          const raw = JSON.parse(text);
          const list = Array.isArray(raw) ? raw : [raw];
          points = list.map((item, idx) => ({
            time: item.time || item.timestamp || `T-${idx}`,
            v_dc: Number(item.v_dc || item.v || 340),
            i_dc: Number(item.i_dc || item.i || 2.5),
            p_dc: Number(item.p_actual_dc || item.p_dc || item.p || 850),
            g_irradiance: Number(item.irradiance_w_m2 || item.g_irradiance || item.g || 800),
            t_panel: Number(item.panel_temp_c || item.t_panel || item.t || 42),
            t_ambient: Number(item.ambient_temp_c || item.t_ambient || 25),
            p_expected: Number(item.p_expected_theor || item.p_expected || 820),
            performance_ratio: item.performance_ratio || null
          }));
        } else if (file.name.endsWith('.csv')) {
          const lines = text.split('\n').filter(l => l.trim().length > 0);
          const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
          
          for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(',').map(c => c.trim());
            const row: any = {};
            headers.forEach((h, idx) => { row[h] = cols[idx]; });
            
            const pReal = Number(row.p_dc || row.p_actual_dc || (Number(row.v_dc) * Number(row.i_dc)) || 0);
            const pExp = Number(row.p_expected || 800);

            points.push({
              time: row.time || row.timestamp || `Muest-${i}`,
              v_dc: Number(row.v_dc || 0),
              i_dc: Number(row.i_dc || 0),
              p_dc: pReal,
              g_irradiance: Number(row.g_irradiance || row.irradiance || 0),
              t_panel: Number(row.t_panel || row.panel_temp || 25),
              t_ambient: Number(row.t_ambient || 24),
              p_expected: pExp,
              performance_ratio: pExp > 0 ? +(pReal / pExp).toFixed(3) : null
            });
          }
        } else {
          throw new Error('Formato no soportado. Debe ser .json o .csv');
        }

        if (points.length === 0) {
          throw new Error('El archivo no contiene filas o datos interpretables.');
        }

        apiService.setInjectedData(points);
        setFeedback(`¡Archivo '${file.name}' cargado con éxito! Total puntos inyectados: ${points.length}`);
        setErrorMsg(null);
        onDataChanged();
      } catch (err: any) {
        setErrorMsg(`Error procesando archivo: ${err.message}`);
        setFeedback(null);
      }
    };
    reader.readAsText(file);
  };

  // --- OPCIÓN 3: RESTABLECER A CERO (MODO PRODUCCIÓN LIMPIO) ---
  const handleResetToZero = () => {
    apiService.resetToZero();
    setFeedback('Sistema restablecido a CERO (Modo Producción Limpio sin sensores conectados).');
    setErrorMsg(null);
    onDataChanged();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-xl w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-all"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Cabecera */}
        <div className="flex items-center space-x-3 pb-4 border-b border-slate-800">
          <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-xl border border-amber-500/30">
            <Terminal className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              PUERTA TRASERA: LABORATORIO DE CALIBRACIÓN & INYECCIÓN
            </h3>
            <p className="text-xs text-slate-400">Permite simular datos reales de campo cuando no hay hardware físico conectado</p>
          </div>
        </div>

        {/* Notificaciones */}
        {feedback && (
          <div className="my-4 p-3 bg-emerald-950/30 border border-emerald-500/40 rounded-lg text-emerald-300 text-xs flex items-center gap-2">
            <Check className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>{feedback}</span>
          </div>
        )}
        {errorMsg && (
          <div className="my-4 p-3 bg-red-950/30 border border-red-500/40 rounded-lg text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Opciones de Inyección */}
        <div className="space-y-4 my-5">
          {/* Opción A: Caso Oficial del Requerimiento */}
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wide flex items-center gap-1.5">
                <Sparkles className="h-4 w-4" /> Opción 1: Caso de Prueba Oficial (Requerimiento)
              </span>
            </div>
            <p className="text-xs text-slate-300 mb-3">
              Inyecta las condiciones de auditoría: <strong>Irradiancia: 950 W/m²</strong>, <strong>Temp. Panel: 48°C</strong>, <strong>Potencia Esperada: 800 W</strong> y <strong>Potencia Real: 310 W</strong> (Pérdida: 61.25%).
            </p>
            <button
              onClick={handleLoadOfficialCase}
              className="w-full py-2 px-3 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-xs font-semibold font-mono transition-all"
            >
              Cargar Caso Obligatorio (950 W/m² - 310 W)
            </button>
          </div>

          {/* Opción B: Subir Archivo JSON / CSV */}
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wide flex items-center gap-1.5">
                <FileText className="h-4 w-4 text-emerald-400" /> Opción 2: Cargar Archivo de Datos (.JSON / .CSV)
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Sube registros exportados de simulación o mediciones reales con columnas (v_dc, i_dc, irradiance, t_panel).
            </p>
            <label className="flex items-center justify-center space-x-2 w-full py-2.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium cursor-pointer transition-all">
              <Upload className="h-4 w-4 text-slate-400" />
              <span>Seleccionar Archivo JSON o CSV</span>
              <input
                type="file"
                accept=".json,.csv"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>

          {/* Opción C: Modo Producción Limpio (En CERO) */}
          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl flex items-center justify-between gap-3">
            <div>
              <span className="text-xs font-bold text-slate-200 uppercase block">Modo Producción Limpio</span>
              <span className="text-xs text-slate-400 block">Restablece la plataforma a 0 (esperando hardware físico real).</span>
            </div>
            <button
              onClick={handleResetToZero}
              className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono border border-slate-700 flex items-center gap-1.5 whitespace-nowrap"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Resetear a CERO
            </button>
          </div>
        </div>

        {/* Pie */}
        <div className="pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium transition-all"
          >
            Cerrar Laboratorio
          </button>
        </div>
      </div>
    </div>
  );
};
