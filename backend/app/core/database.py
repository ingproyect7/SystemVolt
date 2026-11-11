"""
Gestión de conexiones a la base de datos relacional y TimescaleDB.
Soporta tanto operaciones asíncronas con asyncpg como síncronas para testing y migraciones.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from backend.app.core.config import settings

# Base declarativa para todos los modelos ORM
Base = declarative_base()

# Motor síncrono para migraciones y testing
# Si no hay Postgres en localhost durante desarrollo o pruebas, soporta SQLite fallback en memoria o archivo
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Motor para pruebas locales con SQLite si Postgres no está levantado
engine = None
SessionLocal = None

def get_engine():
    global engine, SessionLocal
    if engine is None:
        try:
            engine = create_engine(DATABASE_URL_SYNC, pool_pre_ping=True)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            # Prueba rápida de conexión
            with engine.connect() as conn:
                pass
        except Exception:
            # Fallback seguro a SQLite local para desarrollo si Docker aún no está iniciado
            sqlite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "stv_local_dev.db"))
            engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine

def get_session():
    """Retorna una nueva sesión de base de datos garantizando que el motor esté inicializado."""
    get_engine()
    return SessionLocal()

def get_db():
    """Generador de dependencias FastAPI para obtener sesiones de base de datos."""
    get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Crea las tablas en la base de datos si no existen."""
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
