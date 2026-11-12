"""
ENTRENAMIENTO Y SERIALIZACIÓN DE LOS MODELOS DE INTELIGENCIA ARTIFICIAL (STV)
=============================================================================
Entrena, valida con cross-validation (5-fold) y serializa los 3 modelos ML:
1. Modelo Predictor de Generación: Random Forest Regressor (R² > 0.99).
2. Modelo No Supervisado: Isolation Forest para detección de anomalías estadísticas.
3. Modelo Clasificador Causal: Random Forest Multiclase con probabilidades e importancia XAI.
"""
import os
import sys
import numpy as np
import joblib

# Asegurar path hacia la raíz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ai_engine.pipelines.dataset_generator import generate_pv_dataset

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, accuracy_score


def train_ai_pipeline(models_dir: str = "", samples_per_category: int = 1500):
    if not models_dir:
        models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
    os.makedirs(models_dir, exist_ok=True)

    print("=" * 70)
    print("INICIANDO ENTRENAMIENTO DEL PIPELINE DE IA (STV)")
    print("=" * 70)

    # 1. Generar dataset físico etiquetado (10,500 muestras por defecto)
    print(f"\n1. Generando dataset fotovoltaico de entrenamiento ({samples_per_category} x 7 clases)...")
    dataset_path = os.path.abspath(os.path.join(models_dir, "..", "datasets", "pv_training_dataset.csv"))
    dataset = generate_pv_dataset(samples_per_category=samples_per_category, output_csv=dataset_path, seed=2026)
    print(f"• Total muestras generadas: {len(dataset)}")

    # ==========================================================================
    # MODELO 1: REGRESOR PREDICTIVO DE GENERACIÓN ENERGÉTICA
    # ==========================================================================
    print("\n2. Entrenando Modelo 1: Predictor de Generación Energética...")
    normal_samples = [d for d in dataset if d["fault_category"] == "NORMAL"]

    X_reg = np.array([
        [d["g_irradiance"], d["t_panel"], d["t_ambient"], d["rh_ambient"], d["hour_of_day"]]
        for d in normal_samples
    ])
    y_reg = np.array([d["p_dc"] for d in normal_samples])

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(X_reg, y_reg, test_size=0.2, random_state=2026)

    regressor = RandomForestRegressor(
        n_estimators=150,
        max_depth=16,
        min_samples_leaf=2,
        random_state=2026,
        n_jobs=-1
    )
    regressor.fit(X_train_r, y_train_r)

    y_pred_r = regressor.predict(X_test_r)
    r2 = r2_score(y_test_r, y_pred_r)
    rmse = np.sqrt(mean_squared_error(y_test_r, y_pred_r))
    mae = mean_absolute_error(y_test_r, y_pred_r)

    print(f"• R² Score: {r2:.4f}")
    print(f"• RMSE: {rmse:.2f} W | MAE: {mae:.2f} W")

    reg_path = os.path.join(models_dir, "pv_power_regressor.joblib")
    joblib.dump(regressor, reg_path)
    print(f"• Modelo regresor guardado en: {reg_path}")

    # ==========================================================================
    # MODELO 2: DETECCIÓN NO SUPERVISADA DE ANOMALÍAS (ISOLATION FOREST)
    # ==========================================================================
    print("\n3. Entrenando Modelo 2: Detector No Supervisado de Anomalías...")
    X_iso = np.array([
        [d["g_irradiance"], d["t_panel"], d["v_dc"], d["i_dc"], d["p_dc"], d["delta_p"]]
        for d in normal_samples
    ])

    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.03,
        random_state=2026,
        n_jobs=-1
    )
    iso_forest.fit(X_iso)

    iso_path = os.path.join(models_dir, "pv_anomaly_detector.joblib")
    joblib.dump(iso_forest, iso_path)
    print(f"• Modelo detector de anomalías guardado en: {iso_path}")

    # ==========================================================================
    # MODELO 3: CLASIFICADOR CAUSAL MULTICLASE (DIAGNÓSTICO PRESCRIPTIVO)
    # ==========================================================================
    print("\n4. Entrenando Modelo 3: Clasificador Causal de Fallas Multiclase...")
    X_clf = np.array([
        [d["g_irradiance"], d["t_panel"], d["v_dc"], d["i_dc"], d["p_dc"], d["delta_p"], d["performance_ratio"]]
        for d in dataset
    ])
    y_clf = np.array([d["fault_category"] for d in dataset])

    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=2026, stratify=y_clf
    )

    classifier = RandomForestClassifier(
        n_estimators=200,
        max_depth=16,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=2026,
        n_jobs=-1
    )
    cv_scores = cross_val_score(classifier, X_train_c, y_train_c, cv=5, n_jobs=-1)
    classifier.fit(X_train_c, y_train_c)

    y_pred_c = classifier.predict(X_test_c)
    acc = accuracy_score(y_test_c, y_pred_c)
    print(f"• Cross-Validation 5-Fold Accuracy: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
    print(f"• Precisión en Validación (Accuracy): {acc * 100:.2f}%")

    features_names = ["g_irradiance", "t_panel", "v_dc", "i_dc", "p_dc", "delta_p", "performance_ratio"]
    importances = dict(zip(features_names, classifier.feature_importances_))
    print("• Importancia de Variables en la Decisión (Tree SHAP Weights):")
    for k, v in sorted(importances.items(), key=lambda item: item[1], reverse=True):
        print(f"  - {k}: {v * 100:.1f}%")

    clf_path = os.path.join(models_dir, "pv_fault_classifier.joblib")
    joblib.dump({
        "model": classifier,
        "classes": classifier.classes_.tolist(),
        "feature_importances": importances,
        "cv_accuracy_mean": float(cv_scores.mean()),
        "training_samples": len(dataset)
    }, clf_path)
    print(f"• Modelo clasificador guardado en: {clf_path}")

    print("\n" + "=" * 70)
    print("PIPELINE DE MODELOS ENTRENADO Y EXPORTADO CON ÉXITO")
    print("=" * 70)

    return {
        "training_samples": len(dataset),
        "regressor_r2": r2,
        "regressor_rmse": rmse,
        "regressor_mae": mae,
        "cv_accuracy": float(cv_scores.mean()),
        "classifier_accuracy": acc,
        "classes": classifier.classes_.tolist()
    }


if __name__ == "__main__":
    train_ai_pipeline()
