import React from 'react';
import { ShieldCheck } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="header-bar">
      <div className="brand-section">
        <div className="brand-logo">
          <ShieldCheck size={28} color="#ffffff" />
        </div>
        <div>
          <h1 className="brand-title">Risk2Relief</h1>
          <p className="brand-subtitle">
            Building-Management Digital-Twin Platform
          </p>
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <span className="badge badge-cyan">Phase 1 Foundation</span>
        <span className="badge badge-success">
          <span className="badge-pulse" />
          Simulation Engine Ready
        </span>
      </div>
    </header>
  );
};
