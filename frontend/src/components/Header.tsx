import React, { useState, useEffect } from 'react';
import { CloudRain, Activity } from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  const [currentTime, setCurrentTime] = useState<string>('');

  useEffect(() => {
    const update = () => setCurrentTime(new Date().toUTCString().slice(17, 25) + ' UTC');
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'overview', label: 'Overview & KPIs' },
    { id: 'pipeline', label: 'Live Decision Pipeline' },
    { id: 'sources', label: 'Climate Sources' },
    { id: 'policies', label: 'Insurance Policies' },
    { id: 'settlements', label: 'Simulated Settlements' },
    { id: 'audit', label: 'Decision Audit Trail' },
  ];

  return (
    <header className="glass-panel header-container">
      <div className="header-top">
        <div className="brand-section">
          <div className="brand-icon-wrapper">
            <CloudRain size={28} color="#38bdf8" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h1 className="brand-title">RISK2RELIEF</h1>
              <span className="badge badge-accent" style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }}>
                PROTOTYPE v1.0
              </span>
            </div>
            <p className="brand-subtitle">
              Autonomous Parametric Climate Insurance & Instant Settlement Reliability Engine
            </p>
          </div>
        </div>

        <div className="header-status-group">
          <div className="status-pill">
            <span className="status-dot-pulse" />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#10b981' }}>SYSTEM OPERATIONAL</span>
          </div>
          <div className="time-pill">
            <Activity size={14} color="#94a3b8" />
            <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
              {currentTime}
            </span>
          </div>
        </div>
      </div>

      <nav className="header-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-tab-btn ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
};
