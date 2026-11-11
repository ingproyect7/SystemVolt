/**
 * Cliente de servicios API para STV.
 * Por defecto opera como SISTEMA REAL EN PRODUCCIÓN (valores en 0 si no hay hardware conectado).
 * Soporta inyección por puerta trasera (archivos JSON/CSV o casos de laboratorio).
 */
import { SolarPlant, PlantSummary, TelemetryPoint, SystemAlert, AIDiagnostic } from '../types/solar';

const ENV_API = (import.meta as unknown as { env?: Record<string, string> }).env?.VITE_API_URL;
const API_BASE = ENV_API ? `${ENV_API.replace(/\/$/, '')}/api/v1` : '/api/v1';

// Estado en memoria para telemetría inyectada por puerta trasera en el navegador
let localInjectedTelemetry: TelemetryPoint[] = [];
let localInjectedAlerts: SystemAlert[] = [];
let localInjectedDiagnostic: AIDiagnostic | null = null;

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  const contentType = res.headers.get('content-type') || '';
  // Proteger contra rewrites SPA de Vercel que devuelven index.html (200 OK text/html)
  if (!res.ok || !contentType.includes('application/json')) {
    throw new Error(`API no disponible (${res.status})`);
  }
  return await res.json() as T;
}

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
      return await fetchJson<SolarPlant[]>(`${API_BASE}/plants/`);
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
    // Si hay datos cargados por puerta trasera, priorizarlos hasta que se resetee a cero
    if (localInjectedTelemetry.length > 0) {
      const last = localInjectedTelemetry[localInjectedTelemetry.length - 1];
      return {
        plant_id: plantId,
        name: 'Planta Solar Fotovoltaica (Laboratorio / Simulación)',
        installed_capacity_kw: 1.0,
        current_power_w: last.p_dc,
        current_irradiance_w_m2: last.g_irradiance,
        current_t_panel_c: last.t_panel,
        performance_ratio: last.performance_ratio,
        active_alerts_count: localInjectedAlerts.filter(a => a.status === 'pending').length,
        last_updated: new Date().toISOString()
      };
    }

    try {
      return await fetchJson<PlantSummary>(`${API_BASE}/plants/${plantId}/summary`);
    } catch {
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
    if (localInjectedTelemetry.length > 0) {
      return localInjectedTelemetry.slice(-limit);
    }

    try {
      return await fetchJson<TelemetryPoint[]>(`${API_BASE}/telemetry/history?plant_id=${plantId}&limit=${limit}`);
    } catch {
      // POR DEFECTO: VACÍO (SIN SEÑAL)
      return [];
    }
  },

  async getAlerts(plantId?: string): Promise<SystemAlert[]> {
    if (localInjectedTelemetry.length > 0) {
      return localInjectedAlerts;
    }

    try {
      const url = plantId ? `${API_BASE}/alerts/?plant_id=${plantId}` : `${API_BASE}/alerts/`;
      return await fetchJson<SystemAlert[]>(url);
    } catch {
      // SIN HARDWARE = CERO ALERTAS FALSAS
      return [];
    }
  },

  async getLatestDiagnostic(plantId: string): Promise<AIDiagnostic | null> {
    if (localInjectedTelemetry.length > 0) {
      return localInjectedDiagnostic;
    }

    try {
      return await fetchJson<AIDiagnostic>(`${API_BASE}/ai/latest?plant_id=${plantId}`);
    } catch {
      return null;
    }
  },

  async acknowledgeAlert(alertId: string): Promise<void> {
    if (localInjectedTelemetry.length > 0) {
      localInjectedAlerts = localInjectedAlerts.map(a =>
        a.id === alertId ? { ...a, status: 'acknowledged' } : a
      );
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: 'Reconocido por operador.' })
      });
      const contentType = res.headers.get('content-type') || '';
      if (!res.ok || !contentType.includes('application/json')) {
        throw new Error(`HTTP ${res.status}`);
      }
    } catch {
      localInjectedAlerts = localInjectedAlerts.map(a =>
        a.id === alertId ? { ...a, status: 'acknowledged' } : a
      );
    }
  }
};
