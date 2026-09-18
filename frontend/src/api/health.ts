import { useQuery } from '@tanstack/react-query';
import { apiFetch } from './client';
import { HealthResponse, SimulationStatusResponse } from '../types';

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

export async function fetchSimulationStatus(): Promise<SimulationStatusResponse> {
  return apiFetch<SimulationStatusResponse>('/api/v1/simulation/status');
}

export function useHealthQuery() {
  return useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchHealth,
    refetchInterval: 5000,
    retry: 2,
  });
}

export function useSimulationQuery() {
  return useQuery({
    queryKey: ['simulationStatus'],
    queryFn: fetchSimulationStatus,
    refetchInterval: 5000,
    retry: 2,
  });
}
