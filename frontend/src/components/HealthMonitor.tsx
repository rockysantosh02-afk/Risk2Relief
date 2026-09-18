import React from 'react';
import { Activity, Database, Server, RefreshCw, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useHealthQuery } from '../api/health';

export const HealthMonitor: React.FC = () => {
  const { data: health, isLoading, isError, error, refetch, isFetching } = useHealthQuery();

  const isHealthy = health?.status === 'ok';

  return (
    <div className="glass-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <h3 className="section-title" style={{ margin: 0 }}>
          <Activity size={20} color="#38bdf8" />
          Backend Health & Dependencies
        </h3>
        <button
          className="btn btn-outline"
          onClick={() => refetch()}
          disabled={isFetching}
          style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
          title="Refresh Health"
        >
          <RefreshCw size={14} className={isFetching ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div style={{ padding: '2rem 0', textAlign: 'center', color: 'var(--text-muted)' }}>
          <p>Inspecting platform services and dependencies...</p>
        </div>
      ) : isError ? (
        <div style={{ padding: '1rem', background: 'var(--color-danger-dim)', borderRadius: '8px', color: '#fca5a5' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 600 }}>
            <AlertCircle size={18} />
            Backend Disconnected
          </div>
          <p style={{ fontSize: '0.8125rem' }}>
            {error instanceof Error ? error.message : 'Unable to connect to FastAPI backend.'}
          </p>
          <p style={{ fontSize: '0.75rem', marginTop: '0.5rem', color: '#f87171' }}>
            Ensure the FastAPI server is running on port 8000.
          </p>
        </div>
      ) : (
        <div>
          <div className="metric-row">
            <span className="metric-label">Service Name</span>
            <span className="metric-value">{health?.service}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">API Status</span>
            <span className={`badge ${isHealthy ? 'badge-success' : 'badge-warning'}`}>
              <span className="badge-pulse" />
              {health?.status.toUpperCase()}
            </span>
          </div>
          <div className="metric-row">
            <span className="metric-label">API Version</span>
            <span className="metric-value">v{health?.version}</span>
          </div>
          <div className="metric-row">
            <span className="metric-label">Last Inspection</span>
            <span className="metric-value" style={{ fontSize: '0.775rem' }}>
              {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'N/A'}
            </span>
          </div>

          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px solid rgba(51, 65, 85, 0.4)' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
              Subsystem Dependencies
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '0.75rem' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <Database size={16} color="#94a3b8" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>PostgreSQL</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  {health?.dependencies.database === 'connected' ? (
                    <>
                      <CheckCircle2 size={14} color="#10b981" />
                      <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>Connected</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle size={14} color="#f59e0b" />
                      <span style={{ fontSize: '0.75rem', color: '#f59e0b', fontWeight: 600 }}>
                        {health?.dependencies.database || 'Offline'}
                      </span>
                    </>
                  )}
                </div>
              </div>

              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <Server size={16} color="#94a3b8" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>Redis Cache</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  {health?.dependencies.redis === 'connected' ? (
                    <>
                      <CheckCircle2 size={14} color="#10b981" />
                      <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 600 }}>Connected</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle size={14} color="#94a3b8" />
                      <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>
                        {health?.dependencies.redis || 'Offline'}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
