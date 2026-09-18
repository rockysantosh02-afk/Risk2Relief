import React from 'react';
import {
  Satellite,
  CheckCircle2,
  Brain,
  ShieldCheck,
  Scale,
  Zap,
  CreditCard,
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
          No Scenario Active in Decision Pipeline
        </h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '500px', margin: '0 auto' }}>
          Select a demo scenario above (e.g. <strong style={{ color: '#10b981' }}>Scenario 1: Success</strong> or <strong style={{ color: '#f59e0b' }}>Scenario 2: Disagreement</strong>) to trigger the live 7-stage reliability pipeline.
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Zap size={22} color="#38bdf8" />
            <h3 className="section-title" style={{ margin: 0 }}>
              Live Decision Pipeline Execution
            </h3>
          </div>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: '0.2rem', display: 'block' }}>
            Event: <strong style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{event_identifier}</strong> &bull; Scenario: {scenario_name}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span className="badge badge-accent" style={{ fontFamily: 'var(--font-mono)' }}>
            Latency: {execution_duration_ms} ms
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
                  <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{obs.source_identifier}</span>
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
              <h5 className="step-name">Data Validation</h5>
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

        {/* Step 3: ML Anomaly Detection */}
        <div className="step-card">
          <div className="step-header">
            <div className="step-icon-box" style={{ background: hasAnomaly ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)', color: hasAnomaly ? '#f59e0b' : '#10b981' }}>
              <Brain size={18} />
            </div>
            <div>
              <span className="step-num">STAGE 03</span>
              <h5 className="step-name">Advisory ML Anomaly</h5>
            </div>
          </div>
          <div className="step-body">
            <p style={{ fontSize: '0.775rem', color: hasAnomaly ? '#f87171' : 'var(--text-secondary)' }}>
              {hasAnomaly
                ? `Outlier flagged: ${anomaly_detection.details[0] || 'Peer deviation detected'}`
                : 'Isolation Forest verified normal cluster consistency.'}
            </p>
            <div className="step-badge-row">
              <span className={`badge ${hasAnomaly ? 'badge-danger' : 'badge-success'}`} style={{ fontSize: '0.65rem' }}>
                {hasAnomaly ? 'Anomaly Flagged' : 'Clean Cluster'}
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
                {consensus.consensus_value !== null ? `${consensus.consensus_value} mm` : 'N/A'}
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
              Rule: <strong style={{ color: 'var(--text-primary)' }}>Rainfall &ge; 150 mm</strong>
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

      {/* Decision Summary Card */}
      <div style={{ marginTop: '1.5rem', padding: '1rem 1.25rem', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '12px', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
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
