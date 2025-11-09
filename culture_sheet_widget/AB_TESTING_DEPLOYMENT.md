# A/B Testing Edge Functions Deployment

## Overview
The A/B testing system requires three edge functions to be deployed to Supabase. The frontend is already integrated to call these functions via `src/lib/abTestingApi.ts`.

## Status
⚠️ **Supabase Project is Currently INACTIVE**

**Project ID:** `osuffulpfwdndathiaik`

The edge functions are ready to deploy but the Supabase project needs to be activated first.

### To Activate Your Project:
1. Go to https://supabase.com/dashboard/project/osuffulpfwdndathiaik
2. Click on the "Restore Project" or "Activate Project" button
3. Wait for the project to become active (this may take a few minutes)
4. Once active, return here to deploy the edge functions

### Deployment Attempts:
- ❌ `record-test-event` - Failed (project inactive)
- ❌ `calculate-significance` - Failed (project inactive)
- ❌ `promote-winner` - Failed (project inactive)

**Next Step:** Activate the Supabase project, then re-run the deployment.


## Edge Functions to Deploy

### 1. record-test-event
Records user interactions with email templates during A/B tests.

**Create file:** `supabase/functions/record-test-event/index.ts`

```typescript
export const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type'
};

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { testId, variantName, userId, email, eventType, metadata } = await req.json();

    if (!testId || !variantName || !eventType) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { 'Content-Type': 'application/json', ...corsHeaders } }
      );
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    const eventResponse = await fetch(`${supabaseUrl}/rest/v1/ab_test_events`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Prefer': 'return=minimal'
      },
      body: JSON.stringify({
        test_id: testId,
        variant_name: variantName,
        user_id: userId,
        email: email,
        event_type: eventType,
        event_metadata: metadata || {}
      })
    });

    if (!eventResponse.ok) {
      throw new Error(`Failed to insert event: ${await eventResponse.text()}`);
    }

    return new Response(
      JSON.stringify({ success: true }),
      { headers: { 'Content-Type': 'application/json', ...corsHeaders } }
    );
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders } }
    );
  }
});
```

**Deploy:** `supabase functions deploy record-test-event`

### 2. calculate-significance
Calculates statistical significance using chi-square test.

**Create file:** `supabase/functions/calculate-significance/index.ts`

See AB_TESTING_EDGE_FUNCTIONS.md for full code.

**Deploy:** `supabase functions deploy calculate-significance`

### 3. promote-winner
Promotes winning variant when test completes.

**Create file:** `supabase/functions/promote-winner/index.ts`

See AB_TESTING_EDGE_FUNCTIONS.md for full code.

**Deploy:** `supabase functions deploy promote-winner`

## Deployment Commands

```bash
# Deploy all functions at once
supabase functions deploy record-test-event
supabase functions deploy calculate-significance
supabase functions deploy promote-winner

# Verify deployment
supabase functions list
```

## Frontend Integration
The frontend components are already configured to call these functions:

### Files Updated:
1. **src/lib/abTestingApi.ts** - API utility functions for all three edge functions
2. **src/components/admin/ActiveTestCard.tsx** - Calls `calculateSignificance` and `promoteWinner`
3. **src/components/admin/ABTestDashboard.tsx** - Database integration for test creation and management
4. **src/components/admin/TestEventRecorder.tsx** - Hook for recording test events

### Usage Example:
```typescript
// Record an event
import { recordTestEvent } from '@/lib/abTestingApi';

await recordTestEvent({
  testId: 'test-123',
  variantName: 'A',
  email: 'user@example.com',
  eventType: 'opened',
  metadata: { campaign: 'welcome' }
});

// Calculate significance
import { calculateSignificance } from '@/lib/abTestingApi';
const result = await calculateSignificance('test-123');

// Promote winner
import { promoteWinner } from '@/lib/abTestingApi';
await promoteWinner('test-123', 'B');
```

## Testing
After deployment, test each function:

```bash
# Test record-test-event
curl -X POST https://YOUR_PROJECT.supabase.co/functions/v1/record-test-event \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"testId":"test-123","variantName":"A","email":"test@example.com","eventType":"opened"}'

# Test calculate-significance
curl -X POST https://YOUR_PROJECT.supabase.co/functions/v1/calculate-significance \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"testId":"test-123"}'

# Test promote-winner
curl -X POST https://YOUR_PROJECT.supabase.co/functions/v1/promote-winner \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"testId":"test-123","winnerVariant":"B"}'
```

## Next Steps
1. Activate your Supabase project
2. Run the database schema from AB_TESTING_DATABASE_SETUP.md
3. Deploy the three edge functions using the commands above
4. Test the integration in the admin dashboard
