"""Pure Python Computational Gravity Digital-Twin Engine.

SYSTEM SAFETY BOUNDARY:
This module represents a pure in-silico mathematical simulation.
It DOES NOT control physical hardware, issue actuator commands, or connect to
real-world physical devices. All units are explicitly documented and calculations
are completely deterministic.

Units:
- Distance / Coordinates: meters (m)
- Force / Capacity: kiloNewtons (kN)
- Stress: MegaPascals (MPa)
- Offset: Percentage (%)
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


@dataclass(frozen=True)
class Coordinate3D:
    """3D spatial coordinate in meters."""
    x: float
    y: float
    z: float

    def distance_to(self, other: Coordinate3D) -> float:
        """Calculate Euclidean distance in meters."""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )


@dataclass
class GravityNodeState:
    """State of a simulated anti-gravity digital-twin node."""
    node_id: str
    identifier: str
    position: Coordinate3D
    nominal_capacity_kn: float
    operating_state: str = "ACTIVE"  # ACTIVE, DEGRADED, FAILED, OFFLINE, SIMULATED
    health_score: float = 100.0      # 0.0 to 100.0
    efficiency: float = 1.0          # 0.0 to 1.0
    influence_radius_m: float = 20.0 # Characteristic decay radius R0

    @property
    def is_active(self) -> bool:
        """Check if node is currently emitting simulated field."""
        return self.operating_state.upper() in ("ACTIVE", "SIMULATED") and self.health_score > 0.0

    @property
    def active_field_kn(self) -> float:
        """Computed current simulated force capacity in kiloNewtons."""
        if not self.is_active:
            return 0.0
        health_factor = max(0.0, min(1.0, self.health_score / 100.0))
        efficiency_factor = max(0.0, min(1.0, self.efficiency))
        return round(self.nominal_capacity_kn * efficiency_factor * health_factor, 4)

    def calculate_contribution_at(self, target_pos: Coordinate3D) -> float:
        """Calculate localized field influence at a 3D coordinate in kN.

        Uses deterministic rational quadratic spatial attenuation:
        w(r) = 1.0 / (1.0 + (r / R0)^2)
        """
        if not self.is_active or self.active_field_kn <= 0.0:
            return 0.0

        distance = self.position.distance_to(target_pos)
        r0 = max(1.0, self.influence_radius_m)
        attenuation = 1.0 / (1.0 + (distance / r0) ** 2)

        # Cutoff threshold at 5x R0 to prevent infinite tail evaluation
        if distance > (5.0 * r0):
            return 0.0

        return round(self.active_field_kn * attenuation, 4)


@dataclass
class FieldEvaluationPoint:
    """Spatial observation point within building envelope."""
    point_id: str
    position: Coordinate3D
    zone_id: Optional[str] = None
    reference_dead_load_kn: float = 1000.0
    combined_field_kn: float = 0.0
    effective_offset_percentage: float = 0.0
    contributions_by_node: Dict[str, float] = field(default_factory=dict)


@dataclass
class GravityFieldState:
    """Aggregated spatial state of the simulated gravitational field."""
    target_offset_percentage: float
    evaluation_points: List[FieldEvaluationPoint]
    mean_field_kn: float = 0.0
    mean_offset_percentage: float = 0.0
    target_deviation_percentage: float = 0.0
    field_uniformity: float = 1.0
    min_offset_percentage: float = 0.0
    max_offset_percentage: float = 0.0
    total_field_relief_kn: float = 0.0


@dataclass
class GravitySimulationState:
    """Complete discrete time-step state of the gravity digital twin."""
    step_number: int
    timestamp_seconds: float
    nodes: List[GravityNodeState]
    field_state: GravityFieldState
    total_nominal_capacity_kn: float
    total_active_capacity_kn: float
    active_node_count: int
    total_node_count: int
    active_node_ratio: float
    stability_status: str = "NORMAL"  # NORMAL, WARNING, CRITICAL, UNSTABLE


class PureGravityEngine:
    """Pure computational engine for simulated multi-node gravity fields."""

    @staticmethod
    def calculate_field(
        nodes: List[GravityNodeState],
        evaluation_points: List[FieldEvaluationPoint],
        target_offset_percentage: float = 15.0,
    ) -> GravityFieldState:
        """Calculate spatial superposition field across all evaluation points."""
        if not evaluation_points:
            return GravityFieldState(
                target_offset_percentage=target_offset_percentage,
                evaluation_points=[],
                mean_field_kn=0.0,
                mean_offset_percentage=0.0,
                target_deviation_percentage=target_offset_percentage,
                field_uniformity=0.0,
                min_offset_percentage=0.0,
                max_offset_percentage=0.0,
                total_field_relief_kn=0.0,
            )

        updated_points: List[FieldEvaluationPoint] = []
        total_relief_kn = 0.0
        offsets: List[float] = []

        for pt in evaluation_points:
            contributions: Dict[str, float] = {}
            total_field_at_pt = 0.0

            for node in nodes:
                c = node.calculate_contribution_at(pt.position)
                if c > 0.0:
                    contributions[node.node_id] = c
                    total_field_at_pt += c

            ref_load = max(1.0, pt.reference_dead_load_kn)
            offset_pct = round((total_field_at_pt / ref_load) * 100.0, 4)
            offsets.append(offset_pct)
            total_relief_kn += total_field_at_pt

            updated_points.append(
                FieldEvaluationPoint(
                    point_id=pt.point_id,
                    position=pt.position,
                    zone_id=pt.zone_id,
                    reference_dead_load_kn=pt.reference_dead_load_kn,
                    combined_field_kn=round(total_field_at_pt, 4),
                    effective_offset_percentage=offset_pct,
                    contributions_by_node=contributions,
                )
            )

        n_pts = len(updated_points)
        mean_field = total_relief_kn / n_pts
        mean_offset = sum(offsets) / n_pts
        min_offset = min(offsets) if offsets else 0.0
        max_offset = max(offsets) if offsets else 0.0

        # Uniformity: 1.0 - coefficient of variation (CoV)
        if len(offsets) > 1 and mean_offset > 0.0:
            variance = sum((x - mean_offset) ** 2 for x in offsets) / (len(offsets) - 1)
            stddev = math.sqrt(variance)
            cov = stddev / mean_offset
            uniformity = round(max(0.0, min(1.0, 1.0 - cov)), 4)
        else:
            uniformity = 1.0 if mean_offset > 0.0 else 0.0

        target_dev = round(abs(mean_offset - target_offset_percentage), 4)

        return GravityFieldState(
            target_offset_percentage=target_offset_percentage,
            evaluation_points=updated_points,
            mean_field_kn=round(mean_field, 4),
            mean_offset_percentage=round(mean_offset, 4),
            target_deviation_percentage=target_dev,
            field_uniformity=uniformity,
            min_offset_percentage=round(min_offset, 4),
            max_offset_percentage=round(max_offset, 4),
            total_field_relief_kn=round(total_relief_kn, 4),
        )

    @classmethod
    def simulate_step(
        cls,
        step_number: int,
        timestamp_seconds: float,
        nodes: List[GravityNodeState],
        evaluation_points: List[FieldEvaluationPoint],
        target_offset_percentage: float = 15.0,
    ) -> GravitySimulationState:
        """Execute a single deterministic simulation step."""
        field_state = cls.calculate_field(nodes, evaluation_points, target_offset_percentage)

        total_nom = sum(n.nominal_capacity_kn for n in nodes)
        total_act = sum(n.active_field_kn for n in nodes)
        act_count = sum(1 for n in nodes if n.is_active)
        tot_count = len(nodes)
        ratio = (act_count / tot_count) if tot_count > 0 else 0.0

        return GravitySimulationState(
            step_number=step_number,
            timestamp_seconds=timestamp_seconds,
            nodes=nodes,
            field_state=field_state,
            total_nominal_capacity_kn=round(total_nom, 4),
            total_active_capacity_kn=round(total_act, 4),
            active_node_count=act_count,
            total_node_count=tot_count,
            active_node_ratio=round(ratio, 4),
            stability_status="NORMAL",
        )
