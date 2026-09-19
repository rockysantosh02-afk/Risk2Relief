import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { DemoControlPanel } from './components/DemoControlPanel';
import { PipelineVisualizer } from './components/PipelineVisualizer';
import { ExecutiveOverview } from './components/ExecutiveOverview';
import { ClimateSourcesTable } from './components/ClimateSourcesTable';
import { PoliciesView } from './components/PoliciesView';
import { SettlementsView } from './components/SettlementsView';
import { AuditTimelineView } from './components/AuditTimelineView';
import { DamageAssessmentView } from './components/DamageAssessmentView';
import { AuthModal } from './components/AuthModal';
import { useAuthStore } from './store/useAuthStore';
import { DemoScenarioResponse } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [lastScenarioResult, setLastScenarioResult] = useState<DemoScenarioResponse | null>(null);
  const initAuthListener = useAuthStore((state) => state.initAuthListener);

  useEffect(() => {
    const unsubscribe = initAuthListener();
    return () => {
      if (typeof unsubscribe === 'function') unsubscribe();
    };
  }, [initAuthListener]);

  const handleScenarioExecuted = (result: DemoScenarioResponse) => {
    setLastScenarioResult(result);
    // Automatically switch to pipeline visualizer tab if user executed a scenario
    setActiveTab('pipeline');
  };

  return (
    <div className="app-container">
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      <AuthModal />

      <main className="main-content-layout">
        {/* Sticky/Prominent Demo Control Center on Top for Judge Interaction */}
        <DemoControlPanel
          onScenarioExecuted={handleScenarioExecuted}
          activeScenarioId={lastScenarioResult?.scenario_id}
        />

        {/* Tab-driven Content Views */}
        <div className="tab-view-container">
          {activeTab === 'overview' && <ExecutiveOverview />}

          {activeTab === 'pipeline' && (
            <PipelineVisualizer scenarioResult={lastScenarioResult} />
          )}

          {activeTab === 'assessment' && <DamageAssessmentView />}

          {activeTab === 'sources' && <ClimateSourcesTable />}

          {activeTab === 'policies' && <PoliciesView />}

          {activeTab === 'settlements' && <SettlementsView />}

          {activeTab === 'audit' && <AuditTimelineView />}
        </div>
      </main>

      <footer className="footer-text">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div>
            <strong>RISK2RELIEF &bull; Parametric Climate Insurance Reliability Engine</strong>
          </div>
          <div style={{ color: 'var(--text-tertiary)' }}>
            SIMULATION MODE &bull; NO REAL MONEY MOVED &bull; SYNTHETIC DISBURSEMENTS
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
