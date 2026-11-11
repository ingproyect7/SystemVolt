"""
Modelos ORM de SQLAlchemy para el esquema relacional y series temporales STV.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Float, Integer, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False)
    tax_id = Column(String(50), unique=True, nullable=True)
    contact_email = Column(String(150), nullable=False)
    subscription_plan = Column(String(30), default="pro")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    solar_plants = relationship("SolarPlant", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(30), default="viewer")
    phone_number = Column(String(50), nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="users")


class SolarPlant(Base):
    __tablename__ = "solar_plants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    installed_capacity_kw = Column(Float, nullable=False)
    tilt_angle = Column(Float, default=10.0)
    azimuth_angle = Column(Float, default=180.0)
    temp_coefficient_power = Column(Float, default=-0.0038)
    inverter_nominal_efficiency = Column(Float, default=0.9750)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    company = relationship("Company", back_populates="solar_plants")
    inverters = relationship("Inverter", back_populates="plant", cascade="all, delete-orphan")
    iot_devices = relationship("IoTDevice", back_populates="plant")
    telemetry = relationship("PlantTelemetry", back_populates="plant", cascade="all, delete-orphan")
    alerts = relationship("SystemAlert", back_populates="plant", cascade="all, delete-orphan")


class Inverter(Base):
    __tablename__ = "inverters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String(36), ForeignKey("solar_plants.id", ondelete="CASCADE"), nullable=False)
    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=True)
    nominal_power_kw = Column(Float, nullable=False)
    mppt_count = Column(Integer, default=2)

    plant = relationship("SolarPlant", back_populates="inverters")
    strings = relationship("SolarString", back_populates="inverter")


class SolarString(Base):
    __tablename__ = "solar_strings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String(36), ForeignKey("solar_plants.id", ondelete="CASCADE"), nullable=False)
    inverter_id = Column(String(36), ForeignKey("inverters.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)
    panel_count = Column(Integer, default=10)
    panel_model = Column(String(100), default="Tier-1 Mono 550W")
    string_nominal_power_w = Column(Float, nullable=False)

    inverter = relationship("Inverter", back_populates="strings")


class IoTDevice(Base):
    __tablename__ = "iot_devices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String(36), ForeignKey("solar_plants.id", ondelete="SET NULL"), nullable=True)
    hardware_uid = Column(String(100), unique=True, nullable=False, index=True)
    device_type = Column(String(50), default="ESP32-S3")
    firmware_version = Column(String(50), default="1.0.0")
    api_key_hash = Column(String(255), nullable=True)
    status = Column(String(20), default="offline")
    last_seen = Column(DateTime, nullable=True)

    plant = relationship("SolarPlant", back_populates="iot_devices")


class PlantTelemetry(Base):
    __tablename__ = "plant_telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, nullable=False, index=True)
    plant_id = Column(String(36), ForeignKey("solar_plants.id", ondelete="CASCADE"), nullable=False, index=True)
    device_uid = Column(String(100), nullable=False, index=True)
    string_id = Column(String(36), nullable=True)

    # Medición DC
    v_dc = Column(Float, nullable=True)
    i_dc = Column(Float, nullable=True)
    p_dc = Column(Float, nullable=True)

    # Medición AC
    v_ac = Column(Float, nullable=True)
    i_ac = Column(Float, nullable=True)
    p_ac = Column(Float, nullable=True)
    frequency = Column(Float, nullable=True)

    # Variables Ambientales
    g_irradiance = Column(Float, nullable=True)
    t_panel = Column(Float, nullable=True)
    t_ambient = Column(Float, nullable=True)
    rh_ambient = Column(Float, nullable=True)

    # Métricas de Desempeño
    p_expected_model = Column(Float, nullable=True)
    performance_ratio = Column(Float, nullable=True)

    plant = relationship("SolarPlant", back_populates="telemetry")


class AIDiagnostic(Base):
    __tablename__ = "ai_diagnostics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String(36), ForeignKey("solar_plants.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False)
    anomaly_detected = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
    fault_category = Column(String(100), nullable=False)
    confidence_level = Column(Float, nullable=False)
    p_expected = Column(Float, nullable=False)
    p_actual = Column(Float, nullable=False)
    delta_power = Column(Float, nullable=False)
    loss_percentage = Column(Float, nullable=False)
    features_importance = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SystemAlert(Base):
    __tablename__ = "system_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String(36), ForeignKey("solar_plants.id", ondelete="CASCADE"), nullable=False, index=True)
    diagnostic_id = Column(String(36), ForeignKey("ai_diagnostics.id", ondelete="SET NULL"), nullable=True)
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'critical'
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    evidence_metrics = Column(JSON, nullable=False)
    status = Column(String(30), default="pending")  # 'pending', 'acknowledged', 'resolved'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    plant = relationship("SolarPlant", back_populates="alerts")


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plant_id = Column(String(36), ForeignKey("solar_plants.id", ondelete="CASCADE"), nullable=False)
    alert_id = Column(String(36), ForeignKey("system_alerts.id"), nullable=True)
    technician_name = Column(String(150), nullable=False)
    maintenance_type = Column(String(50), nullable=False)  # 'cleaning', 'rewiring', 'fuse_replacement'
    description = Column(Text, nullable=False)
    pr_before_maintenance = Column(Float, nullable=True)
    pr_after_maintenance = Column(Float, nullable=True)
    performed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
