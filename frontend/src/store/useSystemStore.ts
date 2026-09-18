import { create } from 'zustand';
import { HealthResponse, SimulationStatusResponse } from '../types';

interface SystemState {
  health: HealthResponse | null;
  simulation: SimulationStatusResponse | null;
  isLoading: boolean;
  error: string | null;
  lastChecked: string | null;
  setHealth: (health: HealthResponse) => void;
  setSimulation: (simulation: SimulationStatusResponse) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSystemStore = create<SystemState>((set) => ({
  health: null,
  simulation: null,
  isLoading: true,
  error: null,
  lastChecked: null,
  setHealth: (health) => set({ health, lastChecked: new Date().toLocaleTimeString(), error: null }),
  setSimulation: (simulation) => set({ simulation }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error, isLoading: false }),
}));
