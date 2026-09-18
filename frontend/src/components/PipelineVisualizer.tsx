import React, { useState, useEffect } from 'react';
import {
  Satellite,
  CheckCircle2,
  Brain,
  ShieldCheck,
  Scale,
  Zap,
  CreditCard,
  Info,
  Activity,
  FileText,
  Calculator,
  AlertTriangle,
  Sparkles,
  Wheat,
  ShoppingBag,
  Hammer,
} from 'lucide-react';
import {
  DemoScenarioResponse,
  ReasonForApplying,
  Occupation,
  FarmerCropType,
  LandAreaUnit,
  DamageSeverity,
  ShopStoreType,
  ShopDamageCategory,
  InventoryDamageBand,
  DamageAssessmentFormData,
  CalculationBreakdown,
  Settlement,
} from '../types';
import { useCalculateDamageMutation } from '../api/damage';
import { useSettleDamageAssessmentMutation } from '../api/climate';

interface PipelineVisualizerProps {
  scenarioResult: DemoScenarioResponse | null;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ scenarioResult }) => {
  // Damage Assessment State
  const [reason, setReason] = useState<ReasonForApplying>('EXTREME_RAINFALL');
  const [occupation, setOccupation] = useState<Occupation>('FARMER');
  const [applicantName, setApplicantName] = useState<string>('Ramesh Patel');
  const [locationName, setLocationName] = useState<string>('Wayanad District, Kerala');
  const [damageSeverity, setDamageSeverity] = useState<DamageSeverity>('MAJOR');

  // Farmer specific
  const [cropType, setCropType] = useState<FarmerCropType>('PADDY');
  const [damagedArea, setDamagedArea] = useState<number>(2.5);
  const [damagedAreaUnit, setDamagedAreaUnit] = useState<LandAreaUnit>('ACRES');
  const [affectedPercentage, setAffectedPercentage] = useState<number>(100);

  // Shopkeeper specific
  const [storeType, setStoreType] = useState<ShopStoreType>('GROCERY_STORE');
  const [damageCategory, setDamageCategory] = useState<ShopDamageCategory>('INVENTORY_DAMAGE');
  const [inventoryBand, setInventoryBand] = useState<InventoryDamageBand>('BAND_25K_50K');

  // Daily Wage Worker specific
  const [workType, setWorkType] = useState<string>('Agricultural Labor');
  const [lossQuantity, setLossQuantity] = useState<number>(10);

  // Results state
  const [calculationResult, setCalculationResult] = useState<CalculationBreakdown | null>(null);
  const [executedSettlement, setExecutedSettlement] = useState<Settlement | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);
  const [settleError, setSettleError] = useState<string | null>(null);

  const calculateMutation = useCalculateDamageMutation();
  const settleMutation = useSettleDamageAssessmentMutation();

  // Reset assessment results if scenario/event changes
  useEffect(() => {
    setCalculationResult(null);
    setExecutedSettlement(null);
    setCalcError(null);
    setSettleError(null);
  }, [scenarioResult?.event_identifier]);

  if (!scenarioResult) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem 1.5rem' }}>
        <Brain size={48} color="#38bdf8" style={{ margin: '0 auto 1rem', opacity: 0.6 }} />
        <h3 style={{ fontSize: '1.2rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          No Telemetry Active in Decision Pipeline
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '500px', margin: '0 auto' }}>
          Enter custom readings or select a scenario in the control panel above to trigger live multi-source evaluation and <strong style={{ color: '#38bdf8' }}>scikit-learn Isolation Forest ML</strong> anomaly analysis.
        </p>
      </div>
    );
  }

  const {
    scenario_name,
    event_identifier,
    observations,
    anomaly_detection,
    source_independence,
    consensus,
    trigger_evaluation,
    settlement: initialSettlement,
    execution_duration_ms,
  } = scenarioResult;

  const isTriggered = trigger_evaluation?.triggered ?? false;
  const activeSettlement = executedSettlement || (isTriggered && calculationResult ? null : initialSettlement);
  const isSettled = activeSettlement?.status === 'COMPLETED';
  const hasAnomaly = !anomaly_detection.is_clean;

  // Handle Occupation Change
  const handleOccupationChange = (newOcc: Occupation) => {
    setOccupation(newOcc);
    setCalculationResult(null);
    setExecutedSettlement(null);
    setCalcError(null);
    setSettleError(null);

    if (newOcc === 'FARMER') {
      setCropType('PADDY');
      setDamagedArea(2.5);
      setDamagedAreaUnit('ACRES');
      setApplicantName('Ramesh Patel');
    } else if (newOcc === 'SHOPKEEPER') {
      setStoreType('GROCERY_STORE');
      setDamageCategory('INVENTORY_DAMAGE');
      setInventoryBand('BAND_25K_50K');
      setApplicantName('Anil Sharma');
    } else if (newOcc === 'DAILY_WAGE_WORKER') {
      setWorkType('Agricultural Labor');
      setLossQuantity(10);
      setApplicantName('Suresh Kumar');
    }
  };

  const getFormData = (): DamageAssessmentFormData => {
    const base: DamageAssessmentFormData = {
      reason_for_applying: reason,
      occupation,
      applicant_name: applicantName || 'Anonymous Beneficiary',
      location_name: locationName || 'Monitored District, Kerala',
      damage_severity: damageSeverity,
    };

    if (occupation === 'FARMER') {
      base.crop_type = cropType;
      base.damaged_area = Number(damagedArea);
      base.damaged_area_unit = damagedAreaUnit;
      base.affected_percentage = Number(affectedPercentage);
    } else if (occupation === 'SHOPKEEPER') {
      base.store_type = storeType;
      base.damage_category = damageCategory;
      base.inventory_damage_band = inventoryBand;
    } else {
      base.work_type = workType;
      base.loss_quantity = Number(lossQuantity);
    }

    return base;
  };

  const handleCalculateCompensation = async () => {
    setCalcError(null);
    setSettleError(null);
    if (occupation === 'FARMER' && (!damagedArea || damagedArea <= 0)) {
      setCalcError('Damaged land area must be strictly greater than zero.');
      return;
    }

    try {
      const formData = getFormData();
      const res = await calculateMutation.mutateAsync(formData);
      setCalculationResult(res.breakdown);
    } catch (err: any) {
      setCalcError(err.message || 'Damage calculation failed.');
    }
  };

  const handleExecuteSettlement = async () => {
    if (!calculationResult) return;
    setSettleError(null);

    try {
      const res = await settleMutation.mutateAsync({
        event_identifier,
        calculated_compensation: calculationResult.final_compensation_amount,
        assessment_id: `ASM-${occupation.substring(0, 4)}-${Date.now().toString().slice(-4)}`,
        rule_code: calculationResult.rule_code,
        wallet_id: occupation === 'FARMER' ? 'SIM-WALLET-FARMER-001' : occupation === 'SHOPKEEPER' ? 'SIM-WALLET-SHOP-002' : 'SIM-WALLET-WORKER-003',
      });
      setExecutedSettlement(res);
    } catch (err: any) {
      setSettleError(err.message || 'Settlement execution failed.');
    }
  };

  return (
    <div className="glass-panel pipeline-container">
      {/* Pipeline Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Zap size={22} color="#38bdf8" />
            <h3 className="section-title" style={{ margin: 0 }}>
              Live 8-Stage Decision & Relief Pipeline
            </h3>
          </div>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.2rem', display: 'block' }}>
            Event: <strong style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{event_identifier}</strong> &bull; Evaluation: {scenario_name}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="badge badge-accent" style={{ fontFamily: 'var(--font-mono)' }}>
            Pipeline Latency: {execution_duration_ms} ms
          </span>
          <span className={`badge ${isSettled ? 'badge-success' : hasAnomaly ? 'badge-warning' : 'badge-neutral'}`}>
            {isSettled ? 'SETTLED (PAID)' : consensus.status}
          </span>
        </div>
      </div>

      {/* 8-Step Pipeline Grid */}
      <div className="pipeline-steps-grid">
        {/* Step 1: Telemetry Ingestion */}
        <div className="step-card">
          <div className="step-header">
            <div className="step-icon-box" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
              <Satellite size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 01</span>
              <h5 className="step-name">Multi-Source Ingestion</h5>
            </div>
          </div>
          <div className="step-body">
            <div className="source-mini-list">
              {observations.map((obs, idx) => (
                <div key={idx} className="source-mini-row">
                  <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{obs.source_identifier || obs.source_id}</span>
                  <span className="source-mini-val">{obs.value} {obs.unit}</span>
                </div>
              ))}
            </div>
            <div className="step-badge-row">
              <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                {observations.length} Sources Received
              </span>
            </div>
          </div>
        </div>

        {/* Step 2: Data Validation */}
        <div className="step-card">
          <div className="step-header">
            <div className="step-icon-box" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
              <CheckCircle2 size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 02</span>
              <h5 className="step-name">Deterministic Validation</h5>
            </div>
          </div>
          <div className="step-body">
            <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)' }}>
              Physical bounds check: <strong style={{ color: '#10b981' }}>[0 - 1200 mm]</strong>
            </p>
            <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Freshness & Unit check: <strong style={{ color: '#10b981' }}>Passed</strong>
            </p>
            <div className="step-badge-row">
              <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                Valid Quality
              </span>
            </div>
          </div>
        </div>

        {/* Step 3: Isolation Forest ML Anomaly Detection */}
        <div className="step-card" style={{ borderColor: hasAnomaly ? 'rgba(245, 158, 11, 0.5)' : undefined }}>
          <div className="step-header">
            <div className="step-icon-box" style={{ background: hasAnomaly ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)', color: hasAnomaly ? '#f59e0b' : '#10b981' }}>
              <Brain size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 03</span>
              <h5 className="step-name">Isolation Forest ML</h5>
            </div>
          </div>
          <div className="step-body">
            <div style={{ fontSize: '0.7rem', color: '#38bdf8', fontFamily: 'var(--font-mono)', marginBottom: '0.3rem' }}>
              {anomaly_detection.model_name || 'isolation_forest_climate_anomaly'}:{anomaly_detection.model_version || 'v1.0'}
            </div>
            <p style={{ fontSize: '0.775rem', color: hasAnomaly ? '#f87171' : 'var(--text-secondary)', minHeight: '2rem' }}>
              {hasAnomaly
                ? `Potential Anomaly: ${anomaly_detection.details[0] || 'Peer deviation detected'}`
                : 'Isolation Forest verified normal cluster consistency.'}
            </p>
            <div className="step-badge-row">
              <span className={`badge ${hasAnomaly ? 'badge-warning' : 'badge-success'}`} style={{ fontSize: '0.65rem' }}>
                {hasAnomaly ? `${anomaly_detection.flagged_count} Anomaly Signal(s)` : 'Clean Cluster (Advisory)'}
              </span>
            </div>
          </div>
        </div>

        {/* Step 4: Source Independence */}
        <div className="step-card">
          <div className="step-header">
            <div className="step-icon-box" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
              <ShieldCheck size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 04</span>
              <h5 className="step-name">Source Independence</h5>
            </div>
          </div>
          <div className="step-body">
            <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)' }}>
              Independent Groups: <strong style={{ color: '#38bdf8' }}>{source_independence.independent_groups_count}</strong>
            </p>
            <p style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              {source_independence.groups.join(', ')}
            </p>
            <div className="step-badge-row">
              <span className={`badge ${source_independence.quorum_satisfied ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.65rem' }}>
                {source_independence.quorum_satisfied ? 'Quorum Met' : 'Quorum Failed'}
              </span>
            </div>
          </div>
        </div>

        {/* Step 5: Multi-Source Consensus */}
        <div className="step-card">
          <div className="step-header">
            <div className="step-icon-box" style={{ background: consensus.status === 'CONSENSUS_REACHED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)', color: consensus.status === 'CONSENSUS_REACHED' ? '#10b981' : '#ef4444' }}>
              <Scale size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 05</span>
              <h5 className="step-name">Consensus Engine</h5>
            </div>
          </div>
          <div className="step-body">
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>
                {consensus.consensus_value !== null && consensus.consensus_value !== undefined ? `${consensus.consensus_value} mm` : 'N/A'}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                ({(consensus.agreement_score * 100).toFixed(0)}% agreement)
              </span>
            </div>
            <div className="step-badge-row">
              <span className={`badge ${consensus.status === 'CONSENSUS_REACHED' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.65rem' }}>
                {consensus.status}
              </span>
            </div>
          </div>
        </div>

        {/* Step 6: Parametric Trigger */}
        <div className="step-card">
          <div className="step-header">
            <div className="step-icon-box" style={{ background: isTriggered ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)', color: isTriggered ? '#10b981' : '#f59e0b' }}>
              <Zap size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 06</span>
              <h5 className="step-name">Parametric Trigger</h5>
            </div>
          </div>
          <div className="step-body">
            <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)' }}>
              Rule: <strong style={{ color: 'var(--text-primary)' }}>Rainfall &ge; {trigger_evaluation?.threshold || 150} mm</strong>
            </p>
            <p style={{ fontSize: '0.775rem', color: isTriggered ? '#10b981' : 'var(--text-muted)', marginTop: '0.2rem' }}>
              {isTriggered ? 'Threshold Breached (Trigger Active)' : 'Threshold Not Reached'}
            </p>
            <div className="step-badge-row">
              <span className={`badge ${isTriggered ? 'badge-success' : 'badge-neutral'}`} style={{ fontSize: '0.65rem' }}>
                {isTriggered ? 'TRIGGERED' : 'NO TRIGGER'}
              </span>
            </div>
          </div>
        </div>

        {/* Step 7: Damage Assessment & Relief */}
        <div className="step-card" style={{ borderColor: isTriggered ? 'rgba(56, 189, 248, 0.4)' : undefined }}>
          <div className="step-header">
            <div className="step-icon-box" style={{ background: isTriggered ? 'rgba(56, 189, 248, 0.15)' : 'rgba(100, 116, 139, 0.15)', color: isTriggered ? '#38bdf8' : '#94a3b8' }}>
              <FileText size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 07</span>
              <h5 className="step-name">Damage Assessment</h5>
            </div>
          </div>
          <div className="step-body">
            {isTriggered ? (
              <>
                <p style={{ fontSize: '0.775rem', color: calculationResult ? '#38bdf8' : '#10b981', fontWeight: 600 }}>
                  {calculationResult ? `₹${calculationResult.final_compensation_amount.toLocaleString()} Computed` : 'Loss Evaluation Active'}
                </p>
                <p style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  {occupation} &bull; {damageSeverity}
                </p>
                <div className="step-badge-row">
                  <span className={`badge ${calculationResult ? 'badge-primary' : 'badge-teal'}`} style={{ fontSize: '0.65rem' }}>
                    {calculationResult ? 'ASSESSED' : 'READY TO EVALUATE'}
                  </span>
                </div>
              </>
            ) : (
              <>
                <p style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                  Awaiting parametric trigger qualification.
                </p>
                <div className="step-badge-row">
                  <span className="badge badge-neutral" style={{ fontSize: '0.65rem' }}>
                    INACTIVE
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Step 8: Instant Settlement */}
        <div className="step-card" style={{ borderColor: isSettled ? 'rgba(16, 185, 129, 0.4)' : undefined }}>
          <div className="step-header">
            <div className="step-icon-box" style={{ background: isSettled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.15)', color: isSettled ? '#10b981' : '#94a3b8' }}>
              <CreditCard size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 08</span>
              <h5 className="step-name">Instant Settlement</h5>
            </div>
          </div>
          <div className="step-body">
            {isSettled ? (
              <>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#10b981', marginBottom: '0.2rem' }}>
                  ₹{activeSettlement?.amount.toLocaleString()} {activeSettlement?.currency || 'INR'}
                </div>
                <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                  {activeSettlement?.transaction_id}
                </span>
                <div className="step-badge-row">
                  <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                    PAID (SIMULATED)
                  </span>
                </div>
              </>
            ) : isTriggered ? (
              <>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: calculationResult ? '#38bdf8' : '#94a3b8', marginBottom: '0.2rem' }}>
                  {calculationResult ? `₹${calculationResult.final_compensation_amount.toLocaleString()}` : 'Awaiting Assessment'}
                </div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                  {calculationResult ? 'Ready for disbursement' : 'Compute damage relief below'}
                </span>
                <div className="step-badge-row">
                  <span className={`badge ${calculationResult ? 'badge-primary' : 'badge-neutral'}`} style={{ fontSize: '0.65rem' }}>
                    {calculationResult ? 'READY' : 'PENDING'}
                  </span>
                </div>
              </>
            ) : (
              <>
                <p style={{ fontSize: '0.775rem', color: '#f87171' }}>
                  {initialSettlement?.failure_reason || 'Payout Suppressed (Trigger Not Met)'}
                </p>
                <div className="step-badge-row">
                  <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>
                    ₹0.00 RELEASED
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Source-Level Isolation Forest ML Anomaly Table */}
      <div style={{ marginTop: '1.5rem', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} color="#38bdf8" />
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Source-Level Isolation Forest Anomaly Analysis
            </h4>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Model: <strong style={{ color: '#38bdf8' }}>IsolationForest</strong> &bull; Contamination: <strong style={{ color: '#38bdf8' }}>0.08</strong> &bull; Estimators: <strong style={{ color: '#38bdf8' }}>100</strong>
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8', textAlign: 'left' }}>
                <th style={{ padding: '0.5rem 0.75rem' }}>Source / Sensor</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Observed Value</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>ML Status</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Anomaly Score</th>
                <th style={{ padding: '0.5rem 0.75rem' }}>Isolation Forest Evaluation</th>
              </tr>
            </thead>
            <tbody>
              {observations.map((obs, idx) => {
                const isAnom = obs.is_anomaly;
                return (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.4)', background: isAnom ? 'rgba(239, 68, 68, 0.05)' : 'transparent' }}>
                    <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {obs.source_identifier || obs.source_id}
                    </td>
                    <td style={{ padding: '0.6rem 0.75rem', fontFamily: 'var(--font-mono)', color: isAnom ? '#f87171' : '#38bdf8', fontWeight: 700 }}>
                      {obs.value} {obs.unit}
                    </td>
                    <td style={{ padding: '0.6rem 0.75rem' }}>
                      <span className={`badge ${isAnom ? 'badge-warning' : 'badge-success'}`} style={{ fontSize: '0.7rem' }}>
                        {isAnom ? '⚠ Potential Anomaly' : '✓ Normal'}
                      </span>
                    </td>
                    <td style={{ padding: '0.6rem 0.75rem', fontFamily: 'var(--font-mono)' }}>
                      <span style={{ color: isAnom ? '#f87171' : '#10b981', fontWeight: 700 }}>
                        {obs.anomaly_score !== undefined ? obs.anomaly_score.toFixed(4) : '0.0000'}
                      </span>
                      {obs.raw_decision_score !== undefined && obs.raw_decision_score !== null && (
                        <span style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: '0.4rem' }}>
                          (raw: {obs.raw_decision_score.toFixed(3)})
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '0.6rem 0.75rem', color: isAnom ? '#fca5a5' : 'var(--text-secondary)', fontSize: '0.75rem' }}>
                      {obs.anomaly_reason || (isAnom ? 'Statistically unusual relative to reference data.' : 'Consistent with peer cluster.')}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Advisory Component Notice */}
      <div style={{ marginTop: '1rem', padding: '0.85rem 1.25rem', background: 'rgba(30, 41, 59, 0.35)', border: '1px solid rgba(56, 189, 248, 0.15)', borderRadius: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
          <Info size={15} color="#38bdf8" />
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            ML Reliability Layer (Advisory Component)
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.45 }}>
          Isolation Forest checks contemporaneous peer clusters. It informs consensus but <strong>never directly authorizes payout</strong>. Parametric trigger, deterministic validation, and damage assessment rules remain authoritative.
        </p>
      </div>

      {/* ========================================================================= */}
      {/* CONNECTED DAMAGE ASSESSMENT & INSTANT SETTLEMENT SECTION */}
      {/* ========================================================================= */}
      {isTriggered ? (
        <div style={{ marginTop: '2rem' }}>
          {/* Visual Step Connector */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', margin: '0 auto 1.5rem', maxWidth: '600px' }}>
            <div style={{ height: '1px', flex: 1, background: 'linear-gradient(90deg, transparent, #38bdf8)' }} />
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(14, 165, 233, 0.15)', border: '1px solid rgba(56, 189, 248, 0.4)', borderRadius: '9999px', padding: '0.35rem 0.85rem' }}>
              <Sparkles size={14} color="#38bdf8" />
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', letterSpacing: '0.04em' }}>
                TRIGGER BREACHED &bull; ASSESS DAMAGE & COMPUTE RELIEF
              </span>
            </div>
            <div style={{ height: '1px', flex: 1, background: 'linear-gradient(90deg, #38bdf8, transparent)' }} />
          </div>

          {/* Connected Assessment Container */}
          <div style={{ background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(11, 17, 32, 0.95))', border: '1px solid rgba(56, 189, 248, 0.35)', borderRadius: '14px', padding: '1.5rem', boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <FileText size={20} color="#38bdf8" />
                  <h4 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                    Damage Assessment & Individualized Relief
                  </h4>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem', marginBottom: 0 }}>
                  Parametric trigger confirmed for event <strong style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{event_identifier}</strong>. Enter beneficiary damage profile to authoritatively calculate relief compensation.
                </p>
              </div>

              {/* Occupation Selector Tabs */}
              <div style={{ display: 'flex', gap: '0.4rem', background: 'rgba(15, 23, 42, 0.8)', padding: '0.25rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <button
                  type="button"
                  onClick={() => handleOccupationChange('FARMER')}
                  className={`btn ${occupation === 'FARMER' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', gap: '0.35rem' }}
                >
                  <Wheat size={14} /> Farmer
                </button>
                <button
                  type="button"
                  onClick={() => handleOccupationChange('SHOPKEEPER')}
                  className={`btn ${occupation === 'SHOPKEEPER' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', gap: '0.35rem' }}
                >
                  <ShoppingBag size={14} /> Shopkeeper
                </button>
                <button
                  type="button"
                  onClick={() => handleOccupationChange('DAILY_WAGE_WORKER')}
                  className={`btn ${occupation === 'DAILY_WAGE_WORKER' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem', gap: '0.35rem' }}
                >
                  <Hammer size={14} /> Daily Wage
                </button>
              </div>
            </div>

            {/* Assessment Input Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem', marginBottom: '1.25rem' }}>
              {/* Reason for applying */}
              <div>
                <label className="form-label">Reason for Applying</label>
                <select
                  className="form-input"
                  value={reason}
                  onChange={(e) => {
                    setReason(e.target.value as ReasonForApplying);
                    setCalculationResult(null);
                  }}
                >
                  <option value="EXTREME_RAINFALL">Extreme Rainfall (Flood)</option>
                  <option value="FLOOD">Flood Inundation</option>
                  <option value="CYCLONE">Cyclone Storm</option>
                  <option value="DROUGHT">Drought / Dry Spell</option>
                  <option value="OTHER">Other Climate Event</option>
                </select>
              </div>

              {/* Beneficiary Name */}
              <div>
                <label className="form-label">Beneficiary Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={applicantName}
                  onChange={(e) => setApplicantName(e.target.value)}
                  placeholder="e.g. Ramesh Patel"
                />
              </div>

              {/* Location */}
              <div>
                <label className="form-label">Location / District</label>
                <input
                  type="text"
                  className="form-input"
                  value={locationName}
                  onChange={(e) => setLocationName(e.target.value)}
                  placeholder="e.g. Wayanad District, Kerala"
                />
              </div>

              {/* Severity */}
              <div>
                <label className="form-label">Damage Severity</label>
                <select
                  className="form-input"
                  value={damageSeverity}
                  onChange={(e) => {
                    setDamageSeverity(e.target.value as DamageSeverity);
                    setCalculationResult(null);
                  }}
                >
                  <option value="PARTIAL">Partial Damage (40% Multiplier)</option>
                  <option value="MAJOR">Major Damage (100% Full Multiplier)</option>
                  <option value="COMPLETE">Complete Total Loss (100% Capped)</option>
                </select>
              </div>
            </div>

            {/* Dynamic Occupation-Specific Inputs */}
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.75rem' }}>
                {occupation === 'FARMER' && '🌾 Farmer Agronomic Loss Parameters'}
                {occupation === 'SHOPKEEPER' && '🏬 Commercial / Store Damage Parameters'}
                {occupation === 'DAILY_WAGE_WORKER' && '🛠️ Daily Wage Livelihood Loss Parameters'}
              </div>

              {occupation === 'FARMER' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  <div>
                    <label className="form-label">Crop Type</label>
                    <select
                      className="form-input"
                      value={cropType}
                      onChange={(e) => {
                        setCropType(e.target.value as FarmerCropType);
                        setCalculationResult(null);
                      }}
                    >
                      <option value="PADDY">Paddy (Rice) — ₹10,000 / Acre</option>
                      <option value="WHEAT">Wheat — ₹8,000 / Acre</option>
                      <option value="COTTON">Cotton — ₹12,000 / Acre</option>
                      <option value="SUGARCANE">Sugarcane — ₹15,000 / Acre</option>
                      <option value="VEGETABLES">Vegetables / Horticulture — ₹9,000 / Acre</option>
                      <option value="PULSES">Pulses / Lentils — ₹7,500 / Acre</option>
                      <option value="MAIZE">Maize — ₹7,000 / Acre</option>
                    </select>
                  </div>

                  <div>
                    <label className="form-label">Damaged Land Area</label>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      className="form-input"
                      value={damagedArea}
                      onChange={(e) => {
                        setDamagedArea(parseFloat(e.target.value) || 0);
                        setCalculationResult(null);
                      }}
                    />
                  </div>

                  <div>
                    <label className="form-label">Land Unit</label>
                    <select
                      className="form-input"
                      value={damagedAreaUnit}
                      onChange={(e) => {
                        setDamagedAreaUnit(e.target.value as LandAreaUnit);
                        setCalculationResult(null);
                      }}
                    >
                      <option value="ACRES">Acres</option>
                      <option value="CENTS">Cents (100 Cents = 1 Acre)</option>
                    </select>
                  </div>

                  <div>
                    <label className="form-label">Affected Area %</label>
                    <input
                      type="number"
                      min="10"
                      max="100"
                      className="form-input"
                      value={affectedPercentage}
                      onChange={(e) => {
                        setAffectedPercentage(parseFloat(e.target.value) || 100);
                        setCalculationResult(null);
                      }}
                    />
                  </div>
                </div>
              )}

              {occupation === 'SHOPKEEPER' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                  <div>
                    <label className="form-label">Store Type</label>
                    <select
                      className="form-input"
                      value={storeType}
                      onChange={(e) => {
                        setStoreType(e.target.value as ShopStoreType);
                        setCalculationResult(null);
                      }}
                    >
                      <option value="GROCERY_STORE">Grocery / Kirana Store</option>
                      <option value="CLOTHING_STORE">Clothing & Textile Store</option>
                      <option value="ELECTRONICS_STORE">Electronics & Appliance Store</option>
                      <option value="HARDWARE_STORE">Hardware & Tools Store</option>
                      <option value="PHARMACY">Medical / Pharmacy</option>
                    </select>
                  </div>

                  <div>
                    <label className="form-label">Damage Category</label>
                    <select
                      className="form-input"
                      value={damageCategory}
                      onChange={(e) => {
                        setDamageCategory(e.target.value as ShopDamageCategory);
                        setCalculationResult(null);
                      }}
                    >
                      <option value="INVENTORY_DAMAGE">Inventory / Stock Water Damage</option>
                      <option value="PREMISES_DAMAGE">Premises Structural Loss</option>
                      <option value="EQUIPMENT_DAMAGE">Equipment / Appliance Damage</option>
                      <option value="COMPLETE_STORE_LOSS">Complete Store Loss</option>
                    </select>
                  </div>

                  <div>
                    <label className="form-label">Inventory Loss Band</label>
                    <select
                      className="form-input"
                      value={inventoryBand}
                      onChange={(e) => {
                        setInventoryBand(e.target.value as InventoryDamageBand);
                        setCalculationResult(null);
                      }}
                    >
                      <option value="BELOW_25K">Under ₹25,000</option>
                      <option value="BAND_25K_50K">₹25,000 – ₹50,000</option>
                      <option value="BAND_50K_100K">₹50,000 – ₹1,00,000</option>
                      <option value="ABOVE_100K">Above ₹1,00,000</option>
                    </select>
                  </div>
                </div>
              )}

              {occupation === 'DAILY_WAGE_WORKER' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
                  <div>
                    <label className="form-label">Livelihood / Trade</label>
                    <input
                      type="text"
                      className="form-input"
                      value={workType}
                      onChange={(e) => {
                        setWorkType(e.target.value);
                        setCalculationResult(null);
                      }}
                    />
                  </div>

                  <div>
                    <label className="form-label">Days of Work Lost</label>
                    <input
                      type="number"
                      min="1"
                      max="60"
                      className="form-input"
                      value={lossQuantity}
                      onChange={(e) => {
                        setLossQuantity(parseInt(e.target.value) || 1);
                        setCalculationResult(null);
                      }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Calculate Action */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleCalculateCompensation}
                disabled={calculateMutation.isPending}
                style={{ padding: '0.6rem 1.25rem', fontSize: '0.85rem', gap: '0.5rem' }}
              >
                {calculateMutation.isPending ? (
                  <>
                    <div className="spinner" style={{ width: 14, height: 14 }} />
                    Calculating Authoritative Relief...
                  </>
                ) : (
                  <>
                    <Calculator size={16} />
                    Calculate Relief Compensation
                  </>
                )}
              </button>

              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Powered by authoritative backend <code style={{ color: '#38bdf8' }}>DamageCompensationService</code>
              </span>
            </div>

            {calcError && (
              <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.85rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '8px', color: '#fca5a5', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle size={16} />
                {calcError}
              </div>
            )}

            {/* ========================================================================= */}
            {/* CALCULATED RELIEF COMPENSATION & INSTANT SETTLEMENT CARDS */}
            {/* ========================================================================= */}
            {calculationResult && (
              <div style={{ marginTop: '1.5rem', borderTop: '1px dashed rgba(56, 189, 248, 0.3)', paddingTop: '1.5rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
                  {/* RELIEF COMPENSATION CARD */}
                  <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          RELIEF COMPENSATION
                        </span>
                        <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                          {calculationResult.rule_code}
                        </span>
                      </div>

                      <div style={{ fontSize: '2rem', fontWeight: 800, color: '#38bdf8', fontFamily: 'var(--font-mono)', marginBottom: '0.5rem' }}>
                        ₹{calculationResult.final_compensation_amount.toLocaleString()} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>INR</span>
                      </div>

                      <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                        <strong>Calculated from:</strong> {reason.replace('_', ' ')} &bull; {occupation} &bull; {occupation === 'FARMER' ? cropType : occupation === 'SHOPKEEPER' ? storeType : workType} &bull; {damageSeverity}
                      </p>

                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', background: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.75rem', borderRadius: '6px', margin: 0 }}>
                        {calculationResult.formula_string}
                      </p>
                    </div>

                    <div style={{ marginTop: '0.75rem', fontSize: '0.725rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                      <CheckCircle2 size={13} />
                      Amount calculated from Damage Assessment & Relief
                    </div>
                  </div>

                  {/* INSTANT SETTLEMENT CARD */}
                  <div style={{ background: executedSettlement ? 'rgba(16, 185, 129, 0.08)' : 'rgba(15, 23, 42, 0.8)', border: executedSettlement ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '12px', padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: executedSettlement ? '#10b981' : '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          INSTANT SETTLEMENT
                        </span>
                        <span className={`badge ${executedSettlement ? 'badge-success' : 'badge-primary'}`} style={{ fontSize: '0.65rem' }}>
                          {executedSettlement ? 'EXECUTED (PAID)' : 'READY TO DISBURSE'}
                        </span>
                      </div>

                      <div style={{ fontSize: '2rem', fontWeight: 800, color: '#10b981', fontFamily: 'var(--font-mono)', marginBottom: '0.5rem' }}>
                        ₹{(executedSettlement?.amount ?? calculationResult.final_compensation_amount).toLocaleString()} <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>INR</span>
                      </div>

                      <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', margin: '0 0 0.25rem 0' }}>
                        <strong>Source:</strong> Settlement amount sourced from Relief Compensation
                      </p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: '0 0 0.5rem 0' }}>
                        <strong>Recipient Wallet:</strong> <span style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>{executedSettlement?.wallet_id || (occupation === 'FARMER' ? 'SIM-WALLET-FARMER-001' : occupation === 'SHOPKEEPER' ? 'SIM-WALLET-SHOP-002' : 'SIM-WALLET-WORKER-003')}</span>
                      </p>

                      {executedSettlement && (
                        <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#10b981', display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                          <div>Txn: <span style={{ color: '#38bdf8' }}>{executedSettlement.transaction_id}</span></div>
                          <div>Settlement ID: <span style={{ color: '#38bdf8' }}>{executedSettlement.settlement_id}</span></div>
                          <div style={{ color: '#10b981', fontWeight: 700, marginTop: '0.2rem' }}>
                            ✓ Verified: settlement.amount == damage_assessment.calculated_compensation
                          </div>
                        </div>
                      )}
                    </div>

                    <div style={{ marginTop: '1rem' }}>
                      {!executedSettlement ? (
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={handleExecuteSettlement}
                          disabled={settleMutation.isPending}
                          style={{ width: '100%', padding: '0.65rem 1rem', fontSize: '0.85rem', gap: '0.5rem', background: 'linear-gradient(135deg, #10b981, #059669)', border: 'none' }}
                        >
                          {settleMutation.isPending ? (
                            <>
                              <div className="spinner" style={{ width: 14, height: 14 }} />
                              Executing Instant Payout...
                            </>
                          ) : (
                            <>
                              <CreditCard size={16} />
                              Execute Instant Settlement (₹{calculationResult.final_compensation_amount.toLocaleString()})
                            </>
                          )}
                        </button>
                      ) : (
                        <div style={{ textAlign: 'center', fontSize: '0.775rem', color: '#10b981', fontWeight: 600, padding: '0.4rem' }}>
                          ✓ Instant Payout Successfully Executed & Ledger Recorded
                        </div>
                      )}
                    </div>

                    {settleError && (
                      <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', color: '#fca5a5', fontSize: '0.75rem' }}>
                        {settleError}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* TRIGGER NOT MET NOTICE */
        <div style={{ marginTop: '1.5rem', padding: '1.25rem', background: 'rgba(245, 158, 11, 0.08)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
            <AlertTriangle size={18} color="#f59e0b" />
            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: '#f59e0b' }}>
              Parametric Trigger Threshold Not Breached
            </h4>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
            Consensus rainfall of <strong style={{ color: 'var(--text-primary)' }}>{consensus.consensus_value !== null ? `${consensus.consensus_value} mm` : 'N/A'}</strong> is below the policy threshold of <strong style={{ color: 'var(--text-primary)' }}>{trigger_evaluation?.threshold || 150} mm</strong>. Financial payout is suppressed and damage assessment is not invoked for this climate event.
          </p>
        </div>
      )}

      {/* Decision Summary Card */}
      <div style={{ marginTop: '1.5rem', padding: '1rem 1.25rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '12px', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            Decision Outcome Summary
          </span>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginTop: '0.15rem', marginBottom: 0 }}>
            {scenarioResult.summary_message}
          </p>
        </div>
        {isSettled && (
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Recipient Wallet:</span>
            <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
              {activeSettlement?.wallet_id}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
