import React from 'react';
import { ShieldAlert, Cpu, Eye, Gauge } from 'lucide-react';
import { useSimulationQuery } from '../api/health';

export const SafetyIndicator: React.FC = () => {
  const { data: simulation } = useSimulationQuery();

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h3 className="section-title" style={{ margin: 0 }}>
          <ShieldAlert size={20} color="#10b981" />
          Safety Interlock & Boundary Monitor
        </h3>
        <span className="badge badge-success">
          <span className="badge-pulse" />
          Boundary Enforced
        </span>
      </div>

      <div>
        <div className="metric-row">
          <span className="metric-label">Operating Subsystem</span>
          <span className="metric-value">Digital-Twin Simulation</span>
        </div>
        <div className="metric-row">
          <span className="metric-label">Execution Mode</span>
          <span className="metric-value" style={{ color: 'var(--color-accent)' }}>
            {simulation?.mode || 'in-silico-only'}
          </span>
        </div>
        <div className="metric-row">
          <span className="metric-label">Physical Actuator Output</span>
          <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
            DISABLED (Hard Safety Invariant)
          </span>
        </div>
        <div className="metric-row">
          <span className="metric-label">Gravity-Modifying Hardware</span>
          <span className="metric-value" style={{ color: 'var(--text-muted)' }}>
            None (Software Simulation Only)
          </span>
        </div>
        <div className="metric-row">
          <span className="metric-label">Active Structural Zones</span>
          <span className="metric-value">{simulation?.active_monitored_zones ?? 4} Zones (Virtual)</span>
        </div>

        <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid rgba(51, 65, 85, 0.4)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
            Permitted Integration Channels
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <Eye size={14} color="#38bdf8" />
              <span>Telemetry Ingestion</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <Gauge size={14} color="#10b981" />
              <span>Strain Calculations</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <Cpu size={14} color="#f59e0b" />
              <span>Digital-Twin Modeling</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              <ShieldAlert size={14} color="#38bdf8" />
              <span>Safety Interlocks</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
