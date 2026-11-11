# ESPECIFICACIÓN DE DISEÑO ELECTRÓNICO, AISLAMIENTO GALVÁNICO Y SENSORES (FASE 2)

---

## 1. COMPARATIVA DE HARDWARE DE ADQUISICIÓN Y CONTROL

Para fundamentar la selección técnica bajo criterios de ingeniería de sistemas, electrónica y costos, se evalúan las 5 alternativas requeridas:

| Plataforma | Ventajas | Desventajas | Costo Unitario Aprox. | Veredicto STV |
| :--- | :--- | :--- | :--- | :--- |
| **ESP32-S3 / ESP32** | • Microcontrolador Dual-Core 240 MHz con Wi-Fi y BLE nativo.<br>• Soporte de FreeRTOS multi-hilo para adquisición y comunicación simultánea.<br>• Ultra bajo consumo ($< 150\,\text{mA}$).<br>• Capacidad de buffer offline en Flash SPIFFS y MicroSD. | • ADC interno de 12 bits ruidoso y no lineal (requiere obligatoriamente ADC externo como ADS1115).<br>• Requiere placa de circuito impreso (PCB) con diseño propio de fuentes y protecciones. | **$4 – $7 USD** | **MEJOR ALTERNATIVA PARA PROTOTIPO UNIVERSITARIO Y GATEWAY EDGE COMERCIAL DE BAJO COSTO.** |
| **Arduino (Uno / Mega / Nano)** | • Facilidad de programación educativa.<br>• Gran disponibilidad de librerías para sensores básicos. | • Microcontrolador de 8 bits a 16 MHz muy limitado en memoria SRAM (2 KB).<br>• Sin conectividad de red nativa (requiere módulos Ethernet W5100 o Wi-Fi ESP8266 externos poco confiables).<br>• Incapaz de procesar pilas TLS/HTTPS ni criptografía moderna. | **$5 – $15 USD** | **DESCARTADO.** No apto para telemetría segura en tiempo real ni buffering industrial. |
| **Raspberry Pi (4 / 5 / CM4)** | • Sistema operativo Linux completo (permite correr Python, Docker, base de datos local).<br>• Gran potencia de cómputo para procesar modelos de IA ligeros directamente en el Edge. | • Alto consumo energético (5W – 15W), sensible a apagones intempestivos (corrupción frecuente de tarjeta MicroSD).<br>• No posee entradas analógicas (ADC) nativas.<br>• Costo elevado y sobredimensionado para simple adquisición. | **$45 – $85 USD** | **RESERVADO para subestaciones medianas** como Concentrador Local de múltiples plantas, no para nodos de string individuales. |
| **PLC Industrial (Siemens S7-1200 / Schneider M221)** | • Máxima robustez industrial y certificaciones EMC/IEC.<br>• Fuentes redundantes, entradas analógicas 4-20mA y 0-10V nativas aisladas.<br>• Vida útil $> 10$ años en entornos severos. | • Costo muy elevado.<br>• Programación en lenguajes IEC 61131-3 (Ladder, ST) que dificulta la integración directa con brokers MQTT, TLS y nubes modernas.<br>• Requiere gateways IoT adicionales para comunicación JSON/Cloud. | **$250 – $600 USD** | **RECOMENDABLE PARA VERSIÓN COMERCIAL EN PARQUES SOLARES UTILITY-SCALE (> 1 MWp).** |
| **Monitoreo Integrado en Inversor (Modbus SunSpec)** | • Cero costo de sensores de potencia adicionales.<br>• Lee voltajes, corrientes y potencias internas de cada MPPT con precisión calibrada de fábrica.<br>• No altera la garantía de la instalación eléctrica. | • Depende de que el inversor esté energizado y conectado a red.<br>• No mide irradiancia solar ni temperatura de módulos (requiere estación meteorológica externa auxiliar).<br>• Tasa de actualización típicamente limitada por el firmware del inversor (cada 5 a 60 segundos). | **$0 USD (ya integrado en el inversor)** | **SOLUCIÓN PRINCIPAL PARA INSTALACIONES COMERCIALES EXISTENTES.** Se combina con un gateway ESP32 que solo añade los sensores ambientales. |

---

## 2. COMPARATIVA DE PROTOCOLOS DE COMUNICACIÓN

| Protocolo | Capa OSI | Ventajas | Desventajas | Veredicto STV |
| :--- | :--- | :--- | :--- | :--- |
| **MQTT sobre TLS (MQTTS - 8883)** | Aplicación / Transporte | • Protocolo pub/sub ultraligero y asíncrono.<br>• Bajo ancho de banda (header de solo 2 bytes).<br>• Mecanismos QoS (1 y 2) para asegurar entrega.<br>• *Last Will and Testament (LWT)* para detectar desconexión instantánea del gateway. | • Requiere broker centralizado (EMQX / Mosquitto). | **PROTOCOLO PRINCIPAL PARA TELEMETRÍA Y ALERTAS EN TIEMPO REAL.** |
| **HTTPS REST** | Aplicación | • Universal, fácil de atravesar firewalls corporativos.<br>• Ideal para intercambio de archivos grandes y peticiones atómicas (aprovisionamiento, actualización OTA). | • Sobrecarga de encabezados HTTP (centenares de bytes por paquete).<br>• Basado en petición-respuesta (no apto para streaming continuo de alta frecuencia). | **USADO PARA APROVISIONAMIENTO INICIAL Y VACIADO BATCH DEL BUFFER STORE-AND-FORWARD.** |
| **RS-485 / Modbus RTU** | Físico / Enlace | • Estándar industrial por excelencia.<br>• Bus diferencial balanceado inmune a ruido electromagnético de inversores.<br>• Distancias de cableado de hasta 1200 metros con topología en bus (hasta 32 dispositivos). | • Protocolo maestro-esclavo cableado (no inalámbrico).<br>• Sin cifrado nativo en la línea física. | **USADO PARA LA LECTURA FÍSICA DEL INVERSOR Y DEL PIRANÓMETRO METEOROLÓGICO.** |
| **Modbus TCP** | Aplicación / Ethernet | • Mismo mapa de registros que Modbus RTU pero sobre Ethernet/IP.<br>• Muy alta velocidad ($100\,\text{Mbps}$). | • Requiere cableado estructurado UTP en campo o switches industriales. | **USADO CUANDO EL INVERSOR TIENE PUERTO ETHERNET DIRECTO A LA RED LOCAL.** |
| **Wi-Fi (802.11 b/g/n)** | Enlace / Físico | • Sin costo de cableado, integrado nativamente en el ESP32.<br>• Facilidad de despliegue en techos residenciales y naves comerciales. | • Alcance limitado ($30\text{--}80\,\text{m}$), susceptible a atenuación por estructuras metálicas de paneles. | **OPCIÓN DE RED PRIMARIA EN PROTOTIPOS Y TECHOS RESIDENCIALES.** |
| **Ethernet Cableado (W5500 / LAN8720)** | Enlace / Físico | • Máxima confiabilidad, cero interferencias de radiofrecuencia. | • Requiere canalización y tendido de cable de red hasta el inversor. | **OPCIÓN DE RED PRIMARIA EN INSTALACIONES INDUSTRIALES.** |

---

## 3. ESQUEMA DE CONEXIONADO Y ACONDICIONAMIENTO ELÉCTRICO

### 3.1. Cadena de Medición de Voltaje DC (Hasta 1000V DC Aislados)

```
[ STRING PV (+) ] ─── [ Fusible gPV 2A / 1000V ] ──┐
                                                   ├── [ Varistor MOV 1000V DC ]
[ STRING PV (-) ] ─────────────────────────────────┴── [ Desconectador DC ]
       │
       ▼
 [ DIVISOR DE PRECISIÓN DE ALTA IMPEDANCIA ]
   R_top = 3 x 330 kΩ (1 MΩ total, 1W metal film 0.1%, resiste 1500V)
   R_bottom = 2.00 kΩ (0.1%, 1/4W)
   Atenuación: V_in_iso = V_string * (2000 / 1002000) = V_string * 0.001996
   * Para V_string = 1000V: V_in_iso = 1.996 V (dentro del rango lineal del AMC1301)
       │
       ▼
 [ AMPLIFICADOR DE AISLAMIENTO GALVÁNICO: TI AMC1301 ]
   • Aislamiento reforzado de 5000 V_RMS (7070 V_pk)
   • Rango de entrada diferencial lineal: ±250 mV (se ajusta R_bottom a 250 Ω para 1000V)
   • Ganancia fija: 8.2x
   • Salida diferencial centrada en VCM = 1.44 V: VOUTP - VOUTN = VIN * 8.2
   • Alimentación del lado de alta tensión (VDD1): Fuente DC-DC aislada (B0505S-1WR3, 5V -> 5V con 3 kV aislamiento)
   • Alimentación del lado de baja tensión (VDD2): 3.3V del ESP32
       │
       ▼
 [ FILTRO PASA-BAJOS RC DIFERENCIAL ANTIALIASING ]
   R = 47 Ω, C_diff = 10 nF, C_comm = 1 nF (Frecuencia de corte ~ 150 kHz para rechazar ruido de conmutación MPPT)
       │
       ▼
 [ ADC EXTERNO ADS1115 (16 BITS - I2C) ]
   • Entrada Diferencial: Canal A0 - A1
   • Configuración PGA: ±2.048 V
   • Resolución: 1 LSB = 62.5 µV
       │ Bus I2C (SDA, SCL) a 400 kHz con pull-ups de 4.7 kΩ
       ▼
 [ ESP32-S3 (GPIO 8: SDA, GPIO 9: SCL) ]
```

---

### 3.2. Cadena de Medición de Corriente DC (Efecto Hall Sin Contacto)

```
[ CABLE DC STRING PV ] ───────► ( Núcleo Hall Aislado: Allegro ACS758LCB-050B ) ───────► [ Hacia Inversor ]
                                 • Aislamiento dieléctrico: 4800 V_RMS entre pines 1-2 y 3-5
                                 • Rango: -50 A a +50 A bidireccional
                                 • Sensibilidad nominal: 40 mV/A
                                 • V_out en reposo (0 A): VCC / 2 = 2.50 V (con VCC = 5V)
                                       │
                                       ▼
                         [ FILTRO PASA-BAJOS RC ]
                         R = 100 Ω, C = 47 nF (fc ~ 33 kHz)
                                       │
                                       ▼
                         [ ADC ADS1115 (16 BITS) ]
                         • Entrada Simple: Canal A2
                         • Configuración PGA: ±4.096 V
                         • Resolución: 1 LSB = 125 µV (permite medir corrientes con resolución de 3.125 mA)
                                       │ Bus I2C
                                       ▼
                         [ ESP32-S3 ]
```

---

### 3.3. Sensores Ambientales e Interfaces Físicas

1. **Irradiancia Solar ($G$):**
   - *Sensor:* Piranómetro / Célula calibrada con salida RS-485 Modbus RTU (Baudrate: 9600 bps, 8N1).
   - *Transceiver RS-485:* Circuito integrado `MAX13487EESA` o `ADM2483` (con aislamiento galvánico de $2.5\,\text{kV}$). Cuenta con control automático de flujo de transmisión (AutoDirection), conectándose a los pines UART2 del ESP32 (GPIO 17: TX, GPIO 18: RX).
2. **Temperatura del Panel ($T_{\text{cell}}$):**
   - *Sensor:* Sonda `PT100` platino clase A de 3 hilos adherida con silicona térmica cerámica y cinta de aluminio reflectante a la parte posterior del módulo solar central.
   - *Acondicionador:* Transmisor digital de precisión `MAX31865` con comunicación SPI (GPIO 10: CS, GPIO 11: MOSI, GPIO 12: MISO, GPIO 13: SCK). Precisión de $\pm 0.05\,^\circ\text{C}$.
   - *Opción económica prototipo:* Sonda sumergible `DS18B20` digital mediante bus 1-Wire (GPIO 4 con resistencia pull-up de $4.7\,\text{k}\Omega$).
3. **Temperatura y Humedad Ambiental ($T_{\text{amb}}$, $RH$):**
   - *Sensor:* `Sensirion SHT31-DIS` o `Bosch BME280` alojado en garita meteorológica de platos ventilada. Conectado al mismo bus $\text{I}^2\text{C}$ (Dirección $0\text{x}44$ o $0\text{x}76$).
4. **Sensor Infrarrojo para Hotspots (Opcional):**
   - *Sensor:* Termómetro infrarrojo sin contacto `MLX90614-DCI` (gradiente de campo visual estrecho de $5^\circ$), apuntando hacia la superficie del panel solar. Bus $\text{I}^2\text{C}$ en dirección $0\text{x}5\text{A}$.
5. **Reloj de Tiempo Real (RTC Hardware):**
   - *Módulo:* `DS3231` con oscilador TCXO compensado por temperatura ($\pm 2\,\text{ppm}$) y batería de litio CR2032. Bus $\text{I}^2\text{C}$ (Dirección $0\text{x}68$).
6. **Almacenamiento Local Offline (Store & Forward):**
   - Módulo MicroSD SPI estándar acoplado con tarjeta SanDisk Industrial MicroSD de 8 GB o 16 GB formateada en FAT32.

---

## 4. LISTA DE MATERIALES (BILL OF MATERIALS - BOM) Y ESTIMACIÓN DE COSTOS

### A. Prototipo Universitario / Banco de Pruebas (1 a 2 Strings, < 600V DC)

| Ítem | Componente / Número de Parte | Fabricante | Descripción Técnica | Cant. | Costo Unitario (USD) | Costo Total (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `ESP32-S3-WROOM-1-N8R8` | Espressif Systems | MCU Dual-Core 240MHz, 8MB Flash, 8MB PSRAM, Wi-Fi/BLE | 1 | $4.50 | $4.50 |
| 2 | `ADS1115IDGSR` | Texas Instruments | ADC 16 bits de ultra precisión, 4 canales, bus I2C | 1 | $2.80 | $2.80 |
| 3 | `AMC1301DWVR` | Texas Instruments | Amplificador de aislamiento reforzado 5 kV RMS | 1 | $4.20 | $4.20 |
| 4 | `B0505S-1WR3` | Mornsun | Convertidor DC-DC aislado 5V a 5V (3 kV aislamiento) | 1 | $2.10 | $2.10 |
| 5 | `ACS758LCB-050B-PFF-T` | Allegro MicroSystems | Sensor de corriente Hall galvanizado bidireccional 50A | 1 | $6.80 | $6.80 |
| 6 | `MAX31865ATP+` + Sonda PT100 | Maxim Integrated / Generic | Acondicionador SPI para RTD PT100 3 hilos clase A | 1 | $5.50 | $5.50 |
| 7 | `SHT31-DIS-B` | Sensirion | Sensor digital de temperatura y humedad I2C de alta precisión | 1 | $3.20 | $3.20 |
| 8 | `DS3231SN#` | Maxim Integrated | RTC de alta precisión con oscilador compensado TCXO | 1 | $2.90 | $2.90 |
| 9 | `MAX13487EESA+` | Maxim Integrated | Transceptor RS-485 half-duplex con AutoDirection | 1 | $2.40 | $2.40 |
| 10 | `Célula Calibrada RS-485` | Seven-Sensor / RK200 | Piranómetro solar calibrado salida RS-485 Modbus RTU | 1 | $45.00 | $45.00 |
| 11 | `Protecciones DC (gPV + SPD)` | Suntree / Schneider | Fusible fotovoltaico 1000V 2A + Varistor SPD DC Clase II | 1 | $12.00 | $12.00 |
| 12 | `PCB a Medida + Componentes Pasivos` | JLCPCB / Varios | Resistores 0.1% 1W, capacitores cerámicos, conectores | 1 | $15.00 | $15.00 |
| 13 | `Caja Enclosure IP65` | Saipwell | Gabinete estanco para intemperie con prensacables PG9 | 1 | $8.50 | $8.50 |
| -- | **TOTAL ESTIMADO PROTOTIPO** | | | | | **~$114.90 USD** |

---

### B. Versión Comercial / Industrial (Instalación MWp con Lectura Modbus de Inversor)

| Ítem | Componente / Equipo | Función | Costo Unitario (USD) |
| :--- | :--- | :--- | :--- |
| 1 | `Advantech WISE-710 / RUT955` | Gateway IoT industrial riel DIN con módem 4G LTE Cat-M1 y RS-485 aislado | $190.00 |
| 2 | `Cable Belden 9841 Blindado` | Bus RS-485 Modbus RTU para conectar hasta 16 inversores en guirnalda | $35.00 |
| 3 | `Piranómetro Secundario Clase B (ISO 9060)` | Medición de radiación global horizontal y en el plano del módulo | $220.00 |
| 4 | `Sensor de Temp. Módulo PT100 DIN` | Sonda industrial RTD para montaje en estructura solar | $38.00 |
| 5 | `Gabinete Riel DIN con Fuente MeanWell 24V` | Alimentación ininterrumpida con respaldo de batería | $65.00 |
| -- | **TOTAL COMERCIAL POR PLANTA** | (Supervisa hasta 500 kWp – 1 MWp por gateway) | **~$548.00 USD** |
