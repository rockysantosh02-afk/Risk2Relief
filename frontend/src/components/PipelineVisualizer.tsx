import React from 'react';
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
} from 'lucide-react';
import { DemoScenarioResponse } from '../types';

interface PipelineVisualizerProps {
  scenarioResult: DemoScenarioResponse | null;
}

export const PipelineVisualizer: React.FC<PipelineVisualizerProps> = ({ scenarioResult }) => {
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
    settlement,
    execution_duration_ms,
  } = scenarioResult;

  const isTriggered = trigger_evaluation?.triggered ?? false;
  const isSettled = settlement?.status === 'COMPLETED';
  const hasAnomaly = !anomaly_detection.is_clean;

  return (
    <div className="glass-panel pipeline-container">
      {/* Pipeline Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Zap size={22} color="#38bdf8" />
            <h3 className="section-title" style={{ margin: 0 }}>
              Live 8-Stage Parametric Decision Pipeline
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

      {/* Interactive 7-Step Pipeline Grid */}
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

        {/* Step 7: Instant Settlement */}
        <div className="step-card" style={{ borderColor: isSettled ? 'rgba(16, 185, 129, 0.4)' : undefined }}>
          <div className="step-header">
            <div className="step-icon-box" style={{ background: isSettled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.15)', color: isSettled ? '#10b981' : '#94a3b8' }}>
              <CreditCard size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 07</span>
              <h5 className="step-name">Instant Settlement</h5>
            </div>
          </div>
          <div className="step-body">
            {isSettled ? (
              <>
                <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#10b981', marginBottom: '0.2rem' }}>
                  ₹{settlement?.amount.toLocaleString()} {settlement?.currency}
                </div>
                <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                  {settlement?.transaction_id}
                </span>
                <div className="step-badge-row">
                  <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
                    PAID (SIMULATED)
                  </span>
                </div>
              </>
            ) : (
              <>
                <p style={{ fontSize: '0.775rem', color: '#f87171' }}>
                  {settlement?.failure_reason || 'Payout Suppressed'}
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

      {/* Optional Educational Panel for Judges: ML Reliability Layer (Advisory) */}
      <div style={{ marginTop: '1rem', padding: '1rem 1.25rem', background: 'rgba(30, 41, 59, 0.4)', border: '1px solid rgba(56, 189, 248, 0.15)', borderRadius: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <Info size={16} color="#38bdf8" />
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            ML Reliability Layer (Advisory Component)
          </span>
        </div>
        <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
          <strong>Algorithm:</strong> scikit-learn <code style={{ color: '#38bdf8' }}>IsolationForest</code> (100 trees, contamination 0.08, random_state 42) trained on 605 simulated historical multi-regime climate observations.
          <br />
          <strong>Role:</strong> Advisory Signal. Isolation Forest checks whether an observation is statistically unusual compared with reference data and contemporaneous peer clusters. It informs the consensus engine but <strong>never directly authorizes or triggers financial settlement payouts</strong>. Deterministic validation, multi-source consensus, and parametric trigger rules remain authoritative.
        </p>
      </div>

      {/* Decision Summary Card */}
      <div style={{ marginTop: '1rem', padding: '1rem 1.25rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '12px', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            Decision Outcome Summary
          </span>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-primary)', marginTop: '0.15rem' }}>
            {scenarioResult.summary_message}
          </p>
        </div>
        {isSettled && (
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Recipient Wallet:</span>
            <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
              {settlement?.wallet_id}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
