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
  raw_decision_score?: number;
  ml_status?: string;
  features_used?: Record<string, number>;
  model_name?: string;
  model_version?: string;
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

export interface DynamicPipelineRequest {
  sat_value: number;
  ground_value: number;
  iot_value: number;
  policy_threshold?: number;
  payout_amount?: number;
  event_identifier?: string;
}

export interface DemoScenarioResponse {
  scenario_name: string;
  scenario_id: string;
  description: string;
  event_identifier: string;
  observations: ClimateObservation[];
  validation_status: string;
  anomaly_detection: {
    model_name?: string;
    model_version?: string;
    algorithm?: string;
    advisory_role?: string;
    status?: string;
    flagged_count: number;
    is_clean: boolean;
    details: string[];
    observations?: Array<{
      source_id: string;
      value: number;
      is_anomaly: boolean;
      anomaly_score: number;
      raw_decision_score?: number;
    }>;
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

// ---------------------------------------------------------------------------
// Damage Assessment & Dynamic Filter Types
// ---------------------------------------------------------------------------

export type ReasonForApplying =
  | 'FLOOD'
  | 'CYCLONE'
  | 'EXTREME_RAINFALL'
  | 'EXTREME_HEAT'
  | 'DROUGHT'
  | 'OTHER';

export type Occupation =
  | 'FARMER'
  | 'SHOPKEEPER'
  | 'SMALL_BUSINESS'
  | 'DAILY_WAGE_WORKER'
  | 'STREET_VENDOR'
  | 'FISHER'
  | 'TRANSPORT_WORKER'
  | 'OTHER';

export type FarmerCropType =
  | 'PADDY'
  | 'WHEAT'
  | 'SUGARCANE'
  | 'MAIZE'
  | 'COTTON'
  | 'PULSES'
  | 'VEGETABLES'
  | 'OTHER';

export type LandAreaUnit = 'ACRES' | 'CENTS';

export type DamageSeverity = 'PARTIAL' | 'MAJOR' | 'COMPLETE';

export type ShopStoreType =
  | 'GROCERY_STORE'
  | 'CLOTHING_STORE'
  | 'ELECTRONICS_STORE'
  | 'HARDWARE_STORE'
  | 'PHARMACY'
  | 'RESTAURANT_FOOD'
  | 'STATIONERY_STORE'
  | 'MOBILE_ACCESSORIES'
  | 'AGRI_INPUT_STORE'
  | 'OTHER';

export type ShopDamageCategory =
  | 'INVENTORY_DAMAGE'
  | 'PREMISES_DAMAGE'
  | 'EQUIPMENT_DAMAGE'
  | 'COMPLETE_STORE_LOSS';

export type InventoryDamageBand =
  | 'BELOW_25K'
  | 'BAND_25K_50K'
  | 'BAND_50K_100K'
  | 'ABOVE_100K';

export interface DamageAssessmentFormData {
  reason_for_applying: ReasonForApplying;
  occupation: Occupation;
  applicant_name: string;
  location_name: string;
  damage_severity: DamageSeverity;
  // Farmer fields
  crop_type?: FarmerCropType;
  damaged_area?: number;
  damaged_area_unit?: LandAreaUnit;
  affected_percentage?: number;
  // Shopkeeper fields
  store_type?: ShopStoreType;
  damage_category?: ShopDamageCategory;
  inventory_damage_band?: InventoryDamageBand;
  // Generic fields
  work_type?: string;
  loss_quantity?: number;
  policy_id?: string;
}

export interface CalculationBreakdown {
  rule_code: string;
  rule_version: string;
  reason: string;
  occupation: string;
  target_subtype?: string;
  damage_severity: string;
  original_quantity?: number;
  original_unit?: string;
  normalized_quantity: number;
  normalized_unit: string;
  rate_per_unit: number;
  formula_string: string;
  raw_calculated_amount: number;
  max_payout_cap: number;
  cap_applied: boolean;
  final_compensation_amount: number;
  currency: string;
  explanation: string;
}

export interface DamageAssessmentCalculationResponse {
  status: string;
  breakdown: CalculationBreakdown;
  is_simulation: boolean;
  disclaimer: string;
}

export interface DamageAssessment {
  id: string;
  assessment_number: string;
  policy_id?: string;
  applicant_name: string;
  location_name: string;
  reason_for_applying: string;
  occupation: string;
  crop_type?: string;
  damaged_area?: number;
  damaged_area_unit?: string;
  normalized_area_acres?: number;
  store_type?: string;
  damage_category?: string;
  inventory_damage_band?: string;
  work_type?: string;
  damage_severity: string;
  affected_percentage?: number;
  rule_code: string;
  rule_version: string;
  rate_applied: number;
  calculation_formula: string;
  calculated_amount: number;
  max_cap_applied: boolean;
  currency: string;
  explanation: string;
  status: string;
  created_at: string;
  is_simulation: boolean;
}

export interface DamageCompensationRule {
  id: string;
  rule_code: string;
  rule_version: string;
  reason_for_applying: string;
  occupation: string;
  damage_category: string;
  target_subtype?: string;
  damage_severity: string;
  calculation_type: string;
  rate_per_unit: number;
  unit_name: string;
  max_payout_amount: number;
  currency: string;
  active: boolean;
  explanation_template: string;
}


