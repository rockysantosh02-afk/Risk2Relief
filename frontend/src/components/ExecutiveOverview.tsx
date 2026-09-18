import React from 'react';
import {
  FileText,
  CloudRain,
  CreditCard,
  Percent,
  Clock,
} from 'lucide-react';
import { useDashboardSummaryQuery } from '../api/climate';

export const ExecutiveOverview: React.FC = () => {
  const { data: summary, isLoading, error } = useDashboardSummaryQuery();

  if (isLoading) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
        <p style={{ color: 'var(--text-muted)' }}>Loading live Risk2Relief metrics...</p>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="glass-panel" style={{ padding: '2rem', color: '#f87171' }}>
        <p>Failed to connect to Risk2Relief backend gateway.</p>
      </div>
    );
  }

  const kpis = [
    {
      title: 'Active Policies',
      value: summary.active_policies,
      icon: FileText,
      color: '#38bdf8',
      desc: 'Smallholder & Gig contracts',
    },
    {
      title: 'Climate Events',
      value: summary.climate_events_count,
      icon: CloudRain,
      color: '#f59e0b',
      desc: 'Monitored weather cycles',
    },
    {
      title: 'Triggered Payouts',
      value: summary.triggered_payouts_count,
      icon: CreditCard,
      color: '#10b981',
      desc: 'Automated settlements',
    },
    {
      title: 'Total Simulated Paid',
      value: `₹${(summary.total_simulated_payout_inr / 1000).toFixed(0)}k`,
      icon: CreditCard,
      color: '#38bdf8',
      desc: 'Dispatched to wallets',
    },
    {
      title: 'Settlement Success Rate',
      value: `${summary.settlement_success_rate}%`,
      icon: Percent,
      color: '#10b981',
      desc: 'Idempotency verified',
    },
    {
      title: 'Avg Pipeline Latency',
      value: `${summary.average_settlement_time_ms} ms`,
      icon: Clock,
      color: '#a855f7',
      desc: 'Telemetry to payout',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top 6 KPI Metric Cards */}
      <div className="kpi-grid">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div key={idx} className="glass-panel kpi-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {kpi.title}
                </span>
                <div style={{ padding: '0.4rem', borderRadius: '8px', background: `${kpi.color}15`, color: kpi.color }}>
                  <Icon size={18} />
                </div>
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-primary)', fontFamily: 'var(--font-sans)' }}>
                {kpi.value}
              </div>
              <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)', marginTop: '0.2rem', display: 'block' }}>
                {kpi.desc}
              </span>
            </div>
          );
        })}
      </div>

      {/* Two Column Layout: Recent Settlements + Active Monitored Events */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* Recent Settlements */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h4 style={{ fontSize: '1rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CreditCard size={18} color="#10b981" />
              Recent Simulated Settlements
            </h4>
            <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
              LIVE LEDGER
            </span>
          </div>

          {summary.recent_settlements.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.8125rem', padding: '1rem 0' }}>
              No settlements executed yet. Run <strong style={{ color: '#38bdf8' }}>Scenario 1</strong> above to trigger an automated payout.
            </p>
          ) : (
            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Txn ID</th>
                    <th>Wallet</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent_settlements.map((s, i) => (
                    <tr key={i}>
                      <td style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontSize: '0.75rem' }}>
                        {s.transaction_id}
                      </td>
                      <td style={{ fontSize: '0.775rem' }}>{s.wallet_id}</td>
                      <td style={{ fontWeight: 700, color: '#10b981' }}>
                        ₹{s.amount.toLocaleString()}
                      </td>
                      <td>
                        <span className={`badge ${s.status === 'COMPLETED' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.65rem' }}>
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Monitored Climate Events */}
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <h4 style={{ fontSize: '1rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <CloudRain size={18} color="#38bdf8" />
              Monitored Climate Events
            </h4>
            <span className="badge badge-accent" style={{ fontSize: '0.7rem' }}>
              MULTI-SOURCE
            </span>
          </div>

          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {summary.recent_events.map((evt, i) => (
                  <tr key={i}>
                    <td style={{ fontFamily: 'var(--font-mono)', color: '#38bdf8', fontSize: '0.75rem' }}>
                      {evt.event_identifier}
                    </td>
                    <td style={{ fontSize: '0.775rem', fontWeight: 600 }}>{evt.event_type}</td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{evt.location_name}</td>
                    <td>
                      <span className="badge badge-accent" style={{ fontSize: '0.65rem' }}>
                        {evt.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
