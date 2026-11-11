"""
SIMULADOR DINÁMICO DE ESCENARIOS CLIMÁTICOS Y ENERGÍA FOTOVOLTAICA (FASE 8)
==========================================================================
Somete el sistema STV a un ciclo diurno completo con 5 escenarios reales:
1. Cielo despejado nominal (Clear-Sky).
2. Paso de nubes aisladas de corta duración (transitorio rápido).
3. Sombreado parcial severo persistente (Caso obligatorio).
4. Acumulación progresiva de suciedad (Soiling).
5. Desconexión intempestiva de cadena (String abierto).

Calcula la energía generada vs esperada (kWh) y cuantifica la pérdida financiera.
"""
import math
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.pv_physics_simulator import PhotovoltaicPhysicsEngine
from ai_engine.pipelines.inference_engine import PVInferenceEngine


class DynamicDaySimulator:
    def __init__(
        self,
        nominal_capacity_kw: float = 1.0,
        energy_tariff_usd_kwh: float = 0.18, # Tarifa eléctrica promedio USD/kWh
        hysteresis_cycles_threshold: int = 3 # Número mínimo de ciclos persistentes para alertar
    ):
        self.capacity_w = nominal_capacity_kw * 1000.0
        self.tariff = energy_tariff_usd_kwh
        self.hysteresis_threshold = hysteresis_cycles_threshold
        self.physics = PhotovoltaicPhysicsEngine(p_stc_watts=self.capacity_w)
        self.ai = PVInferenceEngine()

    def simulate_24h_cycle(self) -> Dict:
        """
        Ejecuta la simulación de 49 muestras diurnas (06:00 a 18:00 en intervalos de 15 min = 0.25 h).
        """
        base_date = datetime(2026, 11, 11, 6, 0, 0, tzinfo=timezone.utc)
        results = []
        
        # Acumuladores de energía (kWh)
        energy_actual_kwh = 0.0
        energy_expected_kwh = 0.0
        
        # Contador de histéresis para persistencia de anomalías
        consecutive_anomaly_cycles = 0
        alerts_fired = []
        false_alarms_blocked = 0

        for step in range(49):
            current_time = base_date + timedelta(minutes=step * 15)
            hour = current_time.hour + current_time.minute / 60.0
            dt_hours = 0.25 # 15 minutos en horas
            
            # 1. Curva Base de Cielo Despejado (Haurwitz Clear-Sky)
            solar_sin = math.sin((hour - 6.0) / 12.0 * math.pi)
            g_clear = max(0.0, 960.0 * (solar_sin ** 1.15))
            t_amb = 20.0 + 8.0 * solar_sin
            t_cell = self.physics.calculate_cell_temperature(g_clear, t_amb)
            
            v_nom, i_nom, p_nom = self.physics.calculate_iv_operating_point(g_clear, t_cell)
            p_expected = self.physics.calculate_theoretical_power(g_clear, t_cell)

            v_sim = v_nom
            i_sim = i_nom
            p_sim = p_nom
            g_sim = g_clear
            t_sim = t_cell
            scenario_name = "1. CIELO DESPEJADO"

            # 2. Inyección de Escenarios según horario
            # Escenario 2: Nube rápida transitoria (09:45 a 10:00 - Solo 1 o 2 ciclos)
            if 9.75 <= hour <= 10.0:
                scenario_name = "2. NUBE RÁPIDA TRANSITORIA"
                g_sim = round(g_clear * 0.40, 1) # Irradiancia cae por la sombra de la nube
                t_sim = round(t_cell - 3.0, 1)
                v_sim, i_sim, p_sim = self.physics.calculate_iv_operating_point(g_sim, t_sim)
                p_expected = self.physics.calculate_theoretical_power(g_sim, t_sim)

            # Escenario 3: Sombreado Parcial Severo Persistente (Caso Obligatorio: 11:30 a 13:00)
            elif 11.5 <= hour <= 13.0:
                scenario_name = "3. SOMBREADO CRÍTICO PERSISTENTE"
                g_sim = 950.0
                t_sim = 48.0
                v_sim = 170.0
                i_sim = 1.8235
                p_sim = 310.0
                p_expected = self.physics.calculate_theoretical_power(g_sim, t_sim)

            # Escenario 4: Suciedad Acumulada (Soiling: 13:30 a 15:30)
            elif 13.5 <= hour <= 15.5:
                scenario_name = "4. SUCIEDAD ACUMULADA (SOILING)"
                i_sim = round(i_nom * 0.78, 2) # Pérdida del 22% en corriente
                v_sim = v_nom
                p_sim = round(v_sim * i_sim, 2)

            # Escenario 5: Desconexión de String (16:00 a 17:30)
            elif 16.0 <= hour <= 17.5:
                scenario_name = "5. DESCONEXIÓN DE CADENA"
                i_sim = 0.0
                v_sim = round(self.physics.v_oc_stc * (1.0 - 0.003 * (t_cell - 25.0)), 2)
                p_sim = 0.0

            # 3. Integración de Energía (kWh): E = P * dt / 1000
            energy_actual_kwh += (p_sim * dt_hours) / 1000.0
            energy_expected_kwh += (p_expected * dt_hours) / 1000.0

            # 4. Inferencia de Inteligencia Artificial
            diag = self.ai.diagnose_measurement(
                v_dc=v_sim,
                i_dc=i_sim,
                g_irradiance=g_sim,
                t_panel=t_sim,
                t_ambient=t_amb,
                hour_of_day=hour
            )

            # 5. Filtro de Histéresis Temporal (Prevención de Falsas Alarmas)
            is_alert_dispatched = False
            if diag.is_anomaly:
                consecutive_anomaly_cycles += 1
                if consecutive_anomaly_cycles >= self.hysteresis_threshold:
                    is_alert_dispatched = True
                    alerts_fired.append({
                        "hour": f"{int(hour):02d}:{int((hour%1)*60):02d}",
                        "scenario": scenario_name,
                        "category": diag.fault_category.value,
                        "confidence": diag.confidence_level,
                        "loss_pct": diag.loss_percentage
                    })
                else:
                    false_alarms_blocked += 1
            else:
                consecutive_anomaly_cycles = 0

            results.append({
                "time": current_time.strftime("%H:%M"),
                "scenario": scenario_name,
                "g_irradiance": g_sim,
                "t_panel": t_sim,
                "v_dc": v_sim,
                "i_dc": i_sim,
                "p_actual_w": p_sim,
                "p_expected_w": p_expected,
                "is_anomaly": diag.is_anomaly,
                "alert_dispatched": is_alert_dispatched,
                "fault_category": diag.fault_category.value
            })

        # Balance Financiero y Pérdidas
        energy_loss_kwh = max(0.0, energy_expected_kwh - energy_actual_kwh)
        financial_loss_usd = energy_loss_kwh * self.tariff
        overall_pr = (energy_actual_kwh / max(0.01, energy_expected_kwh)) * 100.0

        return {
            "total_points": len(results),
            "energy_expected_kwh": round(energy_expected_kwh, 3),
            "energy_actual_kwh": round(energy_actual_kwh, 3),
            "energy_loss_kwh": round(energy_loss_kwh, 3),
            "overall_performance_ratio_pct": round(overall_pr, 2),
            "financial_loss_usd": round(financial_loss_usd, 3),
            "false_alarms_blocked_by_hysteresis": false_alarms_blocked,
            "confirmed_alerts_count": len(alerts_fired),
            "alerts_summary": alerts_fired,
            "samples": results
        }


if __name__ == "__main__":
    sim = DynamicDaySimulator(nominal_capacity_kw=1.0)
    report = sim.simulate_24h_cycle()

    print("=" * 75)
    print("INFORME DE SIMULACIÓN DIURNA CONTINUA (FASE 8)")
    print("=" * 75)
    print(f"• Energía Teórica Esperada: {report['energy_expected_kwh']} kWh")
    print(f"• Energía Realmente Generada: {report['energy_actual_kwh']} kWh")
    print(f"• Energía Perdida por Anomalías: {report['energy_loss_kwh']} kWh (-{100 - report['overall_performance_ratio_pct']:.1f}%)")
    print(f"• Performance Ratio Diario Global: {report['overall_performance_ratio_pct']}%")
    print(f"• Pérdida Económica Diaria Estimada: ${report['financial_loss_usd']} USD (Tarifa: $0.18/kWh)")
    print(f"• Falsas Alarmas Bloqueadas por Histéresis: {report['false_alarms_blocked_by_hysteresis']} (Nubes rápidas descartadas)")
    print(f"• Alertas Críticas Confirmadas y Notificadas: {report['confirmed_alerts_count']}")
    print("\nResumen de Alertas Confirmadas Despachadas:")
    for a in report["alerts_summary"][:4]:
        print(f"  [{a['hour']}] {a['scenario']} -> Diagnóstico: {a['category']} (Certeza: {a['confidence']*100:.1f}%, Pérdida: {a['loss_pct']}%)")
    print("=" * 75)
