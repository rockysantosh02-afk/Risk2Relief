/**
 * API client functions for Risk2Relief Climate Insurance & Demo Scenarios.
 * Native fetch-based client integrated with TanStack React Query.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DashboardSummary,
  ClimateSource,
  InsurancePolicy,
  Settlement,
  AuditLogEntry,
  DemoScenarioResponse,
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error (${response.status}): ${errorText || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

// Queries
export const useDashboardSummaryQuery = () => {
  return useQuery<DashboardSummary>({
    queryKey: ['dashboardSummary'],
    queryFn: () => fetchJson<DashboardSummary>('/dashboard/summary'),
    refetchInterval: 6000,
  });
};

export const useClimateSourcesQuery = () => {
  return useQuery<ClimateSource[]>({
    queryKey: ['climateSources'],
    queryFn: () => fetchJson<ClimateSource[]>('/climate/sources'),
    refetchInterval: 10000,
  });
};

export const usePoliciesQuery = () => {
  return useQuery<InsurancePolicy[]>({
    queryKey: ['policies'],
    queryFn: () => fetchJson<InsurancePolicy[]>('/policies'),
    refetchInterval: 10000,
  });
};

export const useSettlementsQuery = () => {
  return useQuery<Settlement[]>({
    queryKey: ['settlements'],
    queryFn: () => fetchJson<Settlement[]>('/settlements'),
    refetchInterval: 4000,
  });
};

export const useAuditTrailQuery = (eventId?: string) => {
  return useQuery<AuditLogEntry[]>({
    queryKey: ['auditTrail', eventId],
    queryFn: () => {
      const endpoint = eventId ? `/climate/audit?event_id=${encodeURIComponent(eventId)}` : '/climate/audit';
      return fetchJson<AuditLogEntry[]>(endpoint);
    },
    refetchInterval: 5000,
  });
};

// Mutations for Scenarios
export const useRunScenarioMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<DemoScenarioResponse, Error, 'success' | 'disagreement' | 'no-trigger' | 'idempotency'>({
    mutationFn: (scenarioType) => {
      return fetchJson<DemoScenarioResponse>(`/demo/scenario/${scenarioType}`, {
        method: 'POST',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      queryClient.invalidateQueries({ queryKey: ['settlements'] });
      queryClient.invalidateQueries({ queryKey: ['auditTrail'] });
    },
  });
};

export const useResetDemoMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<{ status: string; message: string }, Error>({
    mutationFn: () => {
      return fetchJson<{ status: string; message: string }>('/demo/reset', {
        method: 'POST',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      queryClient.invalidateQueries({ queryKey: ['settlements'] });
      queryClient.invalidateQueries({ queryKey: ['auditTrail'] });
    },
  });
};
