"""API v1 Endpoints for Climate Sources, Observations, Policies, Settlements, and Audit."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.climate import (
    ClimateSourceResponse,
    ClimateSourceCreate,
    ClimateObservationResponse,
    ClimateObservationCreate,
    ClimateEventResponse,
)
from app.schemas.insurance import (
    InsurancePolicyResponse,
    InsurancePolicyCreate,
    SettlementResponse,
    ConsensusDecisionResponse,
)
from app.climate.simulator import Risk2ReliefSimulator
from app.climate.settlement_engine import SimulatedSettlementEngine
from app.climate.audit_trail import ClimateAuditTrailService
from app.climate.validation import ClimateValidationEngine
from app.climate.anomaly import ClimateAnomalyEngine
from app.climate.consensus import ClimateConsensusEngine, ConsensusPolicy

router = APIRouter(prefix="", tags=["Risk2Relief Climate Insurance"])

# In-memory demo data stores
_DEMO_SOURCES: List[Dict[str, Any]] = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "source_identifier": "SRC-SAT-001",
        "provider_name": "Copernicus_EU",
        "source_name": "Copernicus Sentinel-1 Synthetic Aperture Radar",
        "source_type": "SATELLITE",
        "source_family": "SATELLITE_RADAR",
        "independence_group": "GROUP_COPERNICUS",
        "location_name": "Vellore Regional Agricultural Belt",
        "latitude": 12.9165,
        "longitude": 79.1325,
        "reliability_score": 0.98,
        "status": "ONLINE",
        "last_seen": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"orbit": "Sun-synchronous", "resolution_meters": 10},
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "source_identifier": "SRC-GROUND-002",
        "provider_name": "IMD_Ground_Network",
        "source_name": "IMD Meteorological Ground Station (Vellore Central)",
        "source_type": "GROUND_STATION",
        "source_family": "TIPPING_BUCKET_GAUGE",
        "independence_group": "GROUP_IMD",
        "location_name": "Vellore Agro Research Center",
        "latitude": 12.9240,
        "longitude": 79.1350,
        "reliability_score": 0.96,
        "status": "ONLINE",
        "last_seen": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"station_id": "IMD-TN-VEL-04", "calibration_date": "2026-08-15"},
    },
    {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "source_identifier": "SRC-IOT-003",
        "provider_name": "Community_IoT",
        "source_name": "AgriSense Community Optical Rain Sensor",
        "source_type": "IOT_SENSOR",
        "source_family": "OPTICAL_GAUGE",
        "independence_group": "GROUP_COMMUNITY_IOT",
        "location_name": "Thiruvalam Farmland Cluster",
        "latitude": 12.9800,
        "longitude": 79.2300,
        "reliability_score": 0.94,
        "status": "ONLINE",
        "last_seen": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"mesh_id": "AGRI-MESH-09", "sampling_interval_min": 5},
    },
    {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "source_identifier": "SRC-API-004",
        "provider_name": "OpenMeteo_Global",
        "source_name": "Open-Meteo High Resolution Reanalysis API",
        "source_type": "WEATHER_API",
        "source_family": "NUMERICAL_MODEL",
        "independence_group": "GROUP_OPEN_METEO",
        "location_name": "Tamil Nadu Northern District Grid",
        "latitude": 12.9165,
        "longitude": 79.1325,
        "reliability_score": 0.91,
        "status": "ONLINE",
        "last_seen": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"model": "ECMWF IFS 0.1deg", "update_frequency_hours": 1},
    },
]

_DEMO_POLICIES: List[Dict[str, Any]] = [
    {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "policy_number": "R2R-POL-2026-001",
        "policyholder_name": "Rajesh Kumar (Smallholder Farmer)",
        "policyholder_type": "FARMER",
        "location_name": "Vellore Agro District, Zone 4",
        "covered_event": "FLASH_FLOOD",
        "metric": "rainfall_24h",
        "operator": ">=",
        "threshold": 150.0,
        "payout_amount": 25000.0,
        "currency": "INR",
        "active": True,
        "effective_from": datetime.now(timezone.utc) - timedelta(days=30),
        "effective_to": datetime.now(timezone.utc) + timedelta(days=335),
        "wallet_id": "SIM-WALLET-FARMER-001",
        "created_at": datetime.now(timezone.utc) - timedelta(days=30),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"crop_type": "Paddy / Rice", "land_area_acres": 2.5},
    },
    {
        "id": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "policy_number": "R2R-POL-2026-002",
        "policyholder_name": "Ananya Sharma (Gig Delivery Partner)",
        "policyholder_type": "GIG_WORKER",
        "location_name": "Chennai Urban Coastal Hub",
        "covered_event": "EXTREME_RAINFALL",
        "metric": "rainfall_24h",
        "operator": ">=",
        "threshold": 120.0,
        "payout_amount": 8000.0,
        "currency": "INR",
        "active": True,
        "effective_from": datetime.now(timezone.utc) - timedelta(days=15),
        "effective_to": datetime.now(timezone.utc) + timedelta(days=350),
        "wallet_id": "SIM-WALLET-GIG-002",
        "created_at": datetime.now(timezone.utc) - timedelta(days=15),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"income_protection_days": 4},
    },
    {
        "id": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        "policy_number": "R2R-POL-2026-003",
        "policyholder_name": "Palaniswamy (Cooperative Society)",
        "policyholder_type": "COOPERATIVE",
        "location_name": "Ranipet Agritech Belt",
        "covered_event": "DROUGHT",
        "metric": "soil_moisture_pct",
        "operator": "<=",
        "threshold": 15.0,
        "payout_amount": 100000.0,
        "currency": "INR",
        "active": True,
        "effective_from": datetime.now(timezone.utc) - timedelta(days=60),
        "effective_to": datetime.now(timezone.utc) + timedelta(days=305),
        "wallet_id": "SIM-WALLET-COOP-003",
        "created_at": datetime.now(timezone.utc) - timedelta(days=60),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"members_count": 48},
    },
]

_DEMO_EVENTS: List[Dict[str, Any]] = [
    {
        "id": uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
        "event_identifier": "EVT-2026-FLOOD-001",
        "event_type": "FLASH_FLOOD",
        "location_name": "Vellore Agro District, Zone 4",
        "latitude": 12.9165,
        "longitude": 79.1325,
        "start_time": datetime.now(timezone.utc) - timedelta(hours=4),
        "end_time": None,
        "status": "TRIGGERED",
        "severity": "CRITICAL",
        "description": "Severe localized precipitation event triggering automated parametric flash flood protection.",
        "consensus_value": 156.0,
        "consensus_unit": "mm",
        "source_count": 3,
        "independent_source_count": 3,
        "created_at": datetime.now(timezone.utc) - timedelta(hours=4),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": {"risk_level": "RED_ALERT"},
    },
]


@router.get("/climate/sources", response_model=List[ClimateSourceResponse], summary="List all climate data sources")
async def list_climate_sources():
    """Return all active climate data sources with provenance and independence groups."""
    return _DEMO_SOURCES


@router.get("/policies", response_model=List[InsurancePolicyResponse], summary="List all insurance policies")
async def list_policies():
    """Return all active parametric insurance contracts."""
    return _DEMO_POLICIES


@router.post("/policies", response_model=InsurancePolicyResponse, summary="Create a new parametric insurance policy")
async def create_policy(policy_in: InsurancePolicyCreate):
    """Register a new parametric climate policy contract."""
    new_pol = {
        "id": uuid.uuid4(),
        "policy_number": policy_in.policy_number,
        "policyholder_name": policy_in.policyholder_name,
        "policyholder_type": policy_in.policyholder_type,
        "location_name": policy_in.location_name,
        "covered_event": policy_in.covered_event,
        "metric": policy_in.metric,
        "operator": policy_in.operator,
        "threshold": policy_in.threshold,
        "payout_amount": policy_in.payout_amount,
        "currency": policy_in.currency,
        "active": policy_in.active,
        "effective_from": policy_in.effective_from,
        "effective_to": policy_in.effective_to,
        "wallet_id": policy_in.wallet_id,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "metadata_json": policy_in.metadata_json or {},
    }
    _DEMO_POLICIES.append(new_pol)
    return new_pol


@router.get("/climate/events", response_model=List[ClimateEventResponse], summary="List monitored climate events")
async def list_climate_events():
    """Return all monitored and triggered climate events."""
    return _DEMO_EVENTS


@router.get("/settlements", response_model=List[SettlementResponse], summary="List simulated settlements")
async def list_settlements():
    """Return all completed and pending simulated settlements."""
    records = SimulatedSettlementEngine.get_all_settlements()
    return [
        SettlementResponse(
            id=uuid.uuid4(),
            settlement_id=r.settlement_id,
            policy_id=uuid.UUID(r.policy_id) if len(r.policy_id) == 36 else uuid.uuid4(),
            policy_number=r.policy_number,
            event_identifier=r.event_identifier,
            settlement_key=r.settlement_key,
            wallet_id=r.wallet_id,
            amount=r.amount,
            currency=r.currency,
            transaction_id=r.transaction_id,
            status=r.status,
            failure_reason=r.failure_reason,
            is_simulation=True,
            created_at=r.created_at,
            completed_at=r.completed_at,
        )
        for r in records
    ]


@router.get("/climate/audit", summary="Fetch complete decision audit timeline")
async def get_audit_trail(event_id: Optional[str] = Query(None, description="Optional climate event filter")):
    """Return chronological decision trail for audit compliance."""
    if event_id:
        events = ClimateAuditTrailService.get_events_for_climate_event(event_id)
    else:
        events = ClimateAuditTrailService.get_all_events(limit=100)

    return [
        {
            "id": e.id,
            "event_identifier": e.event_identifier,
            "policy_id": e.policy_id,
            "stage": e.stage,
            "status": e.status,
            "title": e.title,
            "message": e.message,
            "actor": e.actor,
            "correlation_id": e.correlation_id,
            "metadata": e.metadata,
            "timestamp": e.timestamp.isoformat(),
        }
        for e in events
    ]
