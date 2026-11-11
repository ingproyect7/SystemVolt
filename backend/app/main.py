"""
Punto de entrada principal para el Backend API de STV (FastAPI).
================================================================
Provee servicios REST para ingestión de telemetría, consultas analíticas,
gestión de plantas solares y despacho de alertas.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar tablas de base de datos
    init_db()
    print("[BACKEND] Base de datos y esquemas inicializados correctamente.")
    yield
    print("[BACKEND] Servidor apagándose limpiamente.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Configurar Middleware de CORS para permitir conexión del Frontend
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Incluir rutas de API v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Salud"])
def health_check():
    """Endpoint de verificación de estado y vitalidad del backend."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "api_version": "v1"
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Bienvenido al API del Sistema Fotovoltaico Inteligente (STV)",
        "docs_url": f"{settings.API_V1_STR}/docs"
    }
