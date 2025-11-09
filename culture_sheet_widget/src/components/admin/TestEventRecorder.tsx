import React from 'react';
import { recordTestEvent } from '@/lib/abTestingApi';
import { toast } from 'sonner';

interface TestEventRecorderProps {
  testId: string;
  variantName: 'A' | 'B';
}

export function useTestEventRecorder(testId: string, variantName: 'A' | 'B') {
  const recordEvent = async (
    email: string,
    eventType: 'sent' | 'delivered' | 'opened' | 'clicked' | 'converted' | 'bounced',
    metadata?: Record<string, any>
  ) => {
    try {
      await recordTestEvent({
        testId,
        variantName,
        email,
        eventType,
        metadata,
      });
    } catch (error) {
      console.error('Failed to record event:', error);
    }
  };

  return { recordEvent };
}
