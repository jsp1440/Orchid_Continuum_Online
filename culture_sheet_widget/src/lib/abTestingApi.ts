import { supabase } from './supabase';

export interface RecordEventParams {
  testId: string;
  variantName: 'A' | 'B';
  userId?: string;
  email: string;
  eventType: 'sent' | 'delivered' | 'opened' | 'clicked' | 'converted' | 'bounced';
  metadata?: Record<string, any>;
}

export interface CalculateSignificanceResult {
  isSignificant: boolean;
  improvement: number;
  chiSquare: number;
}

export interface PromoteWinnerResult {
  success: boolean;
  winner: 'A' | 'B';
}

export async function recordTestEvent(params: RecordEventParams) {
  const { data, error } = await supabase.functions.invoke('record-test-event', {
    body: params,
  });

  if (error) throw error;
  return data;
}

export async function calculateSignificance(testId: string): Promise<CalculateSignificanceResult> {
  const { data, error } = await supabase.functions.invoke('calculate-significance', {
    body: { testId },
  });

  if (error) throw error;
  return data;
}

export async function promoteWinner(testId: string, winnerVariant: 'A' | 'B'): Promise<PromoteWinnerResult> {
  const { data, error } = await supabase.functions.invoke('promote-winner', {
    body: { testId, winnerVariant },
  });

  if (error) throw error;
  return data;
}
