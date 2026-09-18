"""Scenario Executor for Digital-Twin Resilience & Disturbance Injections.

Modifies simulation inputs deterministically for 7 disturbance scenarios:
1. NORMAL
2. NODE_FAILURE
3. FIELD_IMBALANCE
4. STRUCTURAL_OVERLOAD
5. TELEMETRY_FAILURE
6. POWER_FAILURE
7. EMERGENCY
"""

from __future__ import annotations
import copy
from enum import Enum
from typing import List, Dict, Any, Tuple
from app.physics.gravity_engine import GravityNodeState, Coordinate3D


class ScenarioType(str, Enum):
    NORMAL = "NORMAL"
    NODE_FAILURE = "NODE_FAILURE"
    FIELD_IMBALANCE = "FIELD_IMBALANCE"
    STRUCTURAL_OVERLOAD = "STRUCTURAL_OVERLOAD"
    TELEMETRY_FAILURE = "TELEMETRY_FAILURE"
    POWER_FAILURE = "POWER_FAILURE"
    EMERGENCY = "EMERGENCY"


class ScenarioExecutor:
    """Applies scenario-specific modifications to digital-twin simulation inputs."""

    @classmethod
    def apply_scenario(
        cls,
        scenario_type: ScenarioType | str,
        nodes: List[GravityNodeState],
        members_data: List[Dict[str, Any]],
        telemetry_by_node: Dict[str, Dict[str, float]],
        target_offset_percentage: float = 15.0,
        custom_params: Dict[str, Any] = None,
    ) -> Tuple[List[GravityNodeState], List[Dict[str, Any]], Dict[str, Dict[str, float]], float, float]:
        """Apply scenario perturbation.

        Returns (modified_nodes, modified_members, modified_telemetry, target_offset, telemetry_reliability).
        """
        # Deepcopy to prevent mutating caller references
        mod_nodes = [copy.deepcopy(n) for n in nodes]
        mod_members = [copy.deepcopy(m) for m in members_data]
        mod_telemetry = copy.deepcopy(telemetry_by_node)
        mod_target = target_offset_percentage
        telemetry_reliability = 1.0

        stype = ScenarioType(scenario_type.upper()) if isinstance(scenario_type, str) else scenario_type

        if stype == ScenarioType.NORMAL:
            # Baseline nominal operating conditions
            pass

        elif stype == ScenarioType.NODE_FAILURE:
            # Drop 1 or 2 nodes to FAILED state (0 capacity)
            if mod_nodes:
                mod_nodes[0].operating_state = "FAILED"
                mod_nodes[0].health_score = 0.0
                mod_nodes[0].efficiency = 0.0

        elif stype == ScenarioType.FIELD_IMBALANCE:
            # Induce strong spatial asymmetry (e.g. degrade nodes with positive x-coordinates)
            for n in mod_nodes:
                if n.position.x >= 0.0:
                    n.efficiency = 0.10
                    n.health_score = 30.0
                    n.operating_state = "DEGRADED"

        elif stype == ScenarioType.STRUCTURAL_OVERLOAD:
            # Apply 250% live load to all structural members
            for m in mod_members:
                m["live_load_kn"] = m.get("live_load_kn", 300.0) * 2.5
            # Elevated strain in telemetry
            for node_id in mod_telemetry:
                if "strain_microstrain" in mod_telemetry[node_id]:
                    mod_telemetry[node_id]["strain_microstrain"] *= 2.2

        elif stype == ScenarioType.TELEMETRY_FAILURE:
            # Telemetry reliability drops significantly; corrupt sensor feeds
            telemetry_reliability = 0.25
            for node_id in mod_telemetry:
                # Corrupt readings with extreme noise or drop them
                if "vibration_hz" in mod_telemetry[node_id]:
                    mod_telemetry[node_id]["vibration_hz"] = 85.0  # Erroneous spike

        elif stype == ScenarioType.POWER_FAILURE:
            # Trip 75% of nodes OFFLINE
            for i, n in enumerate(mod_nodes):
                if i % 4 != 0:  # 3 out of 4 nodes fail
                    n.operating_state = "OFFLINE"
                    n.health_score = 0.0
                    n.efficiency = 0.0

        elif stype == ScenarioType.EMERGENCY:
            # Compound disaster: Structural overload + nodal failure + severe vibration & deflection
            for m in mod_members:
                m["live_load_kn"] = m.get("live_load_kn", 300.0) * 6.0
            if mod_nodes:
                mod_nodes[0].operating_state = "FAILED"
                mod_nodes[0].health_score = 0.0
                mod_nodes[0].efficiency = 0.0
            for node_id in mod_telemetry:
                mod_telemetry[node_id]["strain_microstrain"] = 1800.0
                mod_telemetry[node_id]["vibration_hz"] = 65.0
                mod_telemetry[node_id]["inclination_deg"] = 0.55

        return mod_nodes, mod_members, mod_telemetry, mod_target, telemetry_reliability
