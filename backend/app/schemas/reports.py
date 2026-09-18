"""Pydantic v2 schemas for Facility Intelligence & Summary Reports."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class ReportTypeEnum(str, Enum):
    SAFETY = "SAFETY"
    STRUCTURAL_RISK = "STRUCTURAL_RISK"
    TELEMETRY_QUALITY = "TELEMETRY_QUALITY"
    FACILITY_COMPREHENSIVE = "FACILITY_COMPREHENSIVE"


class ReportGenerateRequest(BaseModel):
    """Parameters for on-demand report compilation."""
    building_id: uuid.UUID
    report_type: ReportTypeEnum = Field(default=ReportTypeEnum.FACILITY_COMPREHENSIVE)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_containment_recommendations: bool = True
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ReportSection(BaseModel):
    title: str
    summary: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    details: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class ReportResponse(BaseModel):
    """Structured generated report representation."""
    report_id: str
    building_id: uuid.UUID
    report_type: ReportTypeEnum
    title: str
    status: str = "GENERATED"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executive_summary: str
    sections: List[ReportSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)
