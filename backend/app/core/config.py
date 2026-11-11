"""
Configuración centralizada del sistema STV utilizando Pydantic Settings.
Soporta variables de entorno y archivo .env.
"""
from typing import List
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "STV - Sistema Inteligente Fotovoltaico"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "stv_super_secret_jwt_key_development_only_change_in_prod_2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    
    # Orígenes permitidos para CORS (Frontend)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Base de Datos PostgreSQL + TimescaleDB
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "stv_postgres_2026"
    POSTGRES_DB: str = "stv_timescale"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Caché y Colas Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # Broker MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_BROKER_TLS_PORT: int = 8883
    MQTT_USERNAME: str = "stv_gateway"
    MQTT_PASSWORD: str = "stv_mqtt_secret_2026"
    MQTT_TOPIC_TELEMETRY: str = "stv/v1/+/+/telemetry"
    MQTT_TOPIC_ALERTS: str = "stv/v1/+/+/alerts"

    # Notificaciones Externas
    TELEGRAM_BOT_TOKEN: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()
