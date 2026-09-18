import React from 'react';
import { Header } from './components/Header';
import { SimulationBanner } from './components/SimulationBanner';
import { HealthMonitor } from './components/HealthMonitor';
import { SafetyIndicator } from './components/SafetyIndicator';

export const App: React.FC = () => {
  return (
    <div className="app-container">
      <Header />
      <SimulationBanner />
      
      <main className="dashboard-grid">
        <HealthMonitor />
        <SafetyIndicator />
      </main>

      <footer className="footer-text">
        <p>Risk2Relief Platform &bull; Phase 1 Foundational Monorepo &bull; Physics Simulation & Digital-Twin Subsystem</p>
      </footer>
    </div>
  );
};

export default App;
