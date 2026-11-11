"""
Endpoints REST para la gestión de Plantas Solares Fotovoltaicas.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.entities import SolarPlant, PlantTelemetry, SystemAlert, Company

router = APIRouter()


class SolarPlantCreate(BaseModel):
    company_id: Optional[str] = None
    name: str = Field(..., max_length=150)
    code: str = Field(..., max_length=50)
    latitude: float
    longitude: float
    installed_capacity_kw: float = Field(..., gt=0.0)
    tilt_angle: Optional[float] = 10.0
    azimuth_angle: Optional[float] = 180.0
    temp_coefficient_power: Optional[float] = -0.0038
    inverter_nominal_efficiency: Optional[float] = 0.9750


class SolarPlantResponse(SolarPlantCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=SolarPlantResponse, status_code=status.HTTP_201_CREATED)
def create_solar_plant(plant_in: SolarPlantCreate, db: Session = Depends(get_db)):
    """Registra una nueva planta fotovoltaica en la plataforma."""
    # Si no se suministra company_id, se asocia a una empresa por defecto o se crea una
    company_id = plant_in.company_id
    if not company_id:
        default_company = db.query(Company).first()
        if not default_company:
            default_company = Company(
                name="Energías Solares de Colombia SAS",
                contact_email="soporte@energiasolar.co"
            )
            db.add(default_company)
            db.commit()
            db.refresh(default_company)
        company_id = default_company.id

    existing = db.query(SolarPlant).filter(SolarPlant.code == plant_in.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una planta registrada con ese código.")

    plant = SolarPlant(
        company_id=company_id,
        name=plant_in.name,
        code=plant_in.code,
        latitude=plant_in.latitude,
        longitude=plant_in.longitude,
        installed_capacity_kw=plant_in.installed_capacity_kw,
        tilt_angle=plant_in.tilt_angle,
        azimuth_angle=plant_in.azimuth_angle,
        temp_coefficient_power=plant_in.temp_coefficient_power,
        inverter_nominal_efficiency=plant_in.inverter_nominal_efficiency
    )
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


@router.get("/", response_model=List[SolarPlantResponse])
def list_solar_plants(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Lista las plantas solares registradas."""
    return db.query(SolarPlant).offset(skip).limit(limit).all()


@router.get("/{plant_id}", response_model=SolarPlantResponse)
def get_solar_plant(plant_id: str, db: Session = Depends(get_db)):
    """Obtiene los detalles de una planta solar específica."""
    plant = db.query(SolarPlant).filter(SolarPlant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Planta solar no encontrada.")
    return plant


@router.get("/{plant_id}/summary")
def get_plant_realtime_summary(plant_id: str, db: Session = Depends(get_db)):
    """Retorna un resumen de monitoreo en tiempo real: última potencia, radiación, estado y alertas activas."""
    plant = db.query(SolarPlant).filter(SolarPlant.id == plant_id).first()
    if not plant:
        raise HTTPException(status_code=404, detail="Planta solar no encontrada.")

    latest_telemetry = (
        db.query(PlantTelemetry)
        .filter(PlantTelemetry.plant_id == plant_id)
        .order_by(desc(PlantTelemetry.time))
        .first()
    )

    pending_alerts_count = (
        db.query(SystemAlert)
        .filter(SystemAlert.plant_id == plant_id, SystemAlert.status == "pending")
        .count()
    )

    return {
        "plant_id": plant.id,
        "name": plant.name,
        "installed_capacity_kw": plant.installed_capacity_kw,
        "current_power_w": latest_telemetry.p_dc if latest_telemetry else 0.0,
        "current_irradiance_w_m2": latest_telemetry.g_irradiance if latest_telemetry else 0.0,
        "current_t_panel_c": latest_telemetry.t_panel if latest_telemetry else 0.0,
        "performance_ratio": latest_telemetry.performance_ratio if latest_telemetry else None,
        "active_alerts_count": pending_alerts_count,
        "last_updated": latest_telemetry.time.isoformat() if latest_telemetry else None
    }
