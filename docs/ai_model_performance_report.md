# INFORME DE RENDIMIENTO ESTADÍSTICO Y VALIDACIÓN DE MODELOS DE IA (FASE 9)

---

## 1. RESUMEN EJECUTIVO
Este informe documenta la validación estadística formal de los modelos de Inteligencia Artificial que integran la plataforma **STV**, entrenados sobre **$10,500$ muestras** ($1,500$ por cada una de las 7 categorías operativas) con validación cruzada *5-Fold* ($99.95\% \pm 0.04\%$).

La evaluación final se realizó sobre un conjunto de prueba independiente (*Holdout Test Set*) de **$1,400$ muestras** ($200$ por categoría) generadas con semilla independiente (`seed=9999`), perturbaciones térmicas, nubes parciales y ruido instrumental no vistos durante el entrenamiento.

---

## 2. MÉTRICAS CLAVE CONSOLIDADAS

| Métrica | Valor Obtenido | Meta de Ingeniería | Estado |
| :--- | :--- | :--- | :--- |
| **Exactitud Global (Accuracy)** | **$99.86\%$** | $\ge 85.0\%$ | Cumplido con creces |
| **Validación Cruzada (5-Fold CV)** | **$99.95\% \pm 0.04\%$** | $\ge 85.0\%$ | Alta generalización |
| **Coeficiente $R^2$ (Predictor de Potencia)** | **$0.9950$** | $\ge 0.980$ | Ajuste excepcional |
| **Error Cuadrático Medio ($RMSE$)** | **$17.90\,\text{W}$** | $< 35.0\,\text{W}$ | Error relativo $< 1.8\%$ |
| **Error Absoluto Medio ($MAE$)** | **$13.07\,\text{W}$** | $< 25.0\,\text{W}$ | Alta fidelidad |
| **Tasa de Falsos Positivos en Normal ($FPR$)** | **$0.0\%$** | $< 5.0\%$ | Cero falsas alarmas |
| **Sensibilidad en Desconexión ($Recall$)** | **$100.0\%$** | $\ge 95.0\%$ | Cero fallas omitidas |

---

## 3. MATRIZ DE CONFUSIÓN MULTICLASE (7 × 7)

Evaluada sobre 1,400 muestras independientes (`seed=9999`) — Filas: Valor Real, Columnas: Predicción del Modelo:

```text
                     HOTSPOT  INVERTER  NORMAL  SENSOR_ERR  SHADING  SOILING  STRING_DISC
HOTSPOT                 198         0       0           0        0        2            0
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
| **`SOILING`** (Acumulación de Polvo) | **$99.0\%$** | **$100.0\%$** | **$99.5\%$** | 200 |
| **`STRING_DISCONNECTED`** (Cadena Abierta) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`INVERTER_FAULT`** (Falla de Inversor/Red) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |
| **`HOTSPOT`** (Punto Caliente Térmico) | **$100.0\%$** | **$99.0\%$** | **$99.5\%$** | 200 |
| **`SENSOR_FAULT`** (Falla Instrumental) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 200 |

---

## 5. IMPORTANCIA DE VARIABLES DETERMINANTES (XAI / FEATURE IMPORTANCE)

El bosque de decisión determinó las siguientes contribuciones ponderadas en la inferencia diagnóstica:
1. **Performance Ratio ($PR$):** **$27.1\%$** (Determina de forma primordial si la planta rinde según su potencial ambiental).
2. **Voltaje DC ($V_{\text{dc}}$):** **$22.4\%$** (Discrimina entre inversor abierto $V_{\text{oc}}$, caída por diodos bypass en sombreado y operación nominal).
3. **Delta de Potencia ($\Delta P$):** **$15.5\%$** (Magnitud absoluta del déficit energético en Vatios).
4. **Temperatura de Panel ($T_{\text{panel}}$):** **$13.7\%$** (Aísla puntos calientes térmicos y compensación térmica).
5. **Irradiancia Solar Incidente ($G$):** **$8.3\%$** (Establece el techo solar disponible).
6. **Potencia DC Medida ($P_{\text{dc}}$):** **$7.1\%$**.
7. **Corriente DC Medida ($I_{\text{dc}}$):** **$5.8\%$**.

---

## 6. CONCLUSIÓN TÉCNICA
El entrenamiento ampliado a $10,500$ muestras con validación cruzada *5-Fold* y evaluación *Holdout* independiente (`seed=9999`) confirma una capacidad de generalización sobresaliente ($99.86\%$ de exactitud global y $0.0\%$ de falsos positivos en operación nominal), manteniendo la trazabilidad explicable (XAI) para soporte a decisiones de mantenimiento en terreno.
