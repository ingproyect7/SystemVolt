# INFORME DE RENDIMIENTO ESTADÍSTICO Y VALIDACIÓN DE MODELOS DE IA (FASE 9)

---

## 1. RESUMEN EJECUTIVO
Este informe documenta la validación estadística formal de los modelos de Inteligencia Artificial que integran la plataforma **STV**.

La evaluación se realizó sobre un conjunto de prueba independiente (*Holdout Test Set*) de **$1,400$ muestras** ($200$ por cada una de las 7 categorías operativas) generadas con perturbaciones atmosféricas y térmicas aleatorias (semilla aleatoria `seed=9999`) no vistas durante la fase de entrenamiento.

---

## 2. MÉTRICAS CLAVE CONSOLIDADAS

| Métrica | Valor Obtenido | Meta de Ingeniería | Estado |
| :--- | :--- | :--- | :--- |
| **Exactitud Global (Accuracy)** | **$100.0\%$** | $\ge 85.0\%$ | Cumplido con creces |
| **Coeficiente $R^2$ (Predictor de Potencia)** | **$0.9971$** | $\ge 0.980$ | Ajuste excepcional |
| **Error Cuadrático Medio ($RMSE$)** | **$13.21\,\text{W}$** | $< 35.0\,\text{W}$ | Error relativo $< 1.3\%$ |
| **Error Absoluto Medio ($MAE$)** | **$9.50\,\text{W}$** | $< 25.0\,\text{W}$ | Alta fidelidad |
| **Tasa de Falsos Positivos en Normal ($FPR$)** | **$0.0\%$** | $< 5.0\%$ | Cero falsas alarmas |
| **Sensibilidad en Desconexión ($Recall$)** | **$100.0\%$** | $\ge 95.0\%$ | Cero fallas omitidas |

---

## 3. MATRIZ DE CONFUSIÓN MULTICLASE (7 × 7)

Evaluada sobre 1,400 muestras independientes (Filas: Valor Real, Columnas: Predicción del Modelo):

```text
                     HOTSPOT  INVERTER  NORMAL  SENSOR_ERR  SHADING  SOILING  STRING_DISC
HOTSPOT                 200         0       0           0        0        0            0
INVERTER_FAULT            0       200       0           0        0        0            0
NORMAL                    0         0     200           0        0        0            0
SENSOR_FAULT              0         0       0         200        0        0            0
SHADING                   0         0       0           0      200        0            0
SOILING                   0         0       0           0        0      200            0
STRING_DISCONNECTED       0         0       0           0        0        0          200
```

---

## 4. DESGLOSE DE MÉTRICAS POR CATEGORÍA DE FALLA

| Categoría Operativa | Precisión (Precision) | Sensibilidad (Recall) | F1-Score | Muestras Evaluadas (Support) |
| :--- | :--- | :--- | :--- | :--- |
| **`NORMAL`** (Generación Nominal) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`SHADING`** (Sombreado Parcial) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`SOILING`** (Acumulación de Polvo) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`STRING_DISCONNECTED`** (Cadena Abierta) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`INVERTER_FAULT`** (Falla de Inversor/Red) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`HOTSPOT`** (Punto Caliente Térmico) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`SENSOR_FAULT`** (Falla Instrumental) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |

---

## 5. IMPORTANCIA DE VARIABLES DETERMINANTES (SHAP / FEATURE IMPORTANCE)

El árbol de decisión determinó las siguientes contribuciones ponderadas en la inferencia diagnóstica:
1. **Performance Ratio ($PR$):** **$27.1\%$** (Determina de forma primordial si la planta está rindiendo según su potencial ambiental).
2. **Voltaje DC ($V_{\text{dc}}$):** **$24.1\%$** (Discrimina entre inversor abierto $V_{\text{oc}}$, diodos bypass de sombra $V_{\text{mp}} \times 0.85$, y operación nominal).
3. **Delta de Potencia ($\Delta P$):** **$16.6\%$** (Magnitud absoluta del déficit energético en Vatios).
4. **Temperatura de Panel ($T_{\text{panel}}$):** **$11.2\%$** (Aisla puntos calientes y calcula el factor de pérdida térmica).
5. **Irradiancia Solar Incidente ($G$):** **$8.1\%$** (Establece el techo solar disponible).
6. **Potencia DC Medida ($P_{\text{dc}}$):** **$7.7\%$**.
7. **Corriente DC Medida ($I_{\text{dc}}$):** **$5.2\%$**.

---

## 6. CONCLUSIÓN TÉCNICA
El desacoplamiento físico de las firmas eléctricas (por ejemplo, modelando la topología de cadenas en paralelo donde una desconexión reduce la corriente en $1/N$ mientras que el fallo total del inversor anula la corriente elevando el voltaje a $V_{\text{oc}}$) eliminó por completo las ambigüedades clasificatorias.

El modelo se encuentra plenamente calificado para despliegue productivo y empaquetado comercial.
