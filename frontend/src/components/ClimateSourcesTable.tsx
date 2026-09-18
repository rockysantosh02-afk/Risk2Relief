import React, { useState } from 'react';
import { useClimateSourcesQuery } from '../api/climate';
import { Radio, Satellite, Cpu, Globe, CheckCircle, AlertTriangle, RefreshCw, Layers } from 'lucide-react';
import { ClimateSource } from '../types';

export const ClimateSourcesTable: React.FC = () => {
  const { data: sources, isLoading, refetch, isFetching } = useClimateSourcesQuery();
  const [filterType, setFilterType] = useState<string>('ALL');

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'SATELLITE':
        return <Satellite size={18} color="#38bdf8" />;
      case 'GROUND_STATION':
        return <Radio size={18} color="#10b981" />;
      case 'IOT_SENSOR':
        return <Cpu size={18} color="#f59e0b" />;
      case 'WEATHER_API':
      default:
        return <Globe size={18} color="#818cf8" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ONLINE':
        return <span className="badge badge-success"><CheckCircle size={12} style={{ marginRight: '4px' }} /> ONLINE</span>;
      case 'DEGRADED':
        return <span className="badge badge-warning"><AlertTriangle size={12} style={{ marginRight: '4px' }} /> DEGRADED</span>;
      default:
        return <span className="badge badge-neutral">{status}</span>;
    }
  };

  const filteredSources = sources?.filter((s) => {
    if (filterType === 'ALL') return true;
    return s.source_type === filterType;
  });

  return (
    <div className="section-container">
      <div className="section-header-row">
        <div>
          <h2 className="section-title">Multi-Source Climate Telemetry Registry</h2>
          <p className="section-subtitle">
            Heterogeneous satellite, ground radar, IoT telemetry, and atmospheric reanalysis nodes with provenance & independence isolation.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <select
            className="filter-select"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="ALL">All Source Types</option>
            <option value="SATELLITE">Satellites</option>
            <option value="GROUND_STATION">Ground Stations</option>
            <option value="IOT_SENSOR">IoT Sensor Meshes</option>
            <option value="WEATHER_API">Multi-Model APIs</option>
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
          <p>Loading multi-source registry...</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Source Name & Provider</th>
                <th>Type</th>
                <th>Independence Group</th>
                <th>Provenance & Location</th>
                <th>Reliability Score</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredSources && filteredSources.length > 0 ? (
                filteredSources.map((source: ClimateSource) => (
                  <tr key={source.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div className="source-icon-badge">
                          {getSourceIcon(source.source_type)}
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {source.source_name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            Provider: {source.provider_name} &bull; <span className="mono-code">{source.source_identifier}</span>
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-primary">{source.source_type}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <Layers size={14} color="#38bdf8" />
                        <span style={{ fontWeight: 600, color: 'var(--accent-teal)' }}>
                          {source.independence_group}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                        Family: {source.source_family}
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{source.location_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                        {source.latitude.toFixed(4)}° N, {source.longitude.toFixed(4)}° E
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <div className="progress-bar-container">
                          <div
                            className="progress-bar-fill"
                            style={{
                              width: `${source.reliability_score * 100}%`,
                              backgroundColor:
                                source.reliability_score >= 0.95
                                  ? '#10b981'
                                  : source.reliability_score >= 0.85
                                  ? '#38bdf8'
                                  : '#f59e0b',
                            }}
                          />
                        </div>
                        <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '0.85rem' }}>
                          {(source.reliability_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td>{getStatusBadge(source.status)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    No climate sources found matching the filter.
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
