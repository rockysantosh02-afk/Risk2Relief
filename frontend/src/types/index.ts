/**
 * Frontend TypeScript Types and Contracts for Risk2Relief.
 */

export interface ClimateSource {
  id: string;
  source_identifier: string;
  provider_name: string;
  source_name: string;
  source_type: "SATELLITE" | "GROUND_STATION" | "IOT_SENSOR" | "WEATHER_API" | "SIMULATOR";
  source_family: string;
  independence_group: string;
  location_name: string;
  latitude: number;
  longitude: number;
  reliability_score: number;
  status: "ONLINE" | "DEGRADED" | "OFFLINE" | "CALIBRATING";
  last_seen?: string;
  metadata_json?: Record<string, any>;
}

export interface ClimateObservation {
  source_id: string;
  source_identifier?: string;
  source_name?: string;
  provider_name?: string;
  event_id: string;
  event_identifier: string;
  metric: string;
  value: number;
  unit: string;
  timestamp: string;
  quality: "VALID" | "DEGRADED" | "SUSPECT" | "INVALID" | "STALE";
  validation_status: "PASSED" | "REJECTED" | "FLAGGED";
  anomaly_score: number;
  is_anomaly: boolean;
  anomaly_reason?: string;
}

export interface ClimateEvent {
  id: string;
  event_identifier: string;
  event_type: "FLASH_FLOOD" | "EXTREME_RAINFALL" | "HEATWAVE" | "DROUGHT" | "CYCLONE";
  location_name: string;
  latitude: number;
  longitude: number;
  start_time: string;
  status: "MONITORED" | "TRIGGERED" | "SETTLED" | "CONSENSUS_FAILED" | "RESOLVED";
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  description: string;
  consensus_value?: number;
  consensus_unit: string;
  source_count: number;
  independent_source_count: number;
}

export interface InsurancePolicy {
  id: string;
  policy_number: string;
  policyholder_name: string;
  policyholder_type: "FARMER" | "GIG_WORKER" | "COOPERATIVE" | "MUNICIPALITY";
  location_name: string;
  covered_event: string;
  metric: string;
  operator: string;
  threshold: number;
  payout_amount: number;
  currency: string;
  active: boolean;
  effective_from: string;
  effective_to: string;
  wallet_id: string;
}

export interface ConsensusDecision {
  event_identifier: string;
  metric: string;
  eligible_source_count: number;
  independent_source_count: number;
  consensus_value?: number;
  consensus_method: string;
  agreement_score: number;
  confidence: number;
  status: "CONSENSUS_REACHED" | "CONSENSUS_FAILED" | "INSUFFICIENT_SOURCES" | "FLAGGED_FOR_REVIEW";
  outliers: Array<Record<string, any>>;
  rejected_sources: Array<Record<string, any>>;
  explanation: string;
}

export interface TriggerEvaluation {
  policy_id: string;
  policy_number?: string;
  event_identifier: string;
  observed_value: number;
  threshold: number;
  operator: string;
  triggered: boolean;
  difference: number;
  payout_amount: number;
  currency: string;
  reason: string;
}

export interface Settlement {
  settlement_id: string;
  policy_id: string;
  policy_number?: string;
  event_identifier: string;
  settlement_key: string;
  wallet_id: string;
  amount: number;
  currency: string;
  transaction_id: string;
  status: "COMPLETED" | "PENDING" | "BLOCKED" | "FAILED";
  failure_reason?: string;
  is_simulation: boolean;
  created_at: string;
  completed_at?: string;
}

export interface PipelineStageResult {
  stage: string;
  status: "SUCCESS" | "WARNING" | "FAILED" | "NORMAL" | "BLOCKED";
  title: string;
  message: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface DemoScenarioResponse {
  scenario_name: string;
  scenario_id: string;
  description: string;
  event_identifier: string;
  observations: ClimateObservation[];
  validation_status: string;
  anomaly_detection: {
    flagged_count: number;
    is_clean: boolean;
    details: string[];
  };
  source_independence: {
    independent_groups_count: number;
    groups: string[];
    quorum_satisfied: boolean;
  };
  consensus: ConsensusDecision;
  trigger_evaluation?: TriggerEvaluation;
  settlement?: Settlement;
  pipeline_stages: PipelineStageResult[];
  audit_trail: Array<{
    stage: string;
    status: string;
    title: string;
    message: string;
    timestamp: string;
  }>;
  execution_duration_ms: number;
  is_simulation: boolean;
  summary_message: string;
}

export interface DashboardSummary {
  active_policies: number;
  climate_events_count: number;
  validated_observations_count: number;
  triggered_payouts_count: number;
  total_simulated_payout_inr: number;
  settlement_success_rate: number;
  average_settlement_time_ms: number;
  active_climate_sources_count: number;
  recent_events: ClimateEvent[];
  recent_settlements: Settlement[];
  system_status: string;
  simulation_mode: boolean;
}

export interface AuditLogEntry {
  id: string;
  event_identifier: string;
  policy_id?: string;
  stage: string;
  status: string;
  title: string;
  message: string;
  actor: string;
  correlation_id?: string;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  service?: string;
  environment: string;
  version: string;
  timestamp: string;
  components?: Record<string, any>;
  dependencies: Record<string, any>;
}

export interface SimulationStatusResponse {
  simulation_mode: boolean;
  mode?: string;
  active_scenarios_count?: number;
  active_monitored_zones?: number;
  last_run_timestamp?: string;
}

