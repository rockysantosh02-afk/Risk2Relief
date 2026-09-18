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

import { getCurrentIdToken } from './firebase';

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
const API_BASE = `${RAW_BASE}/api/v1`;

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options?.headers as Record<string, string>) || {}),
  };

  const idToken = await getCurrentIdToken();
  if (idToken) {
    headers['Authorization'] = `Bearer ${idToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
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

export const useRunDynamicPipelineMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<DemoScenarioResponse, Error, { sat_value: number; ground_value: number; iot_value: number; policy_threshold?: number; payout_amount?: number }>({
    mutationFn: (payload) => {
      return fetchJson<DemoScenarioResponse>('/demo/dynamic-run', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
      queryClient.invalidateQueries({ queryKey: ['settlements'] });
      queryClient.invalidateQueries({ queryKey: ['auditTrail'] });
    },
  });
};

export const useSettleDamageAssessmentMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<Settlement, Error, { event_identifier: string; calculated_compensation: number; assessment_id?: string; policy_id?: string; policy_number?: string; wallet_id?: string; currency?: string; rule_code?: string }>({
    mutationFn: (payload) => {
      return fetchJson<Settlement>('/demo/settle-damage-assessment', {
        method: 'POST',
        body: JSON.stringify(payload),
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
