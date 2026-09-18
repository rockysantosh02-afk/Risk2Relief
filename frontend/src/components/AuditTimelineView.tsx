import React, { useState } from 'react';
import { useAuditTrailQuery } from '../api/climate';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Clock,
  Search,
} from 'lucide-react';
import { AuditLogEntry } from '../types';

export const AuditTimelineView: React.FC = () => {
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const { data: auditLogs, isLoading, refetch, isFetching } = useAuditTrailQuery(selectedEventId || undefined);

  const getStageBadge = (stage: string) => {
    switch (stage) {
      case 'DATA_RECEIVED':
        return <span className="badge badge-primary">1. DATA_RECEIVED</span>;
      case 'VALIDATION':
        return <span className="badge badge-primary">2. VALIDATION</span>;
      case 'ML_ANOMALY_CHECK':
        return <span className="badge badge-accent">3. ML_ANOMALY_CHECK</span>;
      case 'CONSENSUS':
        return <span className="badge badge-teal">4. CONSENSUS</span>;
      case 'TRIGGER_EVALUATION':
        return <span className="badge badge-warning">5. TRIGGER_EVALUATION</span>;
      case 'SETTLEMENT_CREATED':
      case 'SETTLEMENT_COMPLETED':
        return <span className="badge badge-success">6. SETTLEMENT</span>;
      case 'SETTLEMENT_REJECTED':
        return <span className="badge badge-danger">SETTLEMENT_REJECTED</span>;
      case 'FINAL_STATUS':
      default:
        return <span className="badge badge-neutral">{stage}</span>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
      case 'PASSED':
      case 'REACHED':
      case 'COMPLETED':
      case 'TRIGGERED':
        return <CheckCircle2 size={16} color="#10b981" />;
      case 'WARNING':
      case 'FLAGGED':
      case 'DEGRADED':
      case 'NOT_TRIGGERED':
        return <AlertTriangle size={16} color="#f59e0b" />;
      case 'FAILED':
      case 'REJECTED':
      case 'BLOCKED':
        return <XCircle size={16} color="#ef4444" />;
      default:
        return <FileText size={16} color="#38bdf8" />;
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="section-container">
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Cryptographic Decision Audit Trail</h2>
          <p className="section-subtitle">
            Immutable, time-stamped lifecycle trace for every climate observation, ML anomaly score, consensus quorum, and settlement decision.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <div className="search-box">
            <Search size={14} color="#94a3b8" />
            <input
              type="text"
              placeholder="Filter by Event ID (e.g. EVT-)"
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              className="search-input"
            />
          </div>
          <button
            className="btn btn-secondary"
            onClick={() => refetch()}
            disabled={isFetching}
            style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <RefreshCw size={14} className={isFetching ? 'spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading audit ledger...</p>
        </div>
      ) : (
        <div className="audit-timeline-wrapper">
          {auditLogs && auditLogs.length > 0 ? (
            <div className="timeline-container">
              {auditLogs.map((entry: AuditLogEntry, idx: number) => {
                const isExpanded = expandedId === entry.id;
                return (
                  <div key={entry.id || idx} className="timeline-item">
                    <div className="timeline-marker">
                      {getStatusIcon(entry.status)}
                    </div>
                    <div className="timeline-content glass-card">
                      <div className="timeline-header" onClick={() => toggleExpand(entry.id)}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                          {getStageBadge(entry.stage)}
                          <span className="mono-code" style={{ fontSize: '0.8rem', color: '#38bdf8' }}>
                            {entry.event_identifier}
                          </span>
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                            {entry.title}
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                            <Clock size={12} />
                            {new Date(entry.timestamp).toLocaleTimeString()}
                          </div>
                          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        </div>
                      </div>

                      <div className="timeline-body">
                        <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          {entry.message}
                        </p>
                        <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                          <span>Actor: <strong style={{ color: 'var(--text-secondary)' }}>{entry.actor}</strong></span>
                          {entry.correlation_id && (
                            <span>Correlation: <span className="mono-code" style={{ fontSize: '0.7rem' }}>{entry.correlation_id.slice(0, 12)}...</span></span>
                          )}
                        </div>
                      </div>

                      {isExpanded && entry.metadata && (
                        <div className="timeline-metadata-drawer">
                          <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-teal)', marginBottom: '0.4rem' }}>
                            EVENT METADATA & TELEMETRY PAYLOAD:
                          </div>
                          <pre className="json-viewer">
                            {JSON.stringify(entry.metadata, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <FileText size={32} color="#94a3b8" />
              <p>No audit trail records found. Execute demo scenarios to generate end-to-end decision logs.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
