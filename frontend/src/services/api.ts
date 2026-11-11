/**
 * Cliente de servicios API para STV.
 * Por defecto opera como SISTEMA REAL EN PRODUCCIÓN (valores en 0 si no hay hardware conectado).
 * Soporta inyección por puerta trasera (archivos JSON/CSV o casos de laboratorio).
 */
import { SolarPlant, PlantSummary, TelemetryPoint, SystemAlert, AIDiagnostic } from '../types/solar';

const API_BASE = '/api/v1';

// Estado en memoria para telemetría inyectada por puerta trasera en el navegador
let localInjectedTelemetry: TelemetryPoint[] = [];
let localInjectedAlerts: SystemAlert[] = [];
let localInjectedDiagnostic: AIDiagnostic | null = null;

export const apiService = {
  // --- PUERTA TRASERA: MÉTODOS DE INYECCIÓN Y RESET ---
  setInjectedData(points: TelemetryPoint[], alerts: SystemAlert[] = [], diagnostic: AIDiagnostic | null = null) {
    localInjectedTelemetry = [...points];
    localInjectedAlerts = [...alerts];
    localInjectedDiagnostic = diagnostic;
  },

  resetToZero() {
    localInjectedTelemetry = [];
    localInjectedAlerts = [];
    localInjectedDiagnostic = null;
  },

  hasInjectedData(): boolean {
    return localInjectedTelemetry.length > 0;
  },

  getInjectedDiagnostic(): AIDiagnostic | null {
    return localInjectedDiagnostic;
  },

  // --- CONSULTAS PRINCIPALES ---
  async getPlants(): Promise<SolarPlant[]> {
    try {
      const res = await fetch(`${API_BASE}/plants/`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      return [
        {
          id: 'plant-01',
          name: 'Planta Solar Fotovoltaica (Producción)',
          code: 'STV-PLANT-01',
          latitude: 6.2442,
          longitude: -75.5812,
          installed_capacity_kw: 1.0,
          tilt_angle: 10.0,
          azimuth_angle: 180.0,
          temp_coefficient_power: -0.0038,
          inverter_nominal_efficiency: 0.975
        }
      ];
    }
  },

  async getPlantSummary(plantId: string): Promise<PlantSummary> {
    try {
      const res = await fetch(`${API_BASE}/plants/${plantId}/summary`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      return data;
    } catch {
      // Si hay datos cargados por puerta trasera, calcular métricas a partir de la última muestra
      if (localInjectedTelemetry.length > 0) {
        const last = localInjectedTelemetry[localInjectedTelemetry.length - 1];
        return {
          plant_id: plantId,
          name: 'Planta Solar Fotovoltaica (Producción)',
          installed_capacity_kw: 1.0,
          current_power_w: last.p_dc,
          current_irradiance_w_m2: last.g_irradiance,
          current_t_panel_c: last.t_panel,
          performance_ratio: last.performance_ratio,
          active_alerts_count: localInjectedAlerts.filter(a => a.status === 'pending').length,
          last_updated: new Date().toISOString()
        };
      }

      // SISTEMA REAL EN PRODUCCIÓN SIN HARDWARE: ESTRICTAMENTE 0
      return {
        plant_id: plantId,
        name: 'Planta Solar Fotovoltaica (Producción)',
        installed_capacity_kw: 1.0,
        current_power_w: 0.0,
        current_irradiance_w_m2: 0.0,
        current_t_panel_c: 0.0,
        performance_ratio: null,
        active_alerts_count: 0,
        last_updated: null
      };
    }
  },

  async getTelemetryHistory(plantId: string, limit: number = 24): Promise<TelemetryPoint[]> {
    try {
      const res = await fetch(`${API_BASE}/telemetry/history?plant_id=${plantId}&limit=${limit}`);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      // Si se inyectaron datos por la puerta trasera, retornar esos datos
      if (localInjectedTelemetry.length > 0) {
        return localInjectedTelemetry.slice(-limit);
      }
      // POR DEFECTO: VACÍO (SIN SEÑAL)
      return [];
    }
  },

  async getAlerts(plantId?: string): Promise<SystemAlert[]> {
    try {
      const url = plantId ? `${API_BASE}/alerts/?plant_id=${plantId}` : `${API_BASE}/alerts/`;
      const res = await fetch(url);
      if (!res.ok) throw new Error();
      return await res.json();
    } catch {
      if (localInjectedAlerts.length > 0) {
        return localInjectedAlerts;
      }
      // SIN HARDWARE = CERO ALERTAS FALSAS
      return [];
    }
  },

  async acknowledgeAlert(alertId: string): Promise<void> {
    try {
      await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: 'Reconocido por operador.' })
      });
    } catch {
      // Actualizar localmente si está en modo puerta trasera
      localInjectedAlerts = localInjectedAlerts.map(a => 
        a.id === alertId ? { ...a, status: 'acknowledged' } : a
      );
    }
  }
};
