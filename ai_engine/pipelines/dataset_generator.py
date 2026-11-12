"""
GENERADOR DE DATASETS FOTOVOLTAICOS FÍSICAMENTE ETIQUETADOS (STV)
================================================================
Genera un conjunto de datos sintéticos de alta fidelidad basado en curvas I-V reales,
modelo NOCT térmico y ecuaciones IEC 60891, inyectando 7 categorías de funcionamiento
y fallas eléctricas con sus respectivas firmas termoeléctricas y variabilidad climática.
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


def generate_pv_dataset(
    samples_per_category: int = 1500,
    output_csv: str = "",
    seed: int = 2026
) -> List[Dict]:
    """
    Genera un dataset balanceado con 7 categorías de operación:
    0: NORMAL
    1: SHADING (Sombreado parcial con activación de diodos bypass)
    2: SOILING (Acumulación de polvo / suciedad)
    3: STRING_DISCONNECTED (Desconexión de cadena en paralelo / fusible fundido)
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
    rng = random.Random(seed)

    for cat in categories:
        for _ in range(samples_per_category):
            # 1. Condiciones ambientales aleatorias representativas (incluye baja nubosidad y pico)
            hour = rng.uniform(6.2, 17.8)
            sun_angle = math.sin((hour - 6.0) / 12.0 * math.pi)

            # Atenuación atmosférica ocasional (nubes parciales sanas)
            cloud_attenuation = rng.uniform(0.45, 1.0) if rng.random() < 0.25 else 1.0
            g_base = 985.0 * (sun_angle ** 1.1) * cloud_attenuation + rng.gauss(0, 22)
            g_irr = max(45.0, min(1200.0, g_base))

            # Temperatura ambiente (°C) y humedad (%)
            t_amb = 19.0 + 11.0 * sun_angle + rng.uniform(-2.5, 3.5)
            rh = max(20.0, min(95.0, 76.0 - 30.0 * sun_angle + rng.gauss(0, 5)))

            # Temperatura de célula nominal con variación por viento
            t_cell_nom = engine.calculate_cell_temperature(g_irr, t_amb) + rng.gauss(0, 1.6)
            v_nom, i_nom, p_nom = engine.calculate_iv_operating_point(g_irr, t_cell_nom)
            p_expected = engine.calculate_theoretical_power(g_irr, t_cell_nom)

            v_sample = v_nom
            i_sample = i_nom
            p_sample = p_nom
            t_panel = t_cell_nom

            # 2. Inyección de firma física según categoría
            if cat == "NORMAL":
                # Operación óptima con ruido instrumental realista (+/- 3%)
                v_sample = round(v_nom * rng.uniform(0.97, 1.02), 2)
                i_sample = round(i_nom * rng.uniform(0.95, 1.03), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "SHADING":
                # Sombra parcial: corriente cae 40%-72%, tensión cae 12%-55% por bypass de 1 o 2 sub-módulos
                shade_i = rng.uniform(0.28, 0.58)
                shade_v = rng.uniform(0.48, 0.90)
                i_sample = round(i_nom * shade_i, 2)
                v_sample = round(v_nom * shade_v, 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "SOILING":
                # Polvo acumulado: reducción continua de corriente (14%-31%), voltaje prácticamente intacto
                soil_factor = rng.uniform(0.69, 0.86)
                i_sample = round(i_nom * soil_factor, 2)
                v_sample = round(v_nom * rng.uniform(0.96, 1.01), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "STRING_DISCONNECTED":
                # Desconexión de 1 de 2 strings en paralelo: corriente cae ~50%, tensión se mantiene en Vmp
                i_sample = round(i_nom * rng.uniform(0.47, 0.53), 2)
                v_sample = round(v_nom * rng.uniform(0.97, 1.02), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "INVERTER_FAULT":
                # Inversor apagado o disparado por red: corriente = 0, tensión sube a Voc
                i_sample = 0.0
                v_sample = round(engine.v_oc_stc * (1.0 - 0.003 * (t_panel - 25.0)) * rng.uniform(0.98, 1.02), 2)
                p_sample = 0.0

            elif cat == "HOTSPOT":
                # Punto caliente: sobrecalentamiento focalizado (+18°C a +36°C), leve caída de V e I
                t_panel = round(t_cell_nom + rng.uniform(18.0, 36.0), 2)
                i_sample = round(i_nom * rng.uniform(0.84, 0.93), 2)
                v_sample = round(v_nom * rng.uniform(0.89, 0.96), 2)
                p_sample = round(v_sample * i_sample, 2)

            elif cat == "SENSOR_FAULT":
                # Sensor dañado: piranómetro en 0 con generación activa o PT100 fuera de escala física
                mode = rng.random()
                if mode < 0.55:
                    g_irr = round(rng.uniform(0.0, 2.0), 1)
                elif mode < 0.80:
                    t_panel = round(rng.uniform(120.0, 155.0), 1)
                else:
                    t_panel = round(rng.uniform(-35.0, -16.0), 1)

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
    data = generate_pv_dataset(samples_per_category=1500, output_csv=out_path, seed=2026)
    print(f"Dataset generado con {len(data)} muestras en: {out_path}")
