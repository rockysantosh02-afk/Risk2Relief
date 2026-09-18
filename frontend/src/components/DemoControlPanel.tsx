import React, { useState } from 'react';
import { Play, AlertOctagon, CheckCircle, RefreshCw, Layers, ShieldCheck, Cpu } from 'lucide-react';
import { useRunScenarioMutation, useRunDynamicPipelineMutation, useResetDemoMutation } from '../api/climate';
import { DemoScenarioResponse } from '../types';

interface DemoControlPanelProps {
  onScenarioExecuted: (result: DemoScenarioResponse) => void;
  activeScenarioId?: string;
}

export const DemoControlPanel: React.FC<DemoControlPanelProps> = ({ onScenarioExecuted, activeScenarioId }) => {
  const scenarioMutation = useRunScenarioMutation();
  const dynamicMutation = useRunDynamicPipelineMutation();
  const resetMutation = useResetDemoMutation();

  // Dynamic Telemetry Inputs State
  const [satValue, setSatValue] = useState<number>(173.0);
  const [groundValue, setGroundValue] = useState<number>(169.0);
  const [iotValue, setIotValue] = useState<number>(171.0);
  const [policyThreshold, setPolicyThreshold] = useState<number>(150.0);

  const handleRunPreset = async (type: 'success' | 'disagreement' | 'no-trigger' | 'idempotency') => {
    try {
      const res = await scenarioMutation.mutateAsync(type);
      onScenarioExecuted(res);
    } catch (err) {
      console.error('Failed to execute scenario:', err);
    }
  };

  const handleRunDynamic = async () => {
    try {
      const res = await dynamicMutation.mutateAsync({
        sat_value: Number(satValue),
        ground_value: Number(groundValue),
        iot_value: Number(iotValue),
        policy_threshold: Number(policyThreshold),
        payout_amount: 25000.0,
      });
      onScenarioExecuted(res);
    } catch (err) {
      console.error('Failed to execute dynamic pipeline:', err);
    }
  };

  const handleReset = async () => {
    await resetMutation.mutateAsync();
  };

  const isLoading = scenarioMutation.isPending || dynamicMutation.isPending;

  return (
    <div className="glass-panel demo-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Layers size={20} color="#38bdf8" />
            <h3 className="section-title" style={{ margin: 0 }}>
              Live Decision Pipeline & Isolation Forest Control Center
            </h3>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            Submit dynamic arbitrary climate observations or run standard benchmarks scored live by scikit-learn Isolation Forest ML.
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

      {/* Dynamic Arbitrary Telemetry Input Box */}
      <div style={{ background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(56, 189, 248, 0.25)', borderRadius: '12px', padding: '1.25rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <Cpu size={18} color="#38bdf8" />
          <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
            Dynamic Multi-Source Live Telemetry Input (Arbitrary Values)
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.75rem', alignItems: 'end' }}>
          <div>
            <label style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 600, display: 'block', marginBottom: '0.3rem' }}>
              Source A (Copernicus Sat, mm)
            </label>
            <input
              type="number"
              className="input-field"
              value={satValue}
              onChange={(e) => setSatValue(parseFloat(e.target.value) || 0)}
              style={{ width: '100%', padding: '0.45rem 0.75rem', background: 'rgba(30, 41, 59, 0.8)', color: '#f8fafc', border: '1px solid #334155', borderRadius: '6px', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600, display: 'block', marginBottom: '0.3rem' }}>
              Source B (IMD Ground, mm)
            </label>
            <input
              type="number"
              className="input-field"
              value={groundValue}
              onChange={(e) => setGroundValue(parseFloat(e.target.value) || 0)}
              style={{ width: '100%', padding: '0.45rem 0.75rem', background: 'rgba(30, 41, 59, 0.8)', color: '#f8fafc', border: '1px solid #334155', borderRadius: '6px', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: 600, display: 'block', marginBottom: '0.3rem' }}>
              Source C (AgriSense IoT, mm)
            </label>
            <input
              type="number"
              className="input-field"
              value={iotValue}
              onChange={(e) => setIotValue(parseFloat(e.target.value) || 0)}
              style={{ width: '100%', padding: '0.45rem 0.75rem', background: 'rgba(30, 41, 59, 0.8)', color: '#f8fafc', border: '1px solid #334155', borderRadius: '6px', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, display: 'block', marginBottom: '0.3rem' }}>
              Trigger Threshold (mm)
            </label>
            <input
              type="number"
              className="input-field"
              value={policyThreshold}
              onChange={(e) => setPolicyThreshold(parseFloat(e.target.value) || 0)}
              style={{ width: '100%', padding: '0.45rem 0.75rem', background: 'rgba(30, 41, 59, 0.8)', color: '#f8fafc', border: '1px solid #334155', borderRadius: '6px', fontSize: '0.85rem' }}
            />
          </div>

          <div>
            <button
              className="btn btn-primary"
              style={{ width: '100%', padding: '0.5rem 1rem', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem', background: 'linear-gradient(135deg, #0284c7 0%, #2563eb 100%)' }}
              onClick={handleRunDynamic}
              disabled={isLoading}
            >
              <Cpu size={16} className={dynamicMutation.isPending ? 'spin' : ''} />
              {dynamicMutation.isPending ? 'Scoring ML...' : '⚡ Run Live Pipeline'}
            </button>
          </div>
        </div>
      </div>

      {/* Preset Scenario Cards */}
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
            3 independent sources agree on rainfall &ge; 150mm. Isolation Forest confirms clean cluster &rarr; Instant ₹25k payout.
          </p>
          <button
            className="btn btn-success"
            style={{ width: '100%' }}
            onClick={() => handleRunPreset('success')}
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
            IoT sensor reports 17mm. Isolation Forest flags outlier, consensus fails, payout blocked safely.
          </p>
          <button
            className="btn btn-warning"
            style={{ width: '100%' }}
            onClick={() => handleRunPreset('disagreement')}
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
            onClick={() => handleRunPreset('no-trigger')}
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
            onClick={() => handleRunPreset('idempotency')}
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
