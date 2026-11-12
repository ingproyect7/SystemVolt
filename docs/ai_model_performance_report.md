# INFORME DE RENDIMIENTO ESTADÍSTICO Y VALIDACIÓN ANUAL DE IA (FASE 9)

---

## 1. RESUMEN EJECUTIVO
Este informe documenta la validación estadística temporal (*Out-of-Time*) de los modelos de Inteligencia Artificial de **STV** utilizando **1 año climático real completo (365 días / 8,760 horas de 2025)** descargado de **NASA POWER** para Medellín, Colombia (`6.2442, -75.5812`):

- **Entrenamiento (Días 1–250):** `2025-01-01` al `2025-09-07` (`2,845` horas diurnas reales $\rightarrow$ **`19,915` vectores** en 7 clases; validación cruzada *5-Fold* de **`99.97% ± 0.02%`**).
- **Prueba Ciega Out-of-Time (Días 251–365):** `2025-09-08` al `2025-12-31` (`1,245` horas diurnas reales $\rightarrow$ **`8,715` muestras** no vistas durante el entrenamiento).

---

## 2. MÉTRICAS CLAVE CONSOLIDADAS (DÍAS 251–365)

| Métrica | Valor Obtenido | Meta de Ingeniería | Estado |
| :--- | :--- | :--- | :--- |
| **Exactitud Global (Accuracy)** | **$99.97\%$** | $\ge 85.0\%$ | Cumplido con creces |
| **Validación Cruzada (5-Fold CV en 250d)** | **$99.97\% \pm 0.02\%$** | $\ge 85.0\%$ | Alta generalización |
| **Coeficiente $R^2$ (Predictor de Potencia)** | **$0.9970$** | $\ge 0.980$ | Ajuste excepcional |
| **Error Cuadrático Medio ($RMSE$)** | **$11.78\,\text{W}$** | $< 35.0\,\text{W}$ | Error relativo $< 1.2\%$ |
| **Error Absoluto Medio ($MAE$)** | **$8.48\,\text{W}$** | $< 25.0\,\text{W}$ | Alta fidelidad |
| **Tasa de Falsos Positivos en Normal ($FPR$)** | **$0.08\%$** | $< 5.0\%$ | Casi cero falsas alarmas |
| **Sensibilidad en Desconexión ($Recall$)** | **$100.0\%$** | $\ge 95.0\%$ | Cero fallas omitidas |

---

## 3. MATRIZ DE CONFUSIÓN MULTICLASE (7 × 7)

Evaluada sobre **`8,715` muestras** de los últimos **115 días del año 2025** (`1,245` muestras por categoría) — Filas: Valor Real, Columnas: Predicción:

```text
                     HOTSPOT  INVERTER  NORMAL  SENSOR_ERR  SHADING  SOILING  STRING_DISC
HOTSPOT                1245         0       0           0        0        0            0
INVERTER_FAULT            0      1245       0           0        0        0            0
NORMAL                    0         0    1244           0        0        1            0
SENSOR_FAULT              0         0       0        1245        0        0            0
SHADING                   0         0       0           0     1245        0            0
SOILING                   0         0       0           0        0     1243            2
STRING_DISCONNECTED       0         0       0           0        0        0         1245
```

---

## 4. DESGLOSE DE MÉTRICAS POR CATEGORÍA DE FALLA

| Categoría Operativa | Precisión (Precision) | Sensibilidad (Recall) | F1-Score | Muestras Evaluadas (Support) |
| :--- | :--- | :--- | :--- | :--- |
| **`NORMAL`** (Generación Nominal) | **$100.0\%$** | **$99.9\%$** | **$100.0\%$** | 1,245 |
| **`SHADING`** (Sombreado Parcial) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 1,245 |
| **`SOILING`** (Acumulación de Polvo) | **$99.9\%$** | **$99.8\%$** | **$99.9\%$** | 1,245 |
| **`STRING_DISCONNECTED`** (Cadena Abierta) | **$99.8\%$** | **$100.0\%$** | **$99.9\%$** | 1,245 |
| **`INVERTER_FAULT`** (Falla de Inversor/Red) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 1,245 |
| **`HOTSPOT`** (Punto Caliente Térmico) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 1,245 |
| **`SENSOR_FAULT`** (Falla Instrumental) | **$100.0\%$** | **$100.0\%$** | **$100.0\%$** | 1,245 |

---

## 5. IMPORTANCIA DE VARIABLES DETERMINANTES (XAI / FEATURE IMPORTANCE)

El bosque de decisión determinó las siguientes contribuciones ponderadas sobre los 250 días reales de entrenamiento:
1. **Performance Ratio ($PR$):** **$28.8\%$**
2. **Voltaje DC ($V_{\text{dc}}$):** **$20.7\%$**
3. **Temperatura de Panel ($T_{\text{panel}}$):** **$15.6\%$**
4. **Delta de Potencia ($\Delta P$):** **$13.8\%$**
5. **Irradiancia Solar Incidente ($G$):** **$8.5\%$**
6. **Potencia DC Medida ($P_{\text{dc}}$):** **$6.9\%$**
7. **Corriente DC Medida ($I_{\text{dc}}$):** **$5.7\%$**

---

## 6. CONCLUSIÓN TÉCNICA
Validado mediante partición cronológica estricta (**250 días de entrenamiento** vs. **115 días de prueba fuera de muestra temporal** sobre datos climáticos reales NASA POWER 2025), el sistema mantiene un $R^2 = 0.9970$, exactitud global de $99.97\%$ y tasa de falsos positivos de apenas $0.08\%$ frente a cambios climáticos estacionales del último trimestre del año.
