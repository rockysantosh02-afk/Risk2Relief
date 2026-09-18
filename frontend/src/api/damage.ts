/**
 * API client functions and TanStack Query hooks for Damage Assessment & Dynamic Compensation Rules.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DamageAssessmentFormData,
  DamageAssessmentCalculationResponse,
  DamageAssessment,
  DamageCompensationRule,
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
export const useDamageRulesQuery = () => {
  return useQuery<DamageCompensationRule[]>({
    queryKey: ['damageRules'],
    queryFn: () => fetchJson<DamageCompensationRule[]>('/damage-rules'),
    staleTime: 60000,
  });
};

export const useDamageAssessmentsQuery = () => {
  return useQuery<DamageAssessment[]>({
    queryKey: ['damageAssessments'],
    queryFn: () => fetchJson<DamageAssessment[]>('/damage-assessments'),
    refetchInterval: 5000,
  });
};

export const useDamageAssessmentDetailQuery = (assessmentId?: string) => {
  return useQuery<DamageAssessment>({
    queryKey: ['damageAssessmentDetail', assessmentId],
    queryFn: () => fetchJson<DamageAssessment>(`/damage-assessments/${assessmentId}`),
    enabled: Boolean(assessmentId),
  });
};

// Mutations
export const useCalculateDamageMutation = () => {
  return useMutation<DamageAssessmentCalculationResponse, Error, DamageAssessmentFormData>({
    mutationFn: (formData) => {
      return fetchJson<DamageAssessmentCalculationResponse>('/damage-assessments/calculate', {
        method: 'POST',
        body: JSON.stringify(formData),
      });
    },
  });
};

export const useSubmitDamageAssessmentMutation = () => {
  const queryClient = useQueryClient();

  return useMutation<DamageAssessment, Error, DamageAssessmentFormData>({
    mutationFn: (formData) => {
      return fetchJson<DamageAssessment>('/damage-assessments', {
        method: 'POST',
        body: JSON.stringify(formData),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['damageAssessments'] });
      queryClient.invalidateQueries({ queryKey: ['auditTrail'] });
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] });
    },
  });
};
