"""
Esquemas Pydantic v2 para diagnósticos del motor de Inteligencia Artificial y Alertas.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class FaultCategory(str, Enum):
    NORMAL = "NORMAL"
    SHADING = "SHADING"                     # Sombreado parcial
    SOILING = "SOILING"                     # Suciedad acumulada
    STRING_DISCONNECTED = "STRING_DISCONNECTED"  # String abierto o fusible fundido
    INVERTER_FAULT = "INVERTER_FAULT"       # Fallo interno o desconexión de red AC
    HOTSPOT = "HOTSPOT"                     # Punto caliente térmico localizado
    SENSOR_FAULT = "SENSOR_FAULT"           # Falla de sensor o cable cortado
    DEGRADATION = "DEGRADATION"             # Degradación a largo plazo / PID


class AlertStatus(str, Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class AIDiagnosticResult(BaseModel):
    """
    Resultado devuelto por el pipeline de IA tras procesar una ventana de telemetría.
    """
    plant_id: UUID
    device_uid: str
    timestamp: datetime
    
    # Detección
    is_anomaly: bool = Field(..., description="Verdadero si el vector se aparta de la frontera normal")
    anomaly_score: float = Field(..., description="Error cuadrático medio o score de aislamiento [-1, 1]")
    
    # Métricas Energéticas
    p_expected: float = Field(..., ge=0.0, description="Potencia teórica calculada (W)")
    p_actual: float = Field(..., ge=0.0, description="Potencia real medida (W)")
    delta_power: float = Field(..., description="Diferencia absoluta P_esp - P_real (W)")
    loss_percentage: float = Field(..., ge=0.0, le=100.0, description="Porcentaje de pérdida respecto a la esperada")
    
    # Clasificación de Falla y Causa Raíz
    fault_category: FaultCategory = Field(..., description="Categoría de falla más probable")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Certeza probabilística del modelo [0.0 a 1.0]")
    root_cause_explanation: str = Field(..., description="Explicación en lenguaje técnico accesible")
    recommended_action: str = Field(..., description="Acción de campo recomendada para el técnico")
    
    # Explicabilidad (XAI)
    features_importance: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Variables con mayor peso en el diagnóstico (SHAP values)"
    )


class SystemAlertCreate(BaseModel):
    plant_id: UUID
    diagnostic_id: Optional[UUID] = None
    severity: AlertSeverity
    title: str = Field(..., max_length=200)
    description: str
    recommended_action: str
    evidence_metrics: Dict[str, Any]


class SystemAlertResponse(SystemAlertCreate):
    id: UUID
    status: AlertStatus
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
