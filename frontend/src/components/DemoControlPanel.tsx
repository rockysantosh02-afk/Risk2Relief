import React from 'react';
import { Play, AlertOctagon, CheckCircle, RefreshCw, Layers, ShieldCheck } from 'lucide-react';
import { useRunScenarioMutation, useResetDemoMutation } from '../api/climate';
import { DemoScenarioResponse } from '../types';

interface DemoControlPanelProps {
  onScenarioExecuted: (result: DemoScenarioResponse) => void;
  activeScenarioId?: string;
}

export const DemoControlPanel: React.FC<DemoControlPanelProps> = ({ onScenarioExecuted, activeScenarioId }) => {
  const scenarioMutation = useRunScenarioMutation();
  const resetMutation = useResetDemoMutation();

  const handleRun = async (type: 'success' | 'disagreement' | 'no-trigger' | 'idempotency') => {
    try {
      const res = await scenarioMutation.mutateAsync(type);
      onScenarioExecuted(res);
    } catch (err) {
      console.error('Failed to execute scenario:', err);
    }
  };

  const handleReset = async () => {
    await resetMutation.mutateAsync();
  };

  const isLoading = scenarioMutation.isPending;

  return (
    <div className="glass-panel demo-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={20} color="#38bdf8" />
            <h3 className="section-title" style={{ margin: 0 }}>
              Live Demo Control Center
            </h3>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Execute real-time end-to-end pipeline scenarios against live backend consensus & settlement engines.
          </p>
        </div>

        <button
          className="btn btn-outline"
          onClick={handleReset}
          disabled={resetMutation.isPending || isLoading}
          title="Reset Demo State"
          style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
        >
          <RefreshCw size={14} className={resetMutation.isPending ? 'spin' : ''} />
          Reset Demo State
        </button>
      </div>

      <div className="demo-buttons-grid">
        {/* Scenario 1: Success */}
        <div className={`demo-card ${activeScenarioId === 'SCENARIO_1_SUCCESS' ? 'active-card' : ''}`}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>SCENARIO 1</span>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>158 / 154 / 156 mm</span>
          </div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            Corroborated Extreme Rainfall
          </h4>
          <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '1rem', minHeight: '2.4rem' }}>
            3 independent sources agree on rainfall &ge; 150mm. Triggers instant ₹25,000 payout.
          </p>
          <button
            className="btn btn-success"
            style={{ width: '100%' }}
            onClick={() => handleRun('success')}
            disabled={isLoading}
          >
            <Play size={16} />
            Run Success Scenario
          </button>
        </div>

        {/* Scenario 2: Disagreement */}
        <div className={`demo-card ${activeScenarioId === 'SCENARIO_2_DISAGREEMENT' ? 'active-card' : ''}`}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>SCENARIO 2</span>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#f87171' }}>158 / 156 / 17 mm</span>
          </div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            Data Disagreement / Anomaly
          </h4>
          <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '1rem', minHeight: '2.4rem' }}>
            IoT sensor reports 17mm. ML flags outlier, consensus fails, payout is blocked safely.
          </p>
          <button
            className="btn btn-warning"
            style={{ width: '100%' }}
            onClick={() => handleRun('disagreement')}
            disabled={isLoading}
          >
            <AlertOctagon size={16} />
            Run Disagreement Test
          </button>
        </div>

        {/* Scenario 3: No Trigger */}
        <div className={`demo-card ${activeScenarioId === 'SCENARIO_3_NO_TRIGGER' ? 'active-card' : ''}`}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span className="badge badge-neutral" style={{ fontSize: '0.7rem' }}>SCENARIO 3</span>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>120 / 118 / 121 mm</span>
          </div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            Sub-Threshold Nominal Event
          </h4>
          <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '1rem', minHeight: '2.4rem' }}>
            Consensus reaches 120mm nominal rainfall. Below 150mm threshold; ₹0 payout released.
          </p>
          <button
            className="btn btn-outline"
            style={{ width: '100%' }}
            onClick={() => handleRun('no-trigger')}
            disabled={isLoading}
          >
            <CheckCircle size={16} />
            Run No-Trigger Test
          </button>
        </div>

        {/* Scenario 4: Idempotency */}
        <div className={`demo-card ${activeScenarioId === 'SCENARIO_4_IDEMPOTENCY' ? 'active-card' : ''}`}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
            <span className="badge badge-accent" style={{ fontSize: '0.7rem' }}>SCENARIO 4</span>
            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>Retry Duplicate</span>
          </div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
            Idempotency & Retry Guard
          </h4>
          <p style={{ fontSize: '0.775rem', color: 'var(--text-secondary)', marginBottom: '1rem', minHeight: '2.4rem' }}>
            Submits same event twice. Idempotency guard suppresses duplicate payout.
          </p>
          <button
            className="btn btn-accent"
            style={{ width: '100%' }}
            onClick={() => handleRun('idempotency')}
            disabled={isLoading}
          >
            <ShieldCheck size={16} />
            Run Idempotency Test
          </button>
        </div>
      </div>
    </div>
  );
};
