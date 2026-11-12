"""
EVALUADOR DE RENDIMIENTO TEMPORAL (OUT-OF-TIME) DE MODELOS DE IA (FASE 9)
========================================================================
Evalúa los modelos entrenados con los primeros 250 días del año (2025-01-01 a 2025-09-07)
sobre los 115 días restantes del año real de Medellín (2025-09-08 a 2025-12-31, NASA POWER).

Calcula:
1. Matriz de confusión multiclase 7x7 sobre los 115 días de prueba.
2. Precision, Recall, F1-Score y Soporte por categoría.
3. Tasas de Falsos Positivos (FPR) en operación normal.
4. Métricas de regresión (R², RMSE, MAE) prediciendo potencia real en los últimos 115 días.
"""
import os
import sys
import json
import numpy as np
import joblib

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ai_engine.pipelines.dataset_generator import generate_pv_dataset
from ai_engine.pipelines.annual_real_dataset import build_annual_train_test_datasets, DEFAULT_NASA_CSV

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    r2_score,
    mean_squared_error,
    mean_absolute_error
)


def evaluate_trained_models(models_dir: str = "", output_json: str = "", train_days: int = 250) -> dict:
    if not models_dir:
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))

    clf_path = os.path.join(models_dir, "pv_fault_classifier.joblib")
    reg_path = os.path.join(models_dir, "pv_power_regressor.joblib")

    if not os.path.exists(clf_path) or not os.path.exists(reg_path):
        raise FileNotFoundError("Modelos no encontrados. Ejecute train_models.py primero.")

    clf_bundle = joblib.load(clf_path)
    classifier = clf_bundle["model"]
    classes = clf_bundle["classes"]
    regressor = joblib.load(reg_path)

    # 1. Cargar los 115 días reales restantes (Días 251-365) como conjunto ciego out-of-time
    if os.path.exists(DEFAULT_NASA_CSV):
        _, test_data, meta = build_annual_train_test_datasets(DEFAULT_NASA_CSV, train_days=train_days)
        print(
            f"Evaluando Out-of-Time sobre {meta['test_days']} días reales "
            f"({meta['test_date_range']} | {meta['test_diurnal_hours']} horas diurnas | {len(test_data)} muestras)..."
        )
    else:
        print("Generando 1,400 muestras de prueba independientes (seed=9999)...")
        test_data = generate_pv_dataset(samples_per_category=200, seed=9999)
        meta = {"climate_source": "Synthetic Fallback", "train_days": train_days, "test_days": 115}

    # 2. Evaluación del Clasificador Multiclase
    X_test_clf = np.array([
        [d["g_irradiance"], d["t_panel"], d["v_dc"], d["i_dc"], d["p_dc"], d["delta_p"], d["performance_ratio"]]
        for d in test_data
    ])
    y_test_clf = np.array([d["fault_category"] for d in test_data])

    y_pred_clf = classifier.predict(X_test_clf)
    acc = accuracy_score(y_test_clf, y_pred_clf)
    cm = confusion_matrix(y_test_clf, y_pred_clf, labels=classes)
    clf_report = classification_report(y_test_clf, y_pred_clf, labels=classes, output_dict=True)

    # 3. Evaluación del Regresor de Potencia (sobre horas diurnas NORMALES de los días 251-365)
    normal_test = [d for d in test_data if d["fault_category"] == "NORMAL"]
    X_test_reg = np.array([
        [d["g_irradiance"], d["t_panel"], d["t_ambient"], d["rh_ambient"], d["hour_of_day"]]
        for d in normal_test
    ])
    y_test_reg = np.array([d["p_dc"] for d in normal_test])

    y_pred_reg = regressor.predict(X_test_reg)
    r2 = r2_score(y_test_reg, y_pred_reg)
    rmse = np.sqrt(mean_squared_error(y_test_reg, y_pred_reg))
    mae = mean_absolute_error(y_test_reg, y_pred_reg)

    # 4. Tasas de Falsos Positivos en Operación Normal
    normal_idx = classes.index("NORMAL")
    tn = cm[normal_idx, normal_idx]
    fp = np.sum(cm[normal_idx, :]) - tn
    fpr_normal = (fp / max(1, (fp + tn))) * 100.0

    results = {
        "evaluation_protocol": f"Temporal Split {meta.get('train_days', 250)}d Train / {meta.get('test_days', 115)}d Out-of-Time Test",
        "climate_source": meta.get("climate_source", ""),
        "train_date_range": meta.get("train_date_range", ""),
        "test_date_range": meta.get("test_date_range", ""),
        "test_total_samples": len(test_data),
        "classifier_accuracy_pct": round(acc * 100.0, 2),
        "regressor_r2_score": round(r2, 4),
        "regressor_rmse_watts": round(rmse, 2),
        "regressor_mae_watts": round(mae, 2),
        "normal_false_positive_rate_pct": round(fpr_normal, 2),
        "classes": classes,
        "confusion_matrix": cm.tolist(),
        "metrics_per_class": {
            cls_name: {
                "precision": round(clf_report[cls_name]["precision"] * 100.0, 2),
                "recall": round(clf_report[cls_name]["recall"] * 100.0, 2),
                "f1_score": round(clf_report[cls_name]["f1-score"] * 100.0, 2),
                "support": clf_report[cls_name]["support"]
            }
            for cls_name in classes if cls_name in clf_report
        }
    }

    if output_json:
        os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    out_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "evaluation_metrics.json"))
    res = evaluate_trained_models(output_json=out_file)

    print("=" * 75)
    print("INFORME DE EVALUACIÓN ESTADÍSTICA ANUAL (250d TRAIN / 115d TEST REAL)")
    print("=" * 75)
    print(f"• Fuente Climática: {res['climate_source']}")
    print(f"• Entrenamiento: {res['train_date_range']} | Prueba: {res['test_date_range']}")
    print(f"• Precisión Global del Clasificador (Accuracy): {res['classifier_accuracy_pct']}%")
    print(f"• Tasa de Falsos Positivos en Operación Normal (FPR): {res['normal_false_positive_rate_pct']}%")
    print(f"• Coeficiente R² del Predictor de Potencia: {res['regressor_r2_score']}")
    print(f"• Error RMSE del Predictor: {res['regressor_rmse_watts']} W | MAE: {res['regressor_mae_watts']} W")

    print("\nDesglose de Métricas por Categoría de Falla (Precision / Recall / F1):")
    print(f"{'Categoría':<22} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Soporte'}")
    print("-" * 75)
    for cls_name, m in res["metrics_per_class"].items():
        print(f"{cls_name:<22} | {m['precision']:>8.1f}% | {m['recall']:>8.1f}% | {m['f1_score']:>8.1f}% | {m['support']}")

    print("\nMatriz de Confusión (Filas: Real, Columnas: Predicción):")
    print(f"{'':<20}" + "".join([f"{c[:7]:>8}" for c in res["classes"]]))
    for idx, row in enumerate(res["confusion_matrix"]):
        print(f"{res['classes'][idx]:<20}" + "".join([f"{val:>8}" for val in row]))
    print("=" * 75)
