"""Application configuration using Pydantic v2 Settings."""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core settings for Risk2Relief digital-twin platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # General
    ENVIRONMENT: str = Field(default="development", description="Runtime environment")
    PROJECT_NAME: str = Field(default="Risk2Relief Building-Management Digital-Twin")
    APP_VERSION: str = Field(default="0.1.0")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")

    # Server & Networking
    BACKEND_HOST: str = Field(default="0.0.0.0")
    BACKEND_PORT: int = Field(default=8000)
    ALLOWED_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # Database
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="risk2relief_db")
    POSTGRES_USER: str = Field(default="risk2relief_user")
    POSTGRES_PASSWORD: str = Field(default="change_this_in_production_risk2relief_pass")
    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = Field(default=10)
    DB_MAX_OVERFLOW: int = Field(default=20)
    DB_POOL_TIMEOUT: int = Field(default=30)

    # Redis & Celery
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_PASSWORD: Optional[str] = Field(default=None)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: Optional[str] = None
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Digital-Twin & Safety Boundaries
    # The anti-gravity subsystem is an in-silico simulation model only.
    # Hardware actuation is permanently prohibited by architecture invariants.
    SIMULATION_MODE: bool = Field(default=True)
    ENABLE_HARDWARE_ACTUATION: bool = Field(
        default=False,
        description="System safety barrier: hardware actuation must remain disabled"
    )
    SIMULATION_TICK_RATE_HZ: int = Field(default=10)
    MAX_STRUCTURAL_STRESS_TOLERANCE_MPA: float = Field(default=450.0)
    CRITICAL_DEFLECTION_THRESHOLD_MM: float = Field(default=15.0)

    def get_database_url(self) -> str:
        """Construct or return the async database connection URL."""
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_redis_url(self) -> str:
        """Construct or return the Redis connection URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    def get_celery_broker_url(self) -> str:
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    def get_celery_result_backend(self) -> str:
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/2"


@lru_cache()
def get_settings() -> Settings:
    """Cached accessor for application settings."""
    return Settings()
