"""
GENERADOR DE DATASET ANUAL REAL DE 365 DÍAS (NASA POWER MEDELLÍN 2025)
======================================================================
Carga mediciones horarias reales de irradiancia solar, temperatura ambiente,
humedad relativa y velocidad del viento para todo el año 2025 (8,760 horas)
en Medellín, Colombia (Lat: 6.2442, Lon: -75.5812).

Realiza una partición temporal estricta sin fuga de datos:
- Entrenamiento: Días 1 a 250 (2025-01-01 a 2025-09-07)
- Prueba ciega (Out-of-Time Test): Días 251 a 365 (2025-09-08 a 2025-12-31)
"""
import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Tuple
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.pv_physics_simulator import PhotovoltaicPhysicsEngine

DEFAULT_NASA_CSV = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "datasets", "medellin_2025_nasa_power_hourly.csv")
)

FAULT_CATEGORIES = [
    "NORMAL",
    "SHADING",
    "SOILING",
    "STRING_DISCONNECTED",
    "INVERTER_FAULT",
    "HOTSPOT",
    "SENSOR_FAULT",
]


def _build_sample_for_category(
    cat: str,
    row: Dict,
    engine: PhotovoltaicPhysicsEngine,
    rng: random.Random
) -> Dict:
    """Construye un vector de telemetría física sobre una hora climática real."""
    dt = datetime.strptime(str(int(row["datetime_lst"])), "%Y%m%d%H")
    hour = float(dt.hour)
    g_irr = float(row["g_irradiance"])
    t_amb = float(row["t_ambient"])
    rh = float(row["rh_ambient"])
    wind_ms = float(row.get("wind_speed_ms", 0.8))

    # Temperatura de célula con efecto térmico NOCT y ligero enfriamiento eólico
    wind_cooling = 1.0 / (1.0 + 0.05 * max(0.0, wind_ms))
    delta_t_noct = g_irr * ((engine.noct - 20.0) / 800.0) * wind_cooling
    t_cell_nom = t_amb + delta_t_noct + rng.gauss(0, 1.0)

    v_nom, i_nom, p_nom = engine.calculate_iv_operating_point(g_irr, t_cell_nom)
    p_expected = engine.calculate_theoretical_power(g_irr, t_cell_nom)

    v_sample = v_nom
    i_sample = i_nom
    p_sample = p_nom
    t_panel = t_cell_nom

    if cat == "NORMAL":
        v_sample = round(v_nom * rng.uniform(0.975, 1.02), 2)
        i_sample = round(i_nom * rng.uniform(0.955, 1.025), 2)
        p_sample = round(v_sample * i_sample, 2)
    elif cat == "SHADING":
        i_sample = round(i_nom * rng.uniform(0.28, 0.56), 2)
        v_sample = round(v_nom * rng.uniform(0.48, 0.88), 2)
        p_sample = round(v_sample * i_sample, 2)
    elif cat == "SOILING":
        i_sample = round(i_nom * rng.uniform(0.68, 0.85), 2)
        v_sample = round(v_nom * rng.uniform(0.97, 1.01), 2)
        p_sample = round(v_sample * i_sample, 2)
    elif cat == "STRING_DISCONNECTED":
        i_sample = round(i_nom * rng.uniform(0.47, 0.53), 2)
        v_sample = round(v_nom * rng.uniform(0.97, 1.02), 2)
        p_sample = round(v_sample * i_sample, 2)
    elif cat == "INVERTER_FAULT":
        i_sample = 0.0
        v_sample = round(engine.v_oc_stc * (1.0 - 0.003 * (t_panel - 25.0)) * rng.uniform(0.98, 1.02), 2)
        p_sample = 0.0
    elif cat == "HOTSPOT":
        t_panel = round(t_cell_nom + rng.uniform(18.0, 35.0), 2)
        i_sample = round(i_nom * rng.uniform(0.84, 0.92), 2)
        v_sample = round(v_nom * rng.uniform(0.89, 0.96), 2)
        p_sample = round(v_sample * i_sample, 2)
    elif cat == "SENSOR_FAULT":
        mode = rng.random()
        if mode < 0.55:
            g_irr = round(rng.uniform(0.0, 2.0), 1)
        elif mode < 0.80:
            t_panel = round(rng.uniform(120.0, 155.0), 1)
        else:
            t_panel = round(rng.uniform(-35.0, -16.0), 1)

    delta_p = round(p_expected - p_sample, 2)
    pr = round(p_sample / max(1.0, p_expected), 4)

    return {
        "date": dt.strftime("%Y-%m-%d"),
        "day_of_year": dt.timetuple().tm_yday,
        "g_irradiance": round(g_irr, 1),
        "t_ambient": round(t_amb, 1),
        "t_panel": round(t_panel, 1),
        "rh_ambient": round(rh, 1),
        "hour_of_day": hour,
        "v_dc": round(v_sample, 2),
        "i_dc": round(i_sample, 2),
        "p_dc": round(p_sample, 2),
        "p_expected": round(p_expected, 2),
        "delta_p": delta_p,
        "performance_ratio": pr,
        "fault_category": cat,
        "is_anomaly": 0 if cat == "NORMAL" else 1
    }


def _generate_split_records(
    df_days: pd.DataFrame,
    engine: PhotovoltaicPhysicsEngine,
    seed: int,
    include_faults: bool = True
) -> List[Dict]:
    """Genera registros por cada hora diurna real (>40 W/m²) dentro del rango de días dado."""
    rng = random.Random(seed)
    records = []
    diurnal_rows = df_days[df_days["g_irradiance"] >= 40.0].to_dict(orient="records")

    for row in diurnal_rows:
        # Cada hora diurna real aporta su registro NORMAL
        records.append(_build_sample_for_category("NORMAL", row, engine, rng))
        if include_faults:
            for cat in FAULT_CATEGORIES[1:]:
                records.append(_build_sample_for_category(cat, row, engine, rng))

    return records


def build_annual_train_test_datasets(
    nasa_csv_path: str = DEFAULT_NASA_CSV,
    train_days: int = 250
) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Construye partición cronológica estricta de 365 días reales:
    - Días 1..train_days -> Entrenamiento
    - Días (train_days+1)..365 -> Prueba ciega fuera de muestra temporal
    """
    if not os.path.exists(nasa_csv_path):
        raise FileNotFoundError(f"No se encontró el archivo climático anual: {nasa_csv_path}")

    df = pd.read_csv(nasa_csv_path)
    df["dt"] = pd.to_datetime(df["datetime_lst"].astype(str), format="%Y%m%d%H")
    df["day_of_year"] = df["dt"].dt.dayofyear

    df_train = df[df["day_of_year"] <= train_days].copy()
    df_test = df[df["day_of_year"] > train_days].copy()

    engine = PhotovoltaicPhysicsEngine(p_stc_watts=1000.0, gamma_temp_coeff=-0.0038)

    train_records = _generate_split_records(df_train, engine, seed=202501, include_faults=True)
    test_records = _generate_split_records(df_test, engine, seed=202509, include_faults=True)

    metadata = {
        "climate_source": "NASA POWER Hourly 2025 (Medellin, Colombia 6.2442, -75.5812)",
        "total_year_hours": int(len(df)),
        "train_days": int(train_days),
        "test_days": int(df["day_of_year"].max() - train_days),
        "train_date_range": f"{df_train['dt'].min().strftime('%Y-%m-%d')} .. {df_train['dt'].max().strftime('%Y-%m-%d')}",
        "test_date_range": f"{df_test['dt'].min().strftime('%Y-%m-%d')} .. {df_test['dt'].max().strftime('%Y-%m-%d')}",
        "train_diurnal_hours": int((df_train["g_irradiance"] >= 40.0).sum()),
        "test_diurnal_hours": int((df_test["g_irradiance"] >= 40.0).sum()),
        "train_samples": len(train_records),
        "test_samples": len(test_records),
    }

    return train_records, test_records, metadata


if __name__ == "__main__":
    train_data, test_data, meta = build_annual_train_test_datasets()
    print("Resumen Split Anual Real (250 días Train / 115 días Test):")
    for k, v in meta.items():
        print(f"  - {k}: {v}")
