/**
 * Frontend TypeScript Types and Contracts
 */

export interface SystemDependencies {
  database: string;
  redis: string;
}

export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  service: string;
  version: string;
  timestamp: string;
  dependencies: SystemDependencies;
}

export interface SafetyBoundaryStatus {
  subsystem: "physics_simulation_digital_twin";
  simulation_only: true;
  hardware_actuators_allowed: false;
  gravity_modifying_hardware_allowed: false;
  direct_control_commands_allowed: false;
  interlock_state: "ACTIVE" | "STANDBY" | "TRIPPED";
}

export interface SimulationStatusResponse {
  status: "active" | "standby" | "tripped";
  mode: "in-silico-only";
  timestamp: string;
  active_monitored_zones: number;
  safety_boundary: SafetyBoundaryStatus;
}
