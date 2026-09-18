import React from 'react';
import { useSettlementsQuery } from '../api/climate';
import { CheckCircle2, Lock, ShieldAlert, RefreshCw, Hash, Wallet, Clock } from 'lucide-react';
import { Settlement } from '../types';

export const SettlementsView: React.FC = () => {
  const { data: settlements, isLoading, refetch, isFetching } = useSettlementsQuery();

  return (
    <div className="section-container">
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Autonomous Settlement Ledger</h2>
          <p className="section-subtitle">
            Cryptographically signed, idempotent disbursement ledger. Zero double-payouts guaranteed via deterministic idempotency keys.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
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

      <div className="simulation-notice-banner" style={{ marginBottom: '1.25rem' }}>
        <Lock size={16} />
        <span>
          <strong>SIMULATION MODE:</strong> All disbursements are synthetic transfers executed against simulated digital wallets with SHA-256 idempotency verification.
        </span>
      </div>

      {isLoading ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading settlement ledger...</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Settlement ID & Policy</th>
                <th>Event Reference</th>
                <th>Beneficiary Wallet</th>
                <th>Disbursed Amount</th>
                <th>Transaction Hash (Simulated)</th>
                <th>Idempotency Key</th>
                <th>Status</th>
                <th>Execution Time</th>
              </tr>
            </thead>
            <tbody>
              {settlements && settlements.length > 0 ? (
                settlements.map((settlement: Settlement) => (
                  <tr key={settlement.settlement_id}>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span className="mono-code">{settlement.settlement_id}</span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--accent-teal)' }}>
                        Policy: {settlement.policy_number || settlement.policy_id}
                      </div>
                    </td>
                    <td>
                      <div className="mono-code" style={{ fontSize: '0.8rem', color: '#38bdf8' }}>
                        {settlement.event_identifier}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <Wallet size={14} color="#94a3b8" />
                        <span className="mono-code" style={{ fontSize: '0.8rem' }}>
                          {settlement.wallet_id}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 700, color: '#10b981', fontSize: '0.95rem' }}>
                        ₹{settlement.amount.toLocaleString()} <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{settlement.currency}</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <Hash size={12} color="#38bdf8" />
                        <span className="mono-code" style={{ fontSize: '0.75rem', color: 'var(--accent-teal)' }}>
                          {settlement.transaction_id}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="mono-code" style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }} title={settlement.settlement_key}>
                        {settlement.settlement_key ? settlement.settlement_key.slice(0, 16) + '...' : 'N/A'}
                      </span>
                    </td>
                    <td>
                      {settlement.status === 'COMPLETED' ? (
                        <span className="badge badge-success">
                          <CheckCircle2 size={12} style={{ marginRight: '4px' }} /> COMPLETED
                        </span>
                      ) : (
                        <span className="badge badge-danger">
                          <ShieldAlert size={12} style={{ marginRight: '4px' }} /> {settlement.status}
                        </span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                        <Clock size={12} />
                        {new Date(settlement.created_at).toLocaleTimeString()}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-secondary)' }}>
                    No settlements generated yet. Execute <strong>Demo Scenario 1</strong> or <strong>Scenario 4</strong> to disburse simulated parametric payouts.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
