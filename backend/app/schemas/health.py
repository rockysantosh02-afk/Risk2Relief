"""Health check response models."""

from typing import Dict
from pydantic import BaseModel, Field


class DependencyHealth(BaseModel):
    """Status of external system dependencies."""
    database: str = Field(description="Database connectivity status: connected | disconnected")
    redis: str = Field(description="Redis connectivity status: connected | disconnected | not_installed")


class HealthResponse(BaseModel):
    """Structured health response conforming to Risk2Relief Phase 1 specifications."""
    status: str = Field(default="ok", description="Overall platform status")
    service: str = Field(default="risk2relief-api", description="Service identifier")
    version: str = Field(description="Application version")
    timestamp: str = Field(description="ISO-8601 formatted timestamp of the health inspection")
    dependencies: DependencyHealth = Field(description="Health of backing dependencies")
