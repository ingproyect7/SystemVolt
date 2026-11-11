/**
 * Definiciones de tipos TypeScript para la plataforma industrial STV.
 * Coincidentes con los esquemas Pydantic del backend.
 */

export interface SolarPlant {
  id: string;
  name: string;
  code: string;
  latitude: number;
  longitude: number;
  installed_capacity_kw: number;
  tilt_angle: number;
  azimuth_angle: number;
  temp_coefficient_power: number;
  inverter_nominal_efficiency: number;
}

export interface PlantSummary {
  plant_id: string;
  name: string;
  installed_capacity_kw: number;
  current_power_w: number;
  current_irradiance_w_m2: number;
  current_t_panel_c: number;
  performance_ratio: number | null;
  active_alerts_count: number;
  last_updated: string | null;
}

export interface TelemetryPoint {
  time: string;
  v_dc: number;
  i_dc: number;
  p_dc: number;
  g_irradiance: number;
  t_panel: number;
  t_ambient: number;
  p_expected: number;
  performance_ratio: number | null;
}

export type AlertSeverity = 'info' | 'warning' | 'critical';
export type AlertStatus = 'pending' | 'acknowledged' | 'in_progress' | 'resolved' | 'dismissed';

export interface SystemAlert {
  id: string;
  plant_id: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  recommended_action: string;
  evidence_metrics: {
    p_actual?: number;
    p_expected?: number;
    loss_percentage?: number;
    g_irradiance?: number;
    t_panel?: number;
    [key: string]: any;
  };
  status: AlertStatus;
  created_at: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
}

export interface AIDiagnostic {
  id: string;
  plant_id: string;
  timestamp: string;
  is_anomaly: boolean;
  anomaly_score: number;
  fault_category: 'NORMAL' | 'SHADING' | 'SOILING' | 'STRING_DISCONNECTED' | 'INVERTER_FAULT' | 'HOTSPOT' | 'SENSOR_FAULT';
  confidence_level: number;
  p_expected: number;
  p_actual: number;
  delta_power: number;
  loss_percentage: number;
  root_cause_explanation: string;
  recommended_action: string;
  features_importance: Record<string, number>;
}
