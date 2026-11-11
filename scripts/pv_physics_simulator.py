"""
SIMULADOR FÍSICO Y MATEMÁTICO DE GENERACIÓN FOTOVOLTAICA (STV)
=============================================================
Este script implementa modelos de física fotovoltaica validados (Sandia National Labs,
modelo térmico NOCT y ecuaciones IEC 60891) para generar datos sintéticos realistas
e inyectar fallas controladas para pruebas de algoritmos de Inteligencia Artificial.

NOTA DE INGENIERÍA:
Este software genera datos de prueba claramente diferenciados de telemetría real de campo.
Permite validar la recepción de datos y la robustez del motor de diagnóstico antes de
conectar el hardware físico real a la instalación.
"""
import argparse
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class PhotovoltaicPhysicsEngine:
    def __init__(
        self,
        p_stc_watts: float = 1000.0,       # Potencia pico nominal a 1000 W/m² y 25°C
        gamma_temp_coeff: float = -0.0038, # Coeficiente térmico de potencia (-0.38%/°C)
        noct_celsius: float = 45.0,        # Nominal Operating Cell Temperature
        v_mp_stc: float = 380.0,           # Voltaje de máxima potencia en STC (V)
        i_mp_stc: float = 2.63,            # Corriente de máxima potencia en STC (A)
        v_oc_stc: float = 450.0,           # Voltaje de circuito abierto en STC (V)
        i_sc_stc: float = 2.85,            # Corriente de cortocircuito en STC (A)
        inverter_nominal_eff: float = 0.975 # Rendimiento nominal del inversor (97.5%)
    ):
        self.p_stc = p_stc_watts
        self.gamma = gamma_temp_coeff
        self.noct = noct_celsius
        self.v_mp_stc = v_mp_stc
        self.i_mp_stc = i_mp_stc
        self.v_oc_stc = v_oc_stc
        self.i_sc_stc = i_sc_stc
        self.inv_eff = inverter_nominal_eff

    def calculate_cell_temperature(self, g_irradiance: float, t_ambient: float) -> float:
        """
        Calcula la temperatura de la célula solar a partir de la temperatura ambiente
        y la irradiancia incidente usando la formulación empírica estándar del NOCT:
        T_cell = T_amb + G * (NOCT - 20) / 800
        """
        if g_irradiance <= 0.0:
            return t_ambient
        delta_t = g_irradiance * ((self.noct - 20.0) / 800.0)
        return round(t_ambient + delta_t, 2)

    def calculate_theoretical_power(self, g_irradiance: float, t_cell: float) -> float:
        """
        Modelo Físico Sandia / IEC 60891:
        P_esperada = P_stc * (G / 1000) * [1 + gamma * (T_cell - 25)] * n_inversor
        """
        if g_irradiance <= 5.0:
            return 0.0
        
        ratio_g = g_irradiance / 1000.0
        thermal_derating = 1.0 + self.gamma * (t_cell - 25.0)
        thermal_derating = max(0.1, thermal_derating)  # Protección contra valores negativos extremos
        
        p_dc_expected = self.p_stc * ratio_g * thermal_derating
        return round(max(0.0, p_dc_expected * self.inv_eff), 2)

    def calculate_iv_operating_point(self, g_irradiance: float, t_cell: float) -> Tuple[float, float, float]:
        """
        Calcula el punto de operación nominal en máxima potencia (V_mp, I_mp, P_mp).
        - Corriente I_mp escala linealmente con la irradiancia G.
        - Voltaje V_mp disminuye linealmente con el aumento de T_cell (-0.30%/°C).
        """
        if g_irradiance <= 5.0:
            return 0.0, 0.0, 0.0
            
        ratio_g = g_irradiance / 1000.0
        beta_v = -0.0030  # Coeficiente de voltaje con temperatura (-0.30%/°C)
        
        # Corriente proporcional a la irradiancia
        i_mp = self.i_mp_stc * ratio_g * (1.0 + 0.0005 * (t_cell - 25.0))
        # Voltaje dependiente de temperatura y logaritmo de irradiancia
        v_mp = self.v_mp_stc * (1.0 + beta_v * (t_cell - 25.0)) * (1.0 + 0.05 * math.log(max(0.01, ratio_g)))
        
        v_mp = max(0.0, v_mp)
        i_mp = max(0.0, i_mp)
        p_mp = round(v_mp * i_mp, 2)
        return round(v_mp, 2), round(i_mp, 2), p_mp

    def inject_fault(
        self,
        fault_type: str,
        v_nominal: float,
        i_nominal: float,
        p_nominal: float,
        t_cell: float
    ) -> Dict[str, float]:
        """
        Aplica distorsiones físicas al vector eléctrico para simular fallas reales:
        - SHADING: Caída brusca de corriente, tensión con oscilación por diodos bypass.
        - SOILING: Reducción del 20-30% en corriente, voltaje permanece normal.
        - STRING_DISCONNECTED: I=0, V sube a Voc.
        - INVERTER_FAULT: I=0, V en Voc, P=0.
        - HOTSPOT: T_cell se eleva anómalamente (+25°C), potencia cae ~15%.
        """
        fault = fault_type.upper()
        res = {
            "v_dc": v_nominal,
            "i_dc": i_nominal,
            "p_dc": p_nominal,
            "t_panel": t_cell,
            "fault_injected": fault
        }

        if fault == "NORMAL":
            pass
            
        elif fault == "SHADING":
            # Sombreado parcial: corriente cae drásticamente (60%), voltaje cae un 15% por diodos
            res["i_dc"] = round(i_nominal * 0.38, 2)
            res["v_dc"] = round(v_nominal * 0.85, 2)
            res["p_dc"] = round(res["v_dc"] * res["i_dc"], 2)
            
        elif fault == "SOILING":
            # Suciedad homogénea: corriente cae 25%, voltaje inalterado
            res["i_dc"] = round(i_nominal * 0.75, 2)
            res["v_dc"] = v_nominal
            res["p_dc"] = round(res["v_dc"] * res["i_dc"], 2)
            
        elif fault == "STRING_DISCONNECTED":
            # Circuito abierto: corriente cero, voltaje sube a Voc
            res["i_dc"] = 0.0
            res["v_dc"] = round(self.v_oc_stc * (1.0 - 0.003 * (t_cell - 25.0)), 2)
            res["p_dc"] = 0.0
            
        elif fault == "INVERTER_FAULT":
            # Inversor fuera de servicio: no consume corriente del generador
            res["i_dc"] = 0.0
            res["v_dc"] = round(self.v_oc_stc * (1.0 - 0.003 * (t_cell - 25.0)), 2)
            res["p_dc"] = 0.0
            
        elif fault == "HOTSPOT":
            # Célula rota/bloqueada disipa calor: sobrecalentamiento local
            res["t_panel"] = round(t_cell + 26.5, 2)
            res["v_dc"] = round(v_nominal * 0.92, 2)
            res["i_dc"] = round(i_nominal * 0.88, 2)
            res["p_dc"] = round(res["v_dc"] * res["i_dc"], 2)
            
        else:
            raise ValueError(f"Falla no reconocida: {fault}")

        return res


def simulate_daily_curve(fault_schedule: Dict[int, str] = None) -> List[Dict]:
    """
    Simula una curva solar diaria (desde las 06:00 hasta las 18:00) a intervalos de 15 minutos,
    permitiendo programar inyecciones de fallas en horarios específicos.
    """
    engine = PhotovoltaicPhysicsEngine(p_stc_watts=1000.0)
    data_points = []
    base_time = datetime(2026, 11, 11, 6, 0, 0)
    
    if fault_schedule is None:
        fault_schedule = {
            12: "SHADING",  # Inyectar sombreado a las 12:00
            13: "SHADING",  # Continúa a las 13:00
        }

    for step in range(49):  # 12 horas * 4 muestras/hora + 1
        current_time = base_time + timedelta(minutes=step * 15)
        hour = current_time.hour + current_time.minute / 60.0
        
        # Modelo semisinusoidal de irradiancia solar diurna
        if 6.0 <= hour <= 18.0:
            solar_altitude = math.sin((hour - 6.0) / 12.0 * math.pi)
            g_irr = round(max(0.0, 980.0 * (solar_altitude ** 1.1)), 1)
            t_amb = round(20.0 + 10.0 * math.sin((hour - 8.0) / 12.0 * math.pi), 1)
        else:
            g_irr = 0.0
            t_amb = 18.0

        t_cell = engine.calculate_cell_temperature(g_irr, t_amb)
        v_nom, i_nom, p_nom = engine.calculate_iv_operating_point(g_irr, t_cell)
        p_theor = engine.calculate_theoretical_power(g_irr, t_cell)

        # Determinar falla a inyectar según la hora
        fault_to_apply = fault_schedule.get(current_time.hour, "NORMAL")
        
        sample = engine.inject_fault(
            fault_type=fault_to_apply,
            v_nominal=v_nom,
            i_nominal=i_nom,
            p_nominal=p_nom,
            t_cell=t_cell
        )

        record = {
            "timestamp": current_time.isoformat(),
            "irradiance_w_m2": g_irr,
            "ambient_temp_c": t_amb,
            "panel_temp_c": sample["t_panel"],
            "v_dc": sample["v_dc"],
            "i_dc": sample["i_dc"],
            "p_actual_dc": sample["p_dc"],
            "p_expected_theor": p_theor,
            "fault_label": sample["fault_injected"]
        }
        data_points.append(record)

    return data_points


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador Físico Fotovoltaico STV")
    parser.add_argument("--test-case", action="store_true", help="Evaluar caso específico del requerimiento obligatorio")
    parser.add_argument("--output", type=str, default="", help="Guardar salida de simulación en archivo JSON")
    args = parser.parse_args()

    engine = PhotovoltaicPhysicsEngine(p_stc_watts=1000.0)

    if args.test_case:
        # Caso obligatorio del usuario: G=950 W/m², T_panel=48°C, P_esp=800W, P_real=310W
        g_test = 950.0
        t_test = 48.0
        p_esp = engine.calculate_theoretical_power(g_test, t_test)
        p_real = 310.0
        loss_pct = round(((p_esp - p_real) / p_esp) * 100.0, 2)
        
        print("=" * 70)
        print("EVALUACIÓN DEL CASO OBLIGATORIO MEDIANTE FÍSICA FOTOVOLTAICA:")
        print(f"• Irradiancia Solar de Entrada: {g_test} W/m²")
        print(f"• Temperatura de Célula: {t_test} °C")
        print(f"• Potencia Teórica Calculada (P_esperada): {p_esp} W")
        print(f"• Potencia Real Medida en Terreno (P_real): {p_real} W")
        print(f"• Pérdida Energética: {loss_pct}% (-{round(p_esp - p_real, 2)} W)")
        print("=" * 70)
    else:
        results = simulate_daily_curve()
        print(f"Simulación generada exitosamente. Total registros generados: {len(results)}")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            print(f"Datos exportados a: {args.output}")
        else:
            # Imprimir muestra de las 12:00
            print("Muestra a las 12:00 (con sombreado inyectado):")
            print(json.dumps(results[24], indent=2))
