# PLAN DE NEGOCIO SAAS Y ESTRATEGIA DE COMERCIALIZACIÓN (FASE 10)

---

## 1. PROPUESTA DE VALOR Y DIFERENCIACIÓN COMPETITIVA

Las plataformas de monitoreo convencionales del mercado (Huawei FusionSolar, SolarEdge Monitoring, Enphase Enlighten, SMA Sunny Portal) son **sistemas pasivos y propietarios**:
- Se limitan a graficar la producción pasada.
- Disparan alarmas rudimentarias por umbrales fijos o códigos de error genéricos del inversor.
- Amarran al cliente a inversores de una sola marca (ecosistema cerrado).
- No distinguen entre suciedad, sombreado o degradación.

### ¿Por qué STV es una Solución Superior y Comercializable?
1. **Multi-marca e Interoperable (Hardware Agnostic):** Se conecta a inversores de cualquier fabricante mediante el protocolo abierto **Modbus SunSpec** o mediante su propio **Gateway IoT Aislado** de bajo costo.
2. **Diagnóstico Predictivo Basado en IA:** No solo dice *"la planta está produciendo menos"*, sino que especifica: *"Existe una pérdida del 62.9% con 93.3% de probabilidad de sombreado parcial en el String 01; revise los diodos de bypass y la hilera este"*.
3. **Cuantificación Financiera en Tiempo Real:** Traduce las pérdidas técnicas directamente a dinero perdido ($\text{USD}$ o moneda local) según la tarifa del cliente, justificando las órdenes de mantenimiento preventivo.
4. **Optimización del Mantenimiento (Módulo Prescriptivo):** Determina cuándo es económicamente rentable lavar los paneles solares, evitando limpiezas prematuras o retrasos que degraden el retorno de inversión.

---

## 2. PÚBLICO OBJETIVO Y SEGMENTOS DE CLIENTES

| Segmento | Necesidad Principal | Propuesta de Solución STV |
| :--- | :--- | :--- |
| **Instaladores y Empresas EPC** | Reducir costos de cuadrillas de posventa y garantías. | Panel multi-cliente para gestionar todas sus plantas instaladas desde un solo lugar. |
| **Industrias y Fábricas** | Maximizar el autoconsumo y auditar el ahorro prometido por la solar. | Reportes de cumplimiento de PPA y detección inmediata de desconexiones de strings. |
| **Sector Agropecuario y Fincas** | Instalaciones aisladas en zonas remotas de difícil acceso. | Monitoreo 4G con buffer offline (Store & Forward) y alertas por Telegram/WhatsApp. |
| **Parques Solares Utility (> 1 MWp)** | Minimizar pérdidas de Performance Ratio (PR) y penalizaciones de red. | Integración Modbus de alta velocidad, modelos de IA personalizados y SLA 99.9%. |

---

## 3. MODELO DE SUSCRIPCIÓN SAAS (TIERS DE PRECIOS)

```
┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐
│       PLAN RESIDENCIAL       │      PLAN COMERCIAL PYME     │    PLAN INDUSTRIAL UTILITY   │
│         $9.99 USD / mes      │        $49.00 USD / mes      │    $0.20 USD / kWp / mes     │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤
│ • Instalaciones < 15 kWp     │ • Instalaciones 15 a 150 kWp │ • Parques > 150 kWp          │
│ • Telemetría cada 1 minuto   │ • Telemetría cada 10 seg     │ • Telemetría a 1 Hz          │
│ • Diagnóstico básico de IA   │ • Diagnóstico IA completo    │ • Reentrenamiento de IA in situ│
│ • Alertas por Email / Telegram│ • Alertas multicanal completas│ • API REST dedicada y SCADA  │
│ • 1 usuario observador       │ • Hasta 5 usuarios (RBAC)    │ • Usuarios ilimitados + SLA  │
│ • Historial de 6 meses       │ • Historial de 3 años        │ • Historial permanente       │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘
```

---

## 4. ESTRUCTURA DE COSTOS Y MARGEN OPERATIVO (UNIT ECONOMICS)

Para una cartera administrada de **100 plantas comerciales medianas (promedio 50 kWp c/u)**:

### Ingresos Recurrentes (MRR):
- $100 \times \$49.00\,\text{USD} = \mathbf{\$4,900.00\,\text{USD / mes}}$ ($\$58,800\,\text{USD / año}$).

### Costos Operativos de Infraestructura Cloud:
- Servidor Cloud VPS (PostgreSQL + TimescaleDB + FastAPI): $\$80.00\,\text{USD / mes}$.
- Clúster Redis y Broker EMQX gestionado: $\$45.00\,\text{USD / mes}$.
- Almacenamiento S3 para respaldos de base de datos: $\$15.00\,\text{USD / mes}$.
- Tráfico de datos y Notificaciones (Telegram API es gratuito, Email transaccional): $\$20.00\,\text{USD / mes}$.
- **Costo Total de Infraestructura:** $\mathbf{\$160.00\,\text{USD / mes}}$.

### Margen Bruto del Software:
$$\text{Margen Bruto} = \frac{4900 - 160}{4900} \times 100 = \mathbf{96.73\%}$$

---

## 5. HARDWARE Y VENTA INICIAL (OPTIONAL ADD-ON)
Para clientes que no cuentan con inversores inteligentes o requieren telemetría de radiación en el plano:
- **Costo de fabricación del Gateway ESP32 aislado (BOM):** $\approx \$115.00\,\text{USD}$.
- **Precio de venta al público del Gateway (Hardware Plug & Play):** $\mathbf{\$249.00\,\text{USD}}$ (Margen de hardware del $53.8\%$).
