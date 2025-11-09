# A/B Testing Edge Functions

## Overview
These edge functions handle A/B test event recording, statistical significance calculation, and automatic winner promotion.

## 1. record-test-event

Records individual user interactions with email templates during A/B tests.

**Endpoint:** `https://your-project.supabase.co/functions/v1/record-test-event`

**Method:** POST

**Body:**
```json
{
  "testId": "uuid",
  "variantName": "A" | "B",
  "userId": "uuid (optional)",
  "email": "user@example.com",
  "eventType": "sent" | "delivered" | "opened" | "clicked" | "converted" | "bounced",
  "metadata": { "any": "additional data" }
}
```

**Function Code:**
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

## 2. calculate-significance

Calculates statistical significance using chi-square test for A/B test results.

**Endpoint:** `https://your-project.supabase.co/functions/v1/calculate-significance`

**Method:** POST

**Body:**
```json
{
  "testId": "uuid"
}
```

**Function Code:**
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
    const { testId } = await req.json();
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    // Fetch test and results
    const testRes = await fetch(`${supabaseUrl}/rest/v1/ab_tests?id=eq.${testId}&select=*`, {
      headers: { 'apikey': supabaseKey, 'Authorization': `Bearer ${supabaseKey}` }
    });
    const tests = await testRes.json();
    const test = tests[0];

    const resultsRes = await fetch(`${supabaseUrl}/rest/v1/ab_test_results?test_id=eq.${testId}&select=*`, {
      headers: { 'apikey': supabaseKey, 'Authorization': `Bearer ${supabaseKey}` }
    });
    const results = await resultsRes.json();

    const variantA = results.find((r: any) => r.variant_name === 'A');
    const variantB = results.find((r: any) => r.variant_name === 'B');

    if (!variantA || !variantB) {
      return new Response(JSON.stringify({ error: 'Insufficient data' }), {
        status: 400, headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    // Chi-square test calculation
    const metricKey = test.success_metric === 'open_rate' ? 'total_opened' :
                      test.success_metric === 'click_rate' ? 'total_clicked' : 'total_converted';
    
    const successA = variantA[metricKey];
    const totalA = variantA.total_delivered;
    const successB = variantB[metricKey];
    const totalB = variantB.total_delivered;

    const failureA = totalA - successA;
    const failureB = totalB - successB;

    const totalSuccess = successA + successB;
    const totalFailure = failureA + failureB;
    const totalSamples = totalA + totalB;

    const expectedSuccessA = (totalA * totalSuccess) / totalSamples;
    const expectedFailureA = (totalA * totalFailure) / totalSamples;
    const expectedSuccessB = (totalB * totalSuccess) / totalSamples;
    const expectedFailureB = (totalB * totalFailure) / totalSamples;

    const chiSquare = 
      Math.pow(successA - expectedSuccessA, 2) / expectedSuccessA +
      Math.pow(failureA - expectedFailureA, 2) / expectedFailureA +
      Math.pow(successB - expectedSuccessB, 2) / expectedSuccessB +
      Math.pow(failureB - expectedFailureB, 2) / expectedFailureB;

    const isSignificant = chiSquare > 3.841; // 95% confidence
    const rateA = (successA / totalA) * 100;
    const rateB = (successB / totalB) * 100;
    const improvement = ((rateB - rateA) / rateA) * 100;

    // Update results
    await fetch(`${supabaseUrl}/rest/v1/ab_test_results?test_id=eq.${testId}&variant_name=eq.B`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      },
      body: JSON.stringify({
        improvement_percentage: improvement,
        confidence_level: isSignificant ? 95 : 0,
        is_significant: isSignificant
      })
    });

    return new Response(JSON.stringify({ 
      isSignificant, 
      improvement, 
      chiSquare 
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});
```

## 3. promote-winner

Automatically promotes the winning variant when a test completes.

**Endpoint:** `https://your-project.supabase.co/functions/v1/promote-winner`

**Method:** POST

**Body:**
```json
{
  "testId": "uuid",
  "winnerVariant": "A" | "B"
}
```

**Function Code:**
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
    const { testId, winnerVariant } = await req.json();
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;

    // Update test with winner
    const updateRes = await fetch(`${supabaseUrl}/rest/v1/ab_tests?id=eq.${testId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`
      },
      body: JSON.stringify({
        status: 'completed',
        winner_variant: winnerVariant,
        promoted_at: new Date().toISOString()
      })
    });

    if (!updateRes.ok) {
      throw new Error('Failed to update test');
    }

    return new Response(JSON.stringify({ 
      success: true, 
      winner: winnerVariant 
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});
```

## Deployment

Deploy these functions using the Supabase CLI:

```bash
supabase functions deploy record-test-event
supabase functions deploy calculate-significance
supabase functions deploy promote-winner
```
