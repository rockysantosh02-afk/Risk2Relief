"""Simulation-Oriented Structural Load & Response Engine.

Calculates load distributions, structural member utilization, estimated stress,
estimated strain, and safety margins under simulated gravitational relief.

SAFETY INVARIANT & CERTIFICATION DISCLAIMER:
These calculations are in-silico digital-twin simulations for operational observability
and risk scenario testing. They DO NOT constitute certified structural engineering
analyses or replace professional civil/structural engineering stamps.

Explicit Data Provenance:
- MEASURED: Physical sensor telemetry data.
- SIMULATED: In-silico digital-twin gravity offload field values.
- ESTIMATED: Derived structural stresses, strains, and utilization metrics.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from app.physics.gravity_engine import Coordinate3D, GravitySimulationState


class DataProvenance(str, Enum):
    MEASURED = "MEASURED"
    SIMULATED = "SIMULATED"
    ESTIMATED = "ESTIMATED"


@dataclass
class MemberLoadResult:
    """Load and stress state for a single structural element."""
    node_id: str
    node_code: str
    node_type: str                  # COLUMN, BEAM, SLAB, FOUNDATION, etc.
    floor_number: int
    zone_code: str
    position: Coordinate3D
    cross_sectional_area_m2: float  # Member cross section
    elastic_modulus_gpa: float      # Concrete ~30 GPa, Steel ~200 GPa
    capacity_kn: float              # Ultimate structural design capacity in kN

    # Loads (kN)
    dead_load_kn: float             # Permanent gravity load (ESTIMATED)
    live_load_kn: float             # Transient occupancy/wind load (ESTIMATED / MEASURED)
    gravity_relief_kn: float        # Relief force from simulated gravity twin (SIMULATED)
    net_effective_load_kn: float    # Dead + Live - Relief (ESTIMATED)

    # Responses
    utilization_ratio: float        # Net / Capacity (ESTIMATED)
    estimated_axial_stress_mpa: float # Net / Area in MPa (ESTIMATED)
    estimated_strain_microstrain: float # Stress / E in ue (ESTIMATED)
    safety_margin_percentage: float # (1 - Utilization) * 100 (ESTIMATED)

    # Measured Telemetry
    measured_strain_microstrain: Optional[float] = None # (MEASURED)
    measured_vibration_hz: Optional[float] = None       # (MEASURED)
    measured_inclination_deg: Optional[float] = None    # (MEASURED)
    measured_temperature_c: Optional[float] = None      # (MEASURED)

    provenance_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class StructuralLoadDistribution:
    """Aggregated structural load response across the digital twin."""
    total_structural_dead_load_kn: float
    total_live_load_kn: float
    total_applied_load_kn: float
    total_simulated_relief_kn: float
    net_building_load_kn: float
    overall_building_relief_percentage: float
    members: List[MemberLoadResult]
    peak_utilization_ratio: float
    mean_utilization_ratio: float
    critical_members_count: int  # Utilization >= 0.85
    disclaimer: str = (
        "In-silico digital-twin simulation estimates only. "
        "Not a certified civil/structural engineering stamp or safety design document."
    )


class StructuralLoadEngine:
    """Calculates structural load distribution under in-silico gravity mitigation."""

    @staticmethod
    def calculate_member_load(
        node_id: str,
        node_code: str,
        node_type: str,
        floor_number: int,
        zone_code: str,
        position: Coordinate3D,
        capacity_kn: float,
        dead_load_kn: float,
        live_load_kn: float,
        simulated_relief_kn: float,
        cross_sectional_area_m2: float = 0.25, # e.g. 50cm x 50cm column
        elastic_modulus_gpa: float = 30.0,     # Standard reinforced concrete
        telemetry: Optional[Dict[str, float]] = None,
    ) -> MemberLoadResult:
        """Calculate load, stress, strain, and utilization for a structural member."""
        tel = telemetry or {}
        measured_strain = tel.get("strain_microstrain")
        measured_vib = tel.get("vibration_hz")
        measured_incl = tel.get("inclination_deg")
        measured_temp = tel.get("temperature_celsius")

        # Net effective axial load on member
        total_applied = dead_load_kn + live_load_kn
        net_load = max(0.0, total_applied - simulated_relief_kn)

        # Utilization: net_load / capacity
        cap = max(1.0, capacity_kn)
        utilization = round(net_load / cap, 4)
        safety_margin = round(max(-100.0, (1.0 - utilization) * 100.0), 2)

        # Axial stress: N (kN) / A (m^2) -> 1 kN / 1 m^2 = 1 kPa = 0.001 MPa
        area = max(0.01, cross_sectional_area_m2)
        stress_mpa = round((net_load * 0.001) / area, 4)

        # Strain: epsilon = sigma (MPa) / E (GPa) -> 1 MPa / 1 GPa = 10^-3 = 1000 microstrain
        e_gpa = max(1.0, elastic_modulus_gpa)
        strain_ue = round((stress_mpa / e_gpa) * 1000.0, 2)

        provenance = {
            "dead_load_kn": DataProvenance.ESTIMATED.value,
            "live_load_kn": DataProvenance.MEASURED.value if "load_kn" in tel else DataProvenance.ESTIMATED.value,
            "gravity_relief_kn": DataProvenance.SIMULATED.value,
            "net_effective_load_kn": DataProvenance.ESTIMATED.value,
            "utilization_ratio": DataProvenance.ESTIMATED.value,
            "estimated_axial_stress_mpa": DataProvenance.ESTIMATED.value,
            "estimated_strain_microstrain": DataProvenance.ESTIMATED.value,
            "measured_strain_microstrain": DataProvenance.MEASURED.value if measured_strain is not None else "UNAVAILABLE",
            "measured_vibration_hz": DataProvenance.MEASURED.value if measured_vib is not None else "UNAVAILABLE",
            "measured_inclination_deg": DataProvenance.MEASURED.value if measured_incl is not None else "UNAVAILABLE",
            "measured_temperature_c": DataProvenance.MEASURED.value if measured_temp is not None else "UNAVAILABLE",
        }

        return MemberLoadResult(
            node_id=node_id,
            node_code=node_code,
            node_type=node_type,
            floor_number=floor_number,
            zone_code=zone_code,
            position=position,
            cross_sectional_area_m2=cross_sectional_area_m2,
            elastic_modulus_gpa=elastic_modulus_gpa,
            capacity_kn=capacity_kn,
            dead_load_kn=dead_load_kn,
            live_load_kn=live_load_kn,
            gravity_relief_kn=round(simulated_relief_kn, 4),
            net_effective_load_kn=round(net_load, 4),
            utilization_ratio=utilization,
            estimated_axial_stress_mpa=stress_mpa,
            estimated_strain_microstrain=strain_ue,
            safety_margin_percentage=safety_margin,
            measured_strain_microstrain=measured_strain,
            measured_vibration_hz=measured_vib,
            measured_inclination_deg=measured_incl,
            measured_temperature_c=measured_temp,
            provenance_map=provenance,
        )

    @classmethod
    def evaluate_building_loads(
        cls,
        members_data: List[Dict[str, Any]],
        gravity_simulation_state: Optional[GravitySimulationState] = None,
        telemetry_by_node: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> StructuralLoadDistribution:
        """Compute structural load and relief across all building structural members."""
        tel_map = telemetry_by_node or {}
        results: List[MemberLoadResult] = []

        # Map gravity relief at member coordinates
        field_eval_points = (
            gravity_simulation_state.field_state.evaluation_points
            if gravity_simulation_state and gravity_simulation_state.field_state
            else []
        )
        relief_by_point: Dict[str, float] = {
            pt.point_id: pt.combined_field_kn for pt in field_eval_points
        }

        tot_dead = 0.0
        tot_live = 0.0
        tot_relief = 0.0
        tot_net = 0.0

        for m in members_data:
            node_id = str(m["node_id"])
            pos = Coordinate3D(x=m.get("position_x", 0.0), y=m.get("position_y", 0.0), z=m.get("position_z", 0.0))
            
            # Find closest relief or direct mapped point
            relief = relief_by_point.get(node_id, 0.0)
            if relief == 0.0 and field_eval_points:
                # Find nearest evaluation point within 10m
                closest_dist = float("inf")
                closest_relief = 0.0
                for pt in field_eval_points:
                    d = pos.distance_to(pt.position)
                    if d < closest_dist and d <= 15.0:
                        closest_dist = d
                        closest_relief = pt.combined_field_kn
                relief = closest_relief

            dead = float(m.get("dead_load_kn", 800.0))
            live = float(m.get("live_load_kn", 300.0))
            cap = float(m.get("capacity_kn", 2500.0))

            member_tel = tel_map.get(node_id, {})

            res = cls.calculate_member_load(
                node_id=node_id,
                node_code=m.get("node_code", f"SN-{node_id[:6]}"),
                node_type=m.get("node_type", "COLUMN"),
                floor_number=m.get("floor_number", 1),
                zone_code=m.get("zone_code", "CORE"),
                position=pos,
                capacity_kn=cap,
                dead_load_kn=dead,
                live_load_kn=live,
                simulated_relief_kn=relief,
                cross_sectional_area_m2=float(m.get("cross_sectional_area_m2", 0.25)),
                elastic_modulus_gpa=float(m.get("elastic_modulus_gpa", 30.0)),
                telemetry=member_tel,
            )

            tot_dead += dead
            tot_live += live
            tot_relief += res.gravity_relief_kn
            tot_net += res.net_effective_load_kn
            results.append(res)

        total_applied = tot_dead + tot_live
        relief_pct = round((tot_relief / total_applied) * 100.0, 2) if total_applied > 0 else 0.0

        utilizations = [r.utilization_ratio for r in results]
        peak_u = max(utilizations) if utilizations else 0.0
        mean_u = sum(utilizations) / len(utilizations) if utilizations else 0.0
        crit_count = sum(1 for u in utilizations if u >= 0.85)

        return StructuralLoadDistribution(
            total_structural_dead_load_kn=round(tot_dead, 2),
            total_live_load_kn=round(tot_live, 2),
            total_applied_load_kn=round(total_applied, 2),
            total_simulated_relief_kn=round(tot_relief, 2),
            net_building_load_kn=round(tot_net, 2),
            overall_building_relief_percentage=relief_pct,
            members=results,
            peak_utilization_ratio=round(peak_u, 4),
            mean_utilization_ratio=round(mean_u, 4),
            critical_members_count=crit_count,
        )
