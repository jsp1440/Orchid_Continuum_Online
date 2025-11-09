# Email Notification System - Complete Setup Guide

## Features
1. ✅ Confirmation emails when saving culture sheets
2. ✅ Weekly digest emails with seasonal care reminders
3. ✅ Customizable email templates (minimal, detailed, botanical)
4. ✅ Opt-out capability for weekly digests
5. ✅ Unsubscribe links in digest emails
6. ✅ Admin analytics dashboard with email tracking
7. ✅ Open rate, click rate, and unsubscribe tracking


## Prerequisites
- Supabase CLI: `npm install -g supabase`
- Resend account (free): https://resend.com
- Project linked: `supabase link --project-ref YOUR_REF`

## Part 1: Resend Setup

1. Sign up at https://resend.com
2. Get API key from dashboard
3. In Supabase Dashboard → Settings → Edge Functions
4. Add secret: `RESEND_API_KEY` = your key

## Part 2: Database Schema

Run this SQL in Supabase SQL Editor:

```sql
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT true;

CREATE INDEX IF NOT EXISTS idx_user_profiles_email_notifications 
ON user_profiles(email_notifications_enabled) 
WHERE email_notifications_enabled = true;
```

## Part 3: Confirmation Email Function

### Create Directory
```bash
mkdir -p supabase/functions/send-culture-sheet-confirmation
```

### Create File
`supabase/functions/send-culture-sheet-confirmation/index.ts`:

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
    const { email, species, theme, location, userId } = await req.json();
    const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY');
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
    const SUPABASE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    
    // Get user's email template preference
    let templatePref = 'detailed';
    if (userId) {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/user_profiles?id=eq.${userId}&select=email_template_preference`, {
        headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` }
      });
      const profiles = await res.json();
      if (profiles[0]?.email_template_preference) {
        templatePref = profiles[0].email_template_preference;
      }
    }

    // Generate HTML based on template preference
    let html = '';
    if (templatePref === 'minimal') {
      html = `<div style="font-family: Arial; padding: 20px;"><h3>Culture Sheet Saved</h3><p>Your culture sheet for <strong>${species}</strong> has been saved.</p></div>`;
    } else if (templatePref === 'botanical') {
      html = `<div style="font-family: Georgia, serif; background: linear-gradient(to bottom, #f0fdf4, #dcfce7); padding: 30px; border: 2px solid #86efac;"><div style="display: flex; align-items: center; margin-bottom: 20px;"><div style="width: 50px; height: 50px; background: #16a34a; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; margin-right: 15px;">🌸</div><div><h2 style="margin: 0; color: #14532d;">Orchid Culture Sheet</h2><p style="margin: 0; color: #166534; font-style: italic;">Successfully Preserved</p></div></div><div style="background: rgba(255,255,255,0.8); padding: 20px; border-radius: 8px; border: 1px solid #86efac;"><p style="font-style: italic; color: #14532d; margin-bottom: 10px;"><em>${species}</em></p><p style="color: #374151;">Your botanical care guide has been carefully saved to your collection.</p><p style="margin-top: 15px;"><strong>Theme:</strong> ${theme}</p><p><strong>Location:</strong> ${location}</p></div></div>`;
    } else {
      html = `<div style="font-family: Arial; max-width: 600px; margin: 0 auto; background: linear-gradient(to bottom right, #eff6ff, #f3e8ff); padding: 30px; border-radius: 8px;"><h2 style="color: #1e40af; margin-bottom: 15px;">Culture Sheet Saved Successfully</h2><div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px;"><p style="color: #374151; margin-bottom: 10px;">Your culture sheet for:</p><p style="font-size: 20px; font-weight: 600; color: #7c3aed; margin-bottom: 15px;">${species}</p><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;"><div><strong>Theme:</strong> ${theme}</div><div><strong>Location:</strong> ${location}</div></div></div><p style="color: #4b5563;">Access your sheets anytime from your dashboard.</p></div>`;
    }

    await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${RESEND_API_KEY}`
      },
      body: JSON.stringify({
        from: 'Orchid Culture <onboarding@resend.dev>',
        to: [email],
        subject: `Culture Sheet Saved: ${species}`,
        html
      })
    });

    return new Response(JSON.stringify({ success: true }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});
```

### Deploy
```bash
supabase functions deploy send-culture-sheet-confirmation
```

## Part 4: Weekly Digest Function

### Create Directory
```bash
mkdir -p supabase/functions/send-weekly-digest
```

### Create File
`supabase/functions/send-weekly-digest/index.ts`:

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
    const RESEND_API_KEY = Deno.env.get('RESEND_API_KEY');
    const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
    const SUPABASE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    const APP_URL = Deno.env.get('APP_URL') || 'https://your-app.com';

    const month = new Date().getMonth();
    const season = month >= 2 && month <= 4 ? 'Spring' :
                   month >= 5 && month <= 7 ? 'Summer' :
                   month >= 8 && month <= 10 ? 'Fall' : 'Winter';

    // Only fetch users who have email notifications enabled
    const res = await fetch(`${SUPABASE_URL}/rest/v1/user_profiles?email_notifications_enabled=eq.true&select=*`, {
      headers: { 'apikey': SUPABASE_KEY, 'Authorization': `Bearer ${SUPABASE_KEY}` }
    });

    const users = await res.json();

    for (const user of users) {
      const templatePref = user.email_template_preference || 'detailed';
      const unsubscribeUrl = `${APP_URL}?openSettings=true`;
      
      // Generate HTML based on template preference with unsubscribe link
      let html = '';
      if (templatePref === 'minimal') {
        html = `<div style="padding: 20px;"><h3>Weekly Digest - ${season}</h3><p>Check your dashboard for care tips!</p><hr style="margin: 20px 0;"><p style="font-size: 12px; color: #666;"><a href="${unsubscribeUrl}">Manage email preferences</a></p></div>`;
      } else if (templatePref === 'botanical') {
        html = `<div style="font-family: Georgia, serif; background: linear-gradient(to bottom, #f0fdf4, #dcfce7); padding: 30px; border: 2px solid #86efac;"><h2 style="color: #14532d;">${season} Care Reminders</h2><p>Your orchids need special attention this season.</p><hr style="margin: 20px 0; border: none; border-top: 1px solid #86efac;"><p style="font-size: 12px; color: #166534;"><a href="${unsubscribeUrl}" style="color: #166534;">Manage email preferences</a></p></div>`;
      } else {
        html = `<div style="background: linear-gradient(to bottom right, #eff6ff, #f3e8ff); padding: 30px;"><h2 style="color: #1e40af;">Weekly Orchid Digest - ${season}</h2><p>Check your dashboard for seasonal care tips!</p><hr style="margin: 20px 0;"><p style="font-size: 12px; color: #64748b;"><a href="${unsubscribeUrl}" style="color: #64748b;">Manage email preferences</a></p></div>`;
      }

      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${RESEND_API_KEY}`
        },
        body: JSON.stringify({
          from: 'Orchid Care <onboarding@resend.dev>',
          to: [user.email],
          subject: `Weekly Orchid Digest - ${season}`,
          html
        })
      });
    }

    return new Response(JSON.stringify({ success: true, sent: users.length }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});
```

### Deploy
```bash
supabase functions deploy send-weekly-digest
```

### Setup Cron
In Supabase Dashboard → Edge Functions → Cron Jobs:
- Schedule: `0 9 * * 1` (Mondays 9 AM)
- Function: `send-weekly-digest`

## Part 5: User Preferences

Users can manage their email preferences in the Settings modal:

1. **Email Template Style**: Choose from minimal, detailed, or botanical themes
2. **Weekly Digest Toggle**: Enable/disable weekly digest emails
3. **Unsubscribe Link**: Digest emails include a link to manage preferences






## Part 6: Admin Analytics Dashboard

For detailed setup of email tracking and analytics, see `ADMIN_ANALYTICS_SETUP.md`.

Key features:
- Track email opens with tracking pixels
- Track link clicks with redirect URLs
- View open rates, click rates, and unsubscribe rates
- Admin dashboard at `/admin` route
- Filter by date range, email type (confirmation/digest), and template style
- Export analytics as CSV or PDF reports
- Time-based analytics with customizable date ranges

### CSV/PDF Export Setup

Install required dependencies:
```bash
npm install jspdf jspdf-autotable
```

The admin dashboard includes:
- **CSV Export**: Downloads filtered email logs with all metrics
- **PDF Export**: Generates comprehensive reports with summary metrics and charts
- Both exports respect current filter settings (date range, email type, template style)

## Testing
```bash
# Test confirmation
supabase functions invoke send-culture-sheet-confirmation --data '{"email":"test@example.com","species":"Phalaenopsis","theme":"Modern","location":"Indoor","userId":"user-id"}'

# Test digest
supabase functions invoke send-weekly-digest

# Test analytics
supabase functions invoke get-email-analytics
```

## Done! 🎉

