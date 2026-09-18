/**
 * Risk2Relief Shared Contracts & Types
 * Cross-boundary contracts between Frontend, Backend, and Digital-Twin Simulator.
 */

export interface BuildingTelemetry {
  timestamp: string;
  sensor_id: string;
  building_id: string;
  zone_id: string;
  strain_microstrain: number;
  vibration_frequency_hz: number;
  ambient_temperature_celsius: number;
  structural_load_kn: number;
  is_synthetic: boolean;
}

export interface StructuralSafetyLimits {
  max_tensile_stress_mpa: number;
  max_compressive_stress_mpa: number;
  max_deflection_mm: number;
  interlock_trip_threshold_percentage: number;
  enforce_hardware_isolation: true;
}

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

export interface SimulationStatus {
  subsystem: "physics_simulation_digital_twin";
  mode: "in-silico-only";
  hardware_actuators_enabled: false;
  gravity_hardware_connected: false;
  active_sensors_monitored: number;
  simulated_zones: number;
  safety_interlock_active: boolean;
  status: "active" | "standby" | "tripped";
}
