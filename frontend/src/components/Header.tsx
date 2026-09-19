import React, { useState, useEffect } from 'react';
import { Activity, LogIn, LogOut, Shield } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { logOut } from '../api/firebase';
import { Risk2ReliefLogo } from './Risk2ReliefLogo';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  const [currentTime, setCurrentTime] = useState<string>('');
  const { user, status, openAuthModal } = useAuthStore();

  useEffect(() => {
    const update = () => setCurrentTime(new Date().toUTCString().slice(17, 25) + ' UTC');
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = async () => {
    try {
      await logOut();
    } catch (err) {
      console.warn('Logout error:', err);
    }
  };

  const navItems = [
    { id: 'overview', label: 'Overview & KPIs' },
    { id: 'pipeline', label: 'Live Decision Pipeline' },
    { id: 'assessment', label: 'Damage Assessment & Relief' },
    { id: 'sources', label: 'Climate Sources' },
    { id: 'policies', label: 'Insurance Policies' },
    { id: 'settlements', label: 'Simulated Settlements' },
    { id: 'audit', label: 'Decision Audit Trail' },
  ];

  return (
    <header className="glass-panel header-container">
      <div className="header-top">
        <div className="brand-section">
          <Risk2ReliefLogo
            height={50}
            className="header-brand-logo"
            style={{
              maxHeight: '50px',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.4)',
              background: '#000000',
              padding: '2px',
            }}
          />
          <div>
            <h1 className="brand-title">RISK2RELIEF</h1>
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

          {/* Firebase Authentication Status / Action */}
          {status === 'AUTHENTICATED' && user ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.6rem',
                background: 'rgba(15, 23, 42, 0.7)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                padding: '0.3rem 0.6rem 0.3rem 0.75rem',
                borderRadius: '9999px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Shield size={13} color="#38bdf8" />
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {user.displayName || user.email?.split('@')[0]}
                </span>
                <span
                  style={{
                    fontSize: '0.65rem',
                    fontFamily: 'var(--font-mono)',
                    color: '#38bdf8',
                    background: 'rgba(56, 189, 248, 0.15)',
                    padding: '0.1rem 0.35rem',
                    borderRadius: '4px',
                  }}
                >
                  {user.uid.slice(0, 6)}...
                </span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                title="Sign Out"
                style={{
                  background: 'rgba(239, 68, 68, 0.15)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#f87171',
                  borderRadius: '50%',
                  width: '24px',
                  height: '24px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                <LogOut size={12} />
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-primary"
              onClick={openAuthModal}
              style={{
                fontSize: '0.75rem',
                padding: '0.35rem 0.75rem',
                borderRadius: '9999px',
                gap: '0.4rem',
              }}
            >
              <LogIn size={13} /> Sign In
            </button>
          )}
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
