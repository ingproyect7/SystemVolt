"""
GENERADOR DE DATASETS FOTOVOLTAICOS FÍSICAMENTE ETIQUETADOS (STV)
================================================================
Genera un conjunto de datos sintéticos de alta fidelidad basado en curvas I-V reales,
modelo NOCT térmico y ecuaciones IEC 60891, inyectando 7 categorías de funcionamiento
y fallas eléctricas con sus respectivas firmas termoeléctricas.
"""
import os
import sys
import math
import random
import csv
from typing import List, Dict

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.pv_physics_simulator import PhotovoltaicPhysicsEngine


def generate_pv_dataset(samples_per_category: int = 600, output_csv: str = "") -> List[Dict]:
    """
    Genera un dataset balanceado con 7 categorías de operación:
    0: NORMAL
    1: SHADING (Sombreado parcial)
    2: SOILING (Acumulación de polvo / suciedad)
    3: STRING_DISCONNECTED (Desconexión de cadena / fusible fundido)
    4: INVERTER_FAULT (Falla de inversor / pérdida de red)
    5: HOTSPOT (Punto caliente térmico)
    6: SENSOR_FAULT (Falla de sensor de radiación o temperatura)
    """
    engine = PhotovoltaicPhysicsEngine(p_stc_watts=1000.0, gamma_temp_coeff=-0.0038)
    categories = [
        "NORMAL",
        "SHADING",
        "SOILING",
        "STRING_DISCONNECTED",
        "INVERTER_FAULT",
        "HOTSPOT",
        "SENSOR_FAULT"
    ]
    
    dataset = []
    random.seed(2026)

    for cat in categories:
        for _ in range(samples_per_category):
            # 1. Condiciones ambientales aleatorias representativas
            hour = random.uniform(6.5, 17.5) # Horas de sol
            sun_angle = math.sin((hour - 6.0) / 12.0 * math.pi)
            
            # Irradiancia diurna base (W/m²) con ruido atmosférico
            g_base = 980.0 * (sun_angle ** 1.1) + random.gauss(0, 20)
            g_irr = max(50.0, min(1200.0, g_base))
            
            # Temperatura ambiente (°C)
            t_amb = 20.0 + 10.0 * sun_angle + random.uniform(-2, 3)
            # Humedad (%)
            rh = max(20.0, min(95.0, 75.0 - 30.0 * sun_angle + random.gauss(0, 5)))
            
            # Temperatura de célula nominal
            t_cell_nom = engine.calculate_cell_temperature(g_irr, t_amb) + random.gauss(0, 1.0)
            v_nom, i_nom, p_nom = engine.calculate_iv_operating_point(g_irr, t_cell_nom)
            p_expected = engine.calculate_theoretical_power(g_irr, t_cell_nom)

            v_sample = v_nom
            i_sample = i_nom
            p_sample = p_nom
            t_panel = t_cell_nom

            # 2. Inyección de firma física según categoría
            if cat == "NORMAL":
                # Operación óptima: pequeña variación de ruido natural (+/- 2%)
                noise = random.uniform(0.96, 1.02)
                i_sample = round(i_nom * noise, 2)
                v_sample = round(v_nom * noise, 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "SHADING":
                # Sombra parcial: corriente cae drásticamente (40% a 70%), tensión cae levemente
                shade_severity = random.uniform(0.30, 0.55)
                i_sample = round(i_nom * shade_severity, 2)
                v_sample = round(v_nom * random.uniform(0.82, 0.90), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "SOILING":
                # Polvo acumulado: reducción moderada continua de corriente (15% a 30%), voltaje intacto
                soil_factor = random.uniform(0.70, 0.85)
                i_sample = round(i_nom * soil_factor, 2)
                v_sample = round(v_nom * random.uniform(0.97, 1.01), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "STRING_DISCONNECTED":
                # Desconexión de 1 de 2 strings en paralelo: Corriente cae al 50%, Tensión se mantiene en Vmp
                i_sample = round(i_nom * 0.50, 2)
                v_sample = round(v_nom * random.uniform(0.98, 1.02), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "INVERTER_FAULT":
                # Inversor apagado o disparado por red: Corriente total = 0, Tensión sube a Voc
                i_sample = 0.0
                v_sample = round(engine.v_oc_stc * (1.0 - 0.003 * (t_panel - 25.0)), 2)
                p_sample = 0.0

            elif cat == "HOTSPOT":
                # Punto caliente: temperatura focalizada anómala (+18°C a +35°C), potencia cae ~15%
                t_panel = round(t_cell_nom + random.uniform(18.0, 32.0), 2)
                i_sample = round(i_nom * random.uniform(0.85, 0.92), 2)
                v_sample = round(v_nom * random.uniform(0.90, 0.95), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "SENSOR_FAULT":
                # Sensor dañado: e.g. radiación 0 W/m² con producción activa o temperatura corrupta
                if random.random() > 0.5:
                    g_irr = 0.0
                else:
                    t_panel = 135.0  # Fuera de escala física

            # Métricas calculadas para entrenamiento
            delta_p = round(p_expected - p_sample, 2)
            pr = round(p_sample / max(1.0, p_expected), 4)

            record = {
                "g_irradiance": round(g_irr, 1),
                "t_ambient": round(t_amb, 1),
                "t_panel": round(t_panel, 1),
                "rh_ambient": round(rh, 1),
                "hour_of_day": round(hour, 2),
                "v_dc": round(v_sample, 2),
                "i_dc": round(i_sample, 2),
                "p_dc": round(p_sample, 2),
                "p_expected": round(p_expected, 2),
                "delta_p": delta_p,
                "performance_ratio": pr,
                "fault_category": cat,
                "is_anomaly": 0 if cat == "NORMAL" else 1
            }
            dataset.append(record)

    # Exportar a CSV si se indica ruta
    if output_csv and dataset:
        os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
        keys = dataset[0].keys()
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(dataset)

    return dataset


if __name__ == "__main__":
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets", "pv_training_dataset.csv"))
    data = generate_pv_dataset(samples_per_category=700, output_csv=out_path)
    print(f"Dataset generado con {len(data)} muestras en: {out_path}")
