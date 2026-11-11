# STV: SISTEMA INTELIGENTE DE MONITOREO, DIAGNÓSTICO Y DETECCIÓN DE FALLAS EN SISTEMAS FOTOVOLTAICOS MEDIANTE INTELIGENCIA ARTIFICIAL

---

## 1. DESCRIPCIÓN DEL PROYECTO
**STV** es una plataforma tecnológica ciberfísica e industrial diseñada para la supervisión continua, el análisis predictivo y el diagnóstico prescriptivo de fallas en instalaciones solares fotovoltaicas (desde sistemas residenciales hasta parques solares industriales).

A diferencia de los sistemas SCADA y plataformas de monitoreo convencionales que solo grafican datos históricos y activan alarmas rudimentarias por umbrales fijos, STV integra un **motor híbrido**:
1. **Modelado Físico-Termodinámico (Sandia / IEC 60891):** Determina la curva teórica de máxima transferencia de potencia según la irradiancia incidente y la temperatura de la célula.
2. **Predictor de Generación por Machine Learning (XGBoost / Random Forest):** Modela no-linealidades atmosféricas y del microclima local para estimar la producción esperada.
3. **Detector No Supervisado de Anomalías (Autoencoder / Isolation Forest):** Identifica comportamientos que se alejen de la frontera operativa normal sin necesidad de umbrales rígidos.
4. **Clasificador Causal Multiclase con Explicabilidad (XAI):** Asocia la firma eléctrica (voltaje, corriente, potencia, factor de forma) a fallas físicas como sombreado parcial, suciedad progresiva (*soiling*), desconexión de sub-strings, puntos calientes (*hotspots*) o anomalías en el inversor.

---

## 2. ESTRUCTURA DEL REPOSITORIO
```
STV/
├── docs/                      # Especificación técnica, diagramas y esquema de base de datos
│   ├── architecture_spec.md   # Especificación de requisitos y diseño de interfaces
│   └── database_schema.sql    # DDL PostgreSQL + TimescaleDB (Hipertablas y compresión)
├── firmware/                  # Código C++ para adquisición Edge (ESP32-S3 / PlatformIO)
│   ├── src/                   # Lógica de adquisición, filtrado digital, buffer SD y MQTTS
│   └── include/               # Mapeo de pines aislados y calibración de transductores
├── backend/                   # Core API REST y servicios de ingestión (Python FastAPI)
│   ├── app/
│   │   ├── api/v1/endpoints/  # Endpoints REST: telemetry, plants, alerts, auth
│   │   ├── core/              # Configuración (config.py), seguridad y conexiones a DB
│   │   ├── models/            # Modelos ORM SQLAlchemy para TimescaleDB
│   │   ├── schemas/           # Contratos de datos y validaciones Pydantic v2
│   │   └── services/          # Consumidor MQTT, motor de reglas y despachador de alertas
│   └── requirements.txt       # Dependencias de backend
├── ai_engine/                 # Microservicio analítico y modelos de Machine Learning
│   ├── models/                # Modelos exportados (.joblib, .pt)
│   ├── pipelines/             # Pipeline de inferencia, cálculo Sandia y clasificadores
│   └── datasets/              # Datasets sintéticos e históricos para entrenamiento
├── frontend/                  # Interfaz Web Industrial (React 18 + TypeScript + Vite)
│   └── src/                   # Dashboards, métricas en tiempo real, gráficas ECharts
├── scripts/                   # Herramientas de simulación física y pruebas
│   └── pv_physics_simulator.py# Simulador solar basado en física real con inyección de fallos
├── tests/                     # Suite de pruebas unitarias y de integración
│   └── test_phase1_contracts.py
└── docker-compose.yml         # Orquestación de infraestructura (TimescaleDB, Redis, EMQX)
```

---

## 3. HOJA DE RUTA DE DESARROLLO (10 FASES)
- [x] **FASE 1: Análisis de Requisitos, Contratos y Arquitectura Base** (En ejecución)
- [ ] **FASE 2: Diseño Electrónico, Aislamiento Galvánico y Selección de Sensores**
- [ ] **FASE 3: Firmware Edge ESP32 (FreeRTOS, ADC 16-bit, RTC, Buffer MicroSD y MQTTS)**
- [ ] **FASE 4: Backend FastAPI y Persistencia en TimescaleDB**
- [ ] **FASE 5: Frontend Industrial Web (React, TypeScript, TailwindCSS, ECharts)**
- [ ] **FASE 6: Entrenamiento e Implementación del Pipeline de Inteligencia Artificial**
- [ ] **FASE 7: Integración End-to-End Hardware + Software + IA**
- [ ] **FASE 8: Banco de Pruebas con Telemetría Real y Simulador Físico**
- [ ] **FASE 9: Validación de Detección de Fallas y Matriz de Confusión**
- [ ] **FASE 10: Empaquetado SaaS Comercial y Despliegue en Producción**

---

## 4. GUÍA RÁPIDA DE INICIO
1. Clonar o acceder al directorio del proyecto:
   ```bash
   cd C:\Users\berri\Desktop\STV
   ```
2. Instalar dependencias en el entorno virtual de Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar la validación de contratos de la Fase 1:
   ```bash
   python -m unittest tests/test_phase1_contracts.py
   ```
4. Ejecutar el simulador de generación solar con inyección de anomalías:
   ```bash
   python scripts/pv_physics_simulator.py --output data_sample.json
   ```
