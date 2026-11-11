-- ==============================================================================
-- SISTEMA FOTOVOLTAICO INTELIGENTE (STV) - ESQUEMA DE BASE DE DATOS
-- Motor: PostgreSQL 16+ con Extensión TimescaleDB
-- ==============================================================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- ------------------------------------------------------------------------------
-- 1. TABLAS MAESTRAS (MULTI-TENANT & GESTIÓN RELACIONAL)
-- ------------------------------------------------------------------------------

-- Empresas u organizaciones (SaaS Multi-tenant)
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(150) NOT NULL,
    tax_id VARCHAR(50) UNIQUE,
    contact_email VARCHAR(150) NOT NULL,
    contact_phone VARCHAR(50),
    subscription_plan VARCHAR(30) DEFAULT 'pro', -- 'basic', 'pro', 'enterprise'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Usuarios del sistema
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'viewer', -- 'superadmin', 'company_admin', 'om_engineer', 'field_tech', 'viewer'
    phone_number VARCHAR(50),
    telegram_chat_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Plantas Solares Fotovoltaicas
CREATE TABLE IF NOT EXISTS solar_plants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    installed_capacity_kw NUMERIC(10,2) NOT NULL,
    tilt_angle NUMERIC(5,2) DEFAULT 10.0,
    azimuth_angle NUMERIC(5,2) DEFAULT 180.0,
    elevation_masl NUMERIC(6,1) DEFAULT 1500.0,
    temp_coefficient_power NUMERIC(6,4) DEFAULT -0.0038, -- -0.38%/°C
    inverter_nominal_efficiency NUMERIC(5,4) DEFAULT 0.9750, -- 97.5%
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Inversores Solares
CREATE TABLE IF NOT EXISTS inverters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES solar_plants(id) ON DELETE CASCADE,
    brand VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    serial_number VARCHAR(100) UNIQUE,
    nominal_power_kw NUMERIC(10,2) NOT NULL,
    max_dc_voltage NUMERIC(8,2) DEFAULT 1000.0,
    mppt_count INT DEFAULT 2,
    modbus_slave_id INT DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cadenas de Módulos (Strings Fotovoltaicos)
CREATE TABLE IF NOT EXISTS solar_strings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES solar_plants(id) ON DELETE CASCADE,
    inverter_id UUID REFERENCES inverters(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    panel_count INT NOT NULL DEFAULT 10,
    panel_model VARCHAR(100) DEFAULT 'Tier-1 Mono PERC 550W',
    string_nominal_power_w NUMERIC(10,2) NOT NULL,
    voc_stc NUMERIC(8,2) NOT NULL, -- Tensión de circuito abierto STC
    isc_stc NUMERIC(8,2) NOT NULL, -- Corriente de cortocircuito STC
    vmp_stc NUMERIC(8,2) NOT NULL, -- Tensión de máxima potencia STC
    imp_stc NUMERIC(8,2) NOT NULL  -- Corriente de máxima potencia STC
);

-- Dispositivos IoT / Gateways de Campo
CREATE TABLE IF NOT EXISTS iot_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID REFERENCES solar_plants(id) ON DELETE SET NULL,
    hardware_uid VARCHAR(100) UNIQUE NOT NULL,
    device_type VARCHAR(50) DEFAULT 'ESP32-S3',
    firmware_version VARCHAR(50) DEFAULT '1.0.0',
    api_key_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'offline', -- 'online', 'offline', 'warning'
    last_seen TIMESTAMPTZ,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. HIPERTABLAS TIMESCALEDB (SERIES TEMPORALES DE ALTO RENDIMIENTO)
-- ------------------------------------------------------------------------------

-- Tabla de Telemetría Eléctrica y Ambiental
CREATE TABLE IF NOT EXISTS plant_telemetry (
    time TIMESTAMPTZ NOT NULL,
    plant_id UUID NOT NULL,
    device_id UUID NOT NULL,
    string_id UUID,
    
    -- Magnitudes Eléctricas DC (Generador)
    v_dc NUMERIC(8,2),         -- Tensión en voltios
    i_dc NUMERIC(8,2),         -- Corriente en amperios
    p_dc NUMERIC(10,2),        -- Potencia en vatios
    
    -- Magnitudes Eléctricas AC (Salida Inversor)
    v_ac NUMERIC(8,2),
    i_ac NUMERIC(8,2),
    p_ac NUMERIC(10,2),
    frequency NUMERIC(5,2),
    power_factor NUMERIC(4,3),
    
    -- Magnitudes Meteorológicas / Ambientales
    g_irradiance NUMERIC(8,2), -- Irradiancia solar (W/m²)
    t_panel NUMERIC(6,2),      -- Temperatura del panel (°C)
    t_ambient NUMERIC(6,2),    -- Temperatura ambiente (°C)
    rh_ambient NUMERIC(6,2),   -- Humedad relativa (%)
    
    -- Métricas de rendimiento calculadas en el Edge o Ingestion
    p_expected_model NUMERIC(10,2), -- Potencia esperada calculada por modelo físico (W)
    performance_ratio NUMERIC(6,4)  -- Ratio instantáneo P_actual / P_expected
);

-- Convertir a Hipertabla de TimescaleDB particionada por chunks de 7 días
SELECT create_hypertable('plant_telemetry', 'time', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);

-- Índices optimizados para consultas de series temporales
CREATE INDEX IF NOT EXISTS idx_telemetry_plant_time ON plant_telemetry (plant_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time ON plant_telemetry (device_id, time DESC);

-- Habilitar Compresión Columnar de TimescaleDB para datos con más de 14 días
ALTER TABLE plant_telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'plant_id, device_id',
    timescaledb.compress_orderby = 'time DESC'
);

SELECT add_compression_policy('plant_telemetry', INTERVAL '14 days', if_not_exists => TRUE);

-- Política de retención automática (e.g., retener datos brutos por 1 año)
SELECT add_retention_policy('plant_telemetry', INTERVAL '365 days', if_not_exists => TRUE);

-- ------------------------------------------------------------------------------
-- 3. DIAGNÓSTICOS, ALERTAS Y MANTENIMIENTO
-- ------------------------------------------------------------------------------

-- Diagnósticos y Anomalías de Inteligencia Artificial
CREATE TABLE IF NOT EXISTS ai_diagnostics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES solar_plants(id) ON DELETE CASCADE,
    device_id UUID REFERENCES iot_devices(id),
    timestamp TIMESTAMPTZ NOT NULL,
    anomaly_detected BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_score NUMERIC(6,4), -- Score de Isolation Forest o error MSE del Autoencoder
    fault_category VARCHAR(100) NOT NULL, -- 'NORMAL', 'SHADING', 'SOILING', 'STRING_DISCONNECTED', 'INVERTER_FAULT', 'HOTSPOT', 'SENSOR_FAULT'
    confidence_level NUMERIC(5,4) NOT NULL, -- Nivel de certeza (ej. 0.8850)
    p_expected NUMERIC(10,2) NOT NULL,
    p_actual NUMERIC(10,2) NOT NULL,
    delta_power NUMERIC(10,2) NOT NULL,
    loss_percentage NUMERIC(6,2) NOT NULL,
    features_importance JSONB, -- Factores explicativos de la decisión (XAI)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ai_diagnostics_plant_time ON ai_diagnostics (plant_id, timestamp DESC);

-- Sistema de Alertas Notificables
CREATE TABLE IF NOT EXISTS system_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES solar_plants(id) ON DELETE CASCADE,
    diagnostic_id UUID REFERENCES ai_diagnostics(id) ON DELETE SET NULL,
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical'
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    evidence_metrics JSONB NOT NULL,
    status VARCHAR(30) DEFAULT 'pending', -- 'pending', 'acknowledged', 'in_progress', 'resolved', 'dismissed'
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_plant_status ON system_alerts (plant_id, status);

-- Bitácora de Intervenciones y Mantenimiento
CREATE TABLE IF NOT EXISTS maintenance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plant_id UUID NOT NULL REFERENCES solar_plants(id) ON DELETE CASCADE,
    alert_id UUID REFERENCES system_alerts(id),
    technician_id UUID NOT NULL REFERENCES users(id),
    maintenance_type VARCHAR(50) NOT NULL, -- 'cleaning', 'inverter_reset', 'string_rewiring', 'fuse_replacement', 'calibration'
    description TEXT NOT NULL,
    parts_replaced TEXT,
    pr_before_maintenance NUMERIC(6,4),
    pr_after_maintenance NUMERIC(6,4),
    performed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
