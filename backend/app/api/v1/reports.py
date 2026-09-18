"""API v1 Facility Intelligence and Audit Report Endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.report_service import ReportService
from app.schemas.reports import ReportGenerateRequest, ReportResponse

router = APIRouter(prefix="/reports", tags=["Facility Reports"])

# In-memory storage cache for generated reports
_REPORT_CACHE: Dict[str, ReportResponse] = {}


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Facility Intelligence Report",
    description="Compiles multi-section report aggregating telemetry quality, structural load metrics, and safety incidents.",
)
async def generate_facility_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    service = ReportService(db)
    try:
        report = await service.generate_report(request)
        _REPORT_CACHE[report.report_id] = report
        return report
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get Facility Report by ID",
)
async def get_facility_report(
    report_id: str,
) -> ReportResponse:
    report = _REPORT_CACHE.get(report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report '{report_id}' not found")
    return report
