import React, { useState } from 'react';
import { usePoliciesQuery } from '../api/climate';
import { ShieldCheck, UserCheck, MapPin, Gauge, Wallet, Calendar, AlertCircle, RefreshCw } from 'lucide-react';
import { InsurancePolicy } from '../types';

export const PoliciesView: React.FC = () => {
  const { data: policies, isLoading, refetch, isFetching } = usePoliciesQuery();
  const [filterType, setFilterType] = useState<string>('ALL');

  const filteredPolicies = policies?.filter((p) => {
    if (filterType === 'ALL') return true;
    return p.policyholder_type === filterType;
  });

  return (
    <div className="section-container">
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Parametric Insurance Policy Registry</h2>
          <p className="section-subtitle">
            Autonomous smart policies with deterministic trigger thresholds, instant payouts, and zero manual claims processing.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select
            className="filter-select"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="ALL">All Beneficiary Types</option>
            <option value="FARMER">Smallholder Farmers</option>
            <option value="GIG_WORKER">Gig Economy Couriers</option>
            <option value="COOPERATIVE">Agricultural Cooperatives</option>
          </select>
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
          <p>Loading active policies...</p>
        </div>
      ) : (
        <div className="policies-grid">
          {filteredPolicies && filteredPolicies.length > 0 ? (
            filteredPolicies.map((policy: InsurancePolicy) => (
              <div key={policy.id} className="glass-card policy-card">
                <div className="policy-card-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <ShieldCheck size={20} color="#38bdf8" />
                    <span className="mono-code" style={{ fontWeight: 700, fontSize: '0.95rem' }}>
                      {policy.policy_number}
                    </span>
                  </div>
                  <span className={`badge ${policy.active ? 'badge-success' : 'badge-neutral'}`}>
                    {policy.active ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>

                <div className="policy-card-body">
                  <div className="policy-detail-row">
                    <div className="policy-detail-label">
                      <UserCheck size={14} /> Policyholder
                    </div>
                    <div className="policy-detail-value">
                      <strong>{policy.policyholder_name}</strong>
                      <span className="badge badge-primary" style={{ fontSize: '0.65rem', marginLeft: '6px' }}>
                        {policy.policyholder_type}
                      </span>
                    </div>
                  </div>

                  <div className="policy-detail-row">
                    <div className="policy-detail-label">
                      <MapPin size={14} /> Location
                    </div>
                    <div className="policy-detail-value">{policy.location_name}</div>
                  </div>

                  <div className="policy-trigger-banner">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--accent-teal)', marginBottom: '0.25rem' }}>
                      <Gauge size={16} />
                      <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>Deterministic Trigger Condition</span>
                    </div>
                    <div style={{ fontSize: '1.05rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {policy.metric} {policy.operator} {policy.threshold} mm
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Event Type: <strong>{policy.covered_event}</strong>
                    </div>
                  </div>

                  <div className="payout-box">
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Instant Payout</div>
                      <div className="payout-amount">
                        ₹{policy.payout_amount.toLocaleString()} <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>{policy.currency}</span>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px', justifyContent: 'flex-end' }}>
                        <Wallet size={12} /> Synthetic Wallet
                      </div>
                      <div className="mono-code" style={{ fontSize: '0.75rem', color: 'var(--accent-teal)', marginTop: '2px' }}>
                        {policy.wallet_id}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="policy-card-footer">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    <Calendar size={12} /> Effective: {new Date(policy.effective_from).toLocaleDateString()} &ndash; {new Date(policy.effective_to).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
              <AlertCircle size={32} color="#94a3b8" />
              <p>No insurance policies registered.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
