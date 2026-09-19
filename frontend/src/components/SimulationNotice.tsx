import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const SimulationNotice: React.FC = () => {
  return (
    <div className="simulation-notice-banner">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <ShieldAlert size={20} color="#f59e0b" style={{ flexShrink: 0 }} />
        <div>
          <span style={{ fontWeight: 700, letterSpacing: '0.03em', textTransform: 'uppercase', fontSize: '0.8rem', color: '#f59e0b' }}>
            Simulation Mode &bull; Non-Financial Reliability Simulation Engine
          </span>
          <p style={{ fontSize: '0.8125rem', color: '#cbd5e1', marginTop: '0.1rem' }}>
            All climate telemetry, digital wallets (<code style={{ color: '#38bdf8' }}>SIM-WALLET-XXX</code>), and instant payouts (<code style={{ color: '#38bdf8' }}>SIM-TXN-XXX</code>) are simulated in software. No real fiat currency or bank accounts are accessed.
          </p>
        </div>
      </div>
    </div>
  );
};
