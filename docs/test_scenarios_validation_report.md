# INFORME DE VALIDACIÓN DE ESCENARIOS DINÁMICOS Y RENDIMIENTO ENERGÉTICO (FASE 8)

---

## 1. OBJETIVO DEL BANCO DE PRUEBAS
Validar la resiliencia algorítmica y el comportamiento del sistema STV sometido a un ciclo de generación diurno completo (48 intervalos horarios de 15 minutos entre las 06:00 y las 18:00), evaluando la capacidad de la Inteligencia Artificial para:
1. Modelar con precisión la curva de cielo despejado.
2. Descartar falsas alarmas ante el paso rápido de nubes mediante el **filtro de histéresis temporal**.
3. Diagnosticar anomalías persistentes severas (sombreado crítico, suciedad y desconexión de cadena).
4. Cuantificar el balance energético diario en kilovatios-hora ($\text{kWh}$) y la pérdida económica asociada en dólares ($\text{USD}$).

---

## 2. METODOLOGÍA MATEMÁTICA

### 2.1. Integración de Energía Eléctrica (Regla de Riemann)
La energía eléctrica acumulada en el día se calcula mediante la integral temporal de la potencia:

$$E = \int_{t_0}^{t_f} P(t) \, dt \approx \sum_{k=1}^{N} \frac{P_k \cdot \Delta t}{1000} \quad [\text{kWh}]$$

- $P_k$: Potencia instantánea muestreada en el intervalo $k$ (Vatios).
- $\Delta t$: Paso de tiempo ($15\,\text{min} = 0.25\,\text{horas}$).

### 2.2. Pérdida Económica Cuantificada
$$\text{Pérdida Financiera (USD)} = (E_{\text{esperada}} - E_{\text{real}}) \times \text{Tarifa Eléctrica} \; \left[\frac{\text{USD}}{\text{kWh}}\right]$$

Para una instalación típica con tarifa industrial de $0.18\,\text{USD/kWh}$.

### 2.3. Algoritmo de Histéresis Temporal contra Falsas Alarmas
Para evitar disparar alertas de pánico y saturar al operador por el paso transitorio de una nube pequeña (evento que dura 1 o 2 ciclos de muestreo):
$$\text{Alerta Despachada} \iff \sum_{i=0}^{M-1} \mathbb{I}(\text{Anomalía}_{t-i}) \ge M \quad (M = 3 \text{ ciclos consecutivos})$$

---

## 3. RESULTADOS DE LOS 5 ESCENARIOS PROBADOS

| Escenario | Horario | Irradiancia ($G$) | Comportamiento Eléctrico | Diagnóstico IA | Alerta Notificada |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Cielo Despejado** | 06:00 – 09:30 | $100\text{--}780\,\text{W/m}^2$ | Potencia real sigue exactamente la curva nominal esperada. $PR \approx 98.5\%$. | `NORMAL` (Certeza: $96\%$) | Ninguna (Operación Óptima) |
| **2. Nube Rápida Transitoria** | 09:45 – 10:00 | Cae de $820$ a $330\,\text{W/m}^2$ | Caída transitoria simultánea en radiación y corriente. Dura solo 1 ciclo. | Transitorio Ambiental | **Bloqueada por Histéresis** (Cero falsas alarmas) |
| **3. Sombra Parcial Persistente (Caso Obligatorio)** | 11:30 – 13:00 | $950\,\text{W/m}^2$ | $P_{\text{real}} = 310\,\text{W}$ frente a $836\,\text{W}$ esperados. Pérdida del $62.9\%$. | `SHADING` (Certeza: $93.3\%$) | **ALERTA CRÍTICA CONFIRMADA** (Despachada a Telegram/Email) |
| **4. Acumulación de Suciedad (Soiling)** | 13:30 – 15:30 | $650\text{--}880\,\text{W/m}^2$ | Reducción homogénea del $22\%$ en corriente con voltaje nominal estable. | `SOILING` (Certeza: $86.5\%$) | **Advertencia de Mantenimiento** (Lavado programable) |
| **5. Desconexión de Cadena** | 16:00 – 17:30 | $200\text{--}520\,\text{W/m}^2$ | Corriente $I = 0.0\,\text{A}$, voltaje sube a circuito abierto $V_{\text{oc}}$. | `STRING_DISCONNECTED` (Certeza: $98.5\%$) | **ALERTA CRÍTICA CONFIRMADA** |

---

## 4. BALANCE ENERGÉTICO Y FINANCIERO CONSOLIDADO (1 kWp)

- **Energía Teórica Esperada:** $5.412\,\text{kWh/día}$
- **Energía Real Generada:** $3.580\,\text{kWh/día}$
- **Energía Perdida por Fallas:** $1.832\,\text{kWh/día}$ (Pérdida neta del **$33.85\%$**)
- **Performance Ratio ($PR$) Diario Global:** **$66.15\%$**
- **Pérdida Financiera Diaria:** **$0.330\,\text{USD/día}$** por cada $1\,\text{kWp}$ instalado.

> [!IMPORTANT]
> **Escalabilidad Comercial del Diagnóstico Predictivo:**  
> En una planta comercial de **$500\,\text{kWp}$**, esta misma tasa de anomalías no detectada a tiempo representaría una pérdida acumulada de **$\$165.00\,\text{USD}$ al día** o más de **$\$4,950\,\text{USD}$ al mes**, justificando con creces la suscripción al servicio SaaS de STV.
