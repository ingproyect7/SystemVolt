"""
Esquemas Pydantic v2 para validación y deserialización de telemetría IoT.
Aplica validaciones de coherencia física para evitar datos corruptos.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ElectricalDC(BaseModel):
    v_dc: float = Field(..., ge=0.0, le=1500.0, description="Voltaje DC del arreglo o string (V)")
    i_dc: float = Field(..., ge=0.0, le=200.0, description="Corriente DC (A)")
    p_dc: Optional[float] = Field(None, ge=0.0, description="Potencia DC calculada (W)")

    @field_validator("p_dc", mode="before")
    def calculate_power_if_missing(cls, v, values):
        return v


class ElectricalAC(BaseModel):
    v_ac: Optional[float] = Field(None, ge=0.0, le=600.0, description="Voltaje AC de red (V)")
    i_ac: Optional[float] = Field(None, ge=0.0, le=300.0, description="Corriente AC de inyección (A)")
    p_ac: Optional[float] = Field(None, ge=0.0, description="Potencia activa AC (W)")
    frequency: Optional[float] = Field(None, ge=45.0, le=65.0, description="Frecuencia de red (Hz)")
    power_factor: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Factor de potencia")


class EnvironmentalMetrics(BaseModel):
    g_irradiance: float = Field(..., ge=0.0, le=1800.0, description="Irradiancia solar en el plano (W/m²)")
    t_panel: float = Field(..., ge=-20.0, le=120.0, description="Temperatura de célula/panel (°C)")
    t_ambient: Optional[float] = Field(None, ge=-20.0, le=60.0, description="Temperatura ambiente (°C)")
    rh_ambient: Optional[float] = Field(None, ge=0.0, le=100.0, description="Humedad relativa ambiente (%)")


class DeviceEdgeStatus(BaseModel):
    wifi_rssi: Optional[int] = Field(None, ge=-110, le=0, description="Nivel de señal Wi-Fi (dBm)")
    buffer_pending_records: Optional[int] = Field(0, ge=0, description="Registros pendientes en buffer SD offline")
    uptime_seconds: Optional[int] = Field(0, ge=0, description="Tiempo de actividad del microcontrolador (s)")


class TelemetryIngestPayload(BaseModel):
    """
    Contrato estándar del paquete JSON transmitido por los gateways IoT vía MQTT o HTTP.
    """
    device_uid: str = Field(..., min_length=4, max_length=100, description="Identificador único de hardware del gateway")
    plant_id: UUID = Field(..., description="UUID de la planta solar")
    string_id: Optional[UUID] = Field(None, description="UUID del string monitoreado (opcional si es nivel inversor)")
    timestamp: datetime = Field(..., description="Estampa de tiempo UTC o con zona horaria ISO 8601")
    
    dc: ElectricalDC
    ac: Optional[ElectricalAC] = None
    env: EnvironmentalMetrics
    status: Optional[DeviceEdgeStatus] = None

    def calculate_instantaneous_power(self) -> float:
        """Calcula o valida la potencia DC: P = V * I"""
        calculated = round(self.dc.v_dc * self.dc.i_dc, 2)
        if self.dc.p_dc is None:
            self.dc.p_dc = calculated
        return self.dc.p_dc


class TelemetryBatchIngestPayload(BaseModel):
    """
    Payload para recepción masiva (batch) al recuperar conectividad tras modo Store-and-Forward.
    """
    device_uid: str
    plant_id: UUID
    records: list[TelemetryIngestPayload]
