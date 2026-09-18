import React from 'react';
import { AlertTriangle, Lock } from 'lucide-react';

export const SimulationBanner: React.FC = () => {
  return (
    <section className="safety-banner" aria-label="System Safety Invariant Notice">
      <div className="safety-banner-icon">
        <Lock size={24} />
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <h2 className="safety-banner-title">
            DIGITAL-TWIN SYSTEM BOUNDARY: IN-SILICO PHYSICS SIMULATION ONLY
          </h2>
          <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>
            <AlertTriangle size={12} />
            HARDWARE ACTUATION FORBIDDEN
          </span>
        </div>
        <p className="safety-banner-desc">
          The structural load and anti-gravity compensation subsystem functions strictly as an
          isolated in-silico mathematical simulation. All physical building integrations are restricted
          to read-only sensor telemetry, load strain calculations, and fail-safe interlock monitoring.
          No physical actuators or gravity-modifying hardware interfaces exist.
        </p>
      </div>
    </section>
  );
};
