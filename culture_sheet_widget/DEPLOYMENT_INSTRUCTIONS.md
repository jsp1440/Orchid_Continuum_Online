# Email Notification System Deployment

## Overview
This application includes email notifications for culture sheet saves and weekly digests.

## Prerequisites
- Supabase CLI installed (`npm install -g supabase`)
- Supabase project set up
- Resend API key (sign up at https://resend.com)

## Step 1: Set Up Environment Variables

In your Supabase project dashboard:
1. Go to Project Settings → Edge Functions
2. Add the following secret:
   - `RESEND_API_KEY`: Your Resend API key

## Step 2: Deploy Edge Functions

### Confirmation Email Function

Create `supabase/functions/send-culture-sheet-confirmation/index.ts`:

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
    const { email, species, theme, location } = await req.json();

    const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY');
    
    const emailHtml = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #7c3aed;">Culture Sheet Saved!</h2>
        <p>Your orchid culture sheet has been saved.</p>
        <div style="background: #f3f4f6; padding: 20px; border-radius: 8px;">
          <p><strong>Species:</strong> ${species}</p>
          <p><strong>Theme:</strong> ${theme}</p>
          <p><strong>Location:</strong> ${location}</p>
        </div>
      </div>
    `;

    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RESEND_API_KEY}`
      },
      body: JSON.stringify({
        from: 'Orchid Culture <onboarding@resend.dev>',
        to: [email],
        subject: `Culture Sheet Saved: ${species}`,
        html: emailHtml
      })
    });

    const data = await res.json();
    return new Response(JSON.stringify({ success: true }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});
```

Deploy:
```bash
supabase functions deploy send-culture-sheet-confirmation
```

## Features
- Confirmation emails on save
- Weekly digest (requires cron setup)
