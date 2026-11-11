# ESPECIFICACIÓN TÉCNICA DE REQUISITOS Y ARQUITECTURA DEL SISTEMA STV

---

## 1. REQUISITOS DEL SISTEMA

### 1.1. Requisitos Funcionales (RF)
- **RF-01 (Adquisición Continua):** El sistema debe recopilar mediciones de voltaje DC ($V_{\text{dc}}$), corriente DC ($I_{\text{dc}}$), irradiancia incidente ($G$), temperatura de panel ($T_{\text{cell}}$), temperatura ambiental ($T_{\text{amb}}$) y humedad ($RH$) con una tasa de muestreo de $1\,\text{Hz}$ y empaquetado de telemetría cada $10\text{--}30\,\text{s}$.
- **RF-02 (Aislamiento y Protección Física):** La etapa de adquisición de hardware no debe tener acoplamiento galvánico directo con los conductores de alta tensión DC fotovoltaica. Debe contar con aislamiento superior a $3\,\text{kV}_{\text{RMS}}$.
- **RF-03 (Tolerancia a Pérdida de Enlace):** En caso de desconexión de red (Wi-Fi, Ethernet o 4G), el dispositivo Edge debe almacenar localmente los registros en búfer de memoria no volátil (MicroSD / SPIFFS) con estampa de tiempo de hardware (RTC) y sincronizarlos automáticamente al restablecerse el enlace.
- **RF-04 (Cálculo de Potencia Teórica):** El sistema debe calcular en tiempo real la potencia nominal esperada mediante el modelo analítico de Sandia / IEC 60891 y compararla contra la predicción del modelo de Machine Learning supervisado.
- **RF-05 (Detección de Anomalías No Supervisada):** Debe identificar patrones atípicos multivariables que se desvíen de la frontera operativa normal utilizando un *Autoencoder* o *Isolation Forest*.
- **RF-06 (Clasificación Causal de Fallas):** Cuando se confirme una desviación significativa sostenida, el sistema debe estimar la probabilidad de fallas específicas: sombreado parcial, acumulación de suciedad, desconexión de string, punto caliente, fallo de inversor o fallo de sensor.
- **RF-07 (Prevención de Falsas Alarmas por Histéresis):** Una alerta no debe dispararse por eventos transitorios breves (ej. paso puntual de una nube pequeña). El evento debe persistir durante al menos $N$ ciclos consecutivos de telemetría ($N \ge 3$).
- **RF-08 (Despacho de Alertas Multicanal):** Las alertas deben clasificarse en tres niveles de severidad (`info`, `warning`, `critical`) y notificarse a través del dashboard web, correo electrónico y bot de mensajería (Telegram).
- **RF-09 (Registro y Trazabilidad de Mantenimiento):** La plataforma debe permitir registrar intervenciones de mantenimiento y comparar la curva de rendimiento antes y después de la intervención.
- **RF-10 (Arquitectura Multi-tenant SaaS):** El sistema debe soportar múltiples empresas u organizaciones, donde cada cliente administra sus propias plantas solares, dispositivos y usuarios con control de acceso basado en roles (RBAC).

### 1.2. Requisitos No Funcionales (RNF)
- **RNF-01 (Rendimiento de Ingestión):** El backend debe ser capaz de procesar hasta $10,000$ mensajes de telemetría por segundo utilizando colas en memoria Redis y FastAPI asíncrono.
- **RNF-02 (Eficiencia de Almacenamiento):** La base de datos debe implementar compresión columnar en hipertablas de series temporales (TimescaleDB) reduciendo el uso de disco en al menos un $80\%$.
- **RNF-03 (Seguridad en Tránsito y Reposo):** Toda la comunicación Edge-to-Cloud debe emplear TLS 1.3 (MQTTS y HTTPS). Las contraseñas de usuarios deben protegerse con hash `bcrypt` o `argon2id` y los dispositivos deben autenticarse mediante API Keys criptográficas.
- **RNF-04 (Explicabilidad de IA - XAI):** Cada diagnóstico generado por el motor de IA debe incluir las variables determinantes (valores SHAP o diferencias de vector) que sustentan la recomendación entregada al operador.

---

## 2. DICCIONARIO DE FALLAS Y FIRMAS ELÉCTRICAS

| Código de Falla | Denominación | Patrón Eléctrico / Síntomas | Acciones Prescriptivas Recomendadas |
| :--- | :--- | :--- | :--- |
| **FAULT-SHADE** | Sombreado Parcial | $G > 400\,\text{W/m}^2$, $P_{\text{real}} \ll P_{\text{esp}}$. Corriente $I_{\text{dc}}$ disminuye de forma escalonada. $V_{\text{dc}}$ se reduce ligeramente por diodos de bypass activos. | Inspeccionar obstáculos físicos (árboles, postes, estructuras nuevas) o suciedad extrema localizada en un cuadrante. |
| **FAULT-SOIL** | Suciedad / Polvo (*Soiling*) | Descenso suave y monotónico del Performance Ratio ($PR$) a lo largo de días/semanas. Afecta principalmente a $I_{\text{dc}}$ sin alterar $V_{\text{dc}}$ en circuito abierto. | Programar lavado de paneles fotovoltaicos en horas de baja radiación (amanecer/atardecer). |
| **FAULT-STRING-DISC** | Desconexión de String | La corriente $I_{\text{dc}}$ cae abruptamente a $0\,\text{A}$ (o a la mitad si hay 2 strings en paralelo). El voltaje $V_{\text{dc}}$ se eleva a nivel de circuito abierto ($V_{\text{oc}}$). | Verificar fusibles gPV en la caja de combinación (*string box*), cables DC y conectores MC4. |
| **FAULT-HOTSPOT** | Punto Caliente Térmico | Caída leve de potencia ($5\text{--}15\%$) con gradiente de temperatura anómalo ($\Delta T > 15\,^\circ\text{C}$) en una zona del arreglo. | Realizar inspección termográfica con cámara IR. Comprobar soldaduras de interconexión y células agrietadas. |
| **FAULT-INV-OFF** | Fallo de Inversor / Red | $V_{\text{dc}}$ permanece en $V_{\text{oc}}$, corriente $I_{\text{dc}} = 0\,\text{A}$ con radiación alta. Inversor sin inyección AC. | Verificar protecciones AC de red, magnetotérmico del inversor, sobretemperatura en el disipador del inversor. |
| **FAULT-SENSOR-ERR** | Anomalía en Sensor | Mediciones físicamente inconsistentes (ej. $G = 0\,\text{W/m}^2$ a las 12:00 con producción activa, o $T > 110\,^\circ\text{C}$). | Revisar cableado de señal, bus I2C/RS-485 y calibración del piranómetro o sonda PT100. |
| **FAULT-DEGRADATION** | Degradación Celular / PID | Pérdida acumulada del factor de forma ($FF$) y potencia nominal a lo largo de meses/años, descartando suciedad y sombras. | Evaluar pruebas de electroluminiscencia (EL) y resistencia de aislamiento para descartar degradación inducida por potencial (PID). |

---

## 3. MODELO DE SEGURIDAD Y CONTROL DE ACCESO (RBAC)

1. **Super Administrador (Root):** Gestión de la plataforma multi-tenant, auditoría global y aprovisionamiento de empresas.
2. **Administrador de Empresa (Company Admin):** Gestión de plantas solares de su organización, gestión de usuarios técnicos y configuración de tarifas energéticas.
3. **Ingeniero de Operación y Mantenimiento (O&M Engineer):** Visualización de telemetría completa, recepción de alertas críticas, gestión de intervenciones de mantenimiento y descarga de reportes técnicos.
4. **Técnico de Campo (Field Tech):** Cierre de órdenes de trabajo de mantenimiento y confirmación de resolución de alertas físicas en terreno.
5. **Observador / Cliente Final (Viewer):** Vista de alto nivel con generación acumulada, ahorro económico en moneda local y estado general del sistema (sin acceso a configuraciones críticas).
