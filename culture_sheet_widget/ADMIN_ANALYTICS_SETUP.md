# Admin Analytics Dashboard Setup

## Database Setup

1. Run the SQL in `supabase-admin-analytics-schema.sql` in your Supabase SQL Editor
2. Grant admin privileges to users:
```sql
INSERT INTO admin_users (user_id) VALUES ('user-uuid-here');
```

## Edge Functions

### 1. track-email-open
Tracks email opens via 1x1 transparent tracking pixel.

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
    const url = new URL(req.url);
    const emailLogId = url.searchParams.get('id');

    if (!emailLogId) {
      const pixel = Uint8Array.from(atob('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'), c => c.charCodeAt(0));
      return new Response(pixel, {
        headers: { 'Content-Type': 'image/gif', 'Cache-Control': 'no-cache, no-store, must-revalidate' }
      });
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    
    const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
    const supabase = createClient(supabaseUrl, supabaseKey);

    await supabase.from('email_analytics').insert({
      email_log_id: emailLogId,
      event_type: 'open',
      user_agent: req.headers.get('user-agent'),
      ip_address: req.headers.get('x-forwarded-for') || req.headers.get('x-real-ip')
    });

    const pixel = Uint8Array.from(atob('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'), c => c.charCodeAt(0));
    return new Response(pixel, {
      headers: { 'Content-Type': 'image/gif', 'Cache-Control': 'no-cache, no-store, must-revalidate' }
    });
  } catch (error) {
    console.error('Error:', error);
    const pixel = Uint8Array.from(atob('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'), c => c.charCodeAt(0));
    return new Response(pixel, {
      headers: { 'Content-Type': 'image/gif', 'Cache-Control': 'no-cache, no-store, must-revalidate' }
    });
  }
});
```

### 2. track-email-click
Tracks link clicks and redirects to target URL.

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
    const url = new URL(req.url);
    const emailLogId = url.searchParams.get('id');
    const targetUrl = url.searchParams.get('url');
    const linkName = url.searchParams.get('link');

    if (!targetUrl) {
      return new Response('Missing target URL', { status: 400 });
    }

    if (emailLogId) {
      const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
      const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
      
      const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
      const supabase = createClient(supabaseUrl, supabaseKey);

      await supabase.from('email_analytics').insert({
        email_log_id: emailLogId,
        event_type: 'click',
        event_data: { link_name: linkName, target_url: targetUrl },
        user_agent: req.headers.get('user-agent'),
        ip_address: req.headers.get('x-forwarded-for') || req.headers.get('x-real-ip')
      });
    }

    return Response.redirect(targetUrl, 302);
  } catch (error) {
    console.error('Error:', error);
    return new Response('Error processing request', { status: 500 });
  }
});
```

### 3. get-email-analytics
Fetches analytics data for admin dashboard with filtering support.

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
    const authHeader = req.headers.get('Authorization');
    if (!authHeader) {
      return new Response(JSON.stringify({ error: 'No authorization header' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_ANON_KEY')!;
    
    const { createClient } = await import('https://esm.sh/@supabase/supabase-js@2');
    const supabase = createClient(supabaseUrl, supabaseKey, {
      global: { headers: { Authorization: authHeader } }
    });

    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    // Check if user is admin
    const { data: adminCheck } = await supabase
      .from('admin_users')
      .select('id')
      .eq('user_id', user.id)
      .single();

    if (!adminCheck) {
      return new Response(JSON.stringify({ error: 'Not authorized as admin' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    const { startDate, endDate, emailType, templateStyle } = await req.json();

    // Build query
    let query = supabase
      .from('email_logs')
      .select('*, email_analytics(*)');

    if (startDate) {
      query = query.gte('sent_at', startDate);
    }
    if (endDate) {
      query = query.lte('sent_at', endDate);
    }
    if (emailType) {
      query = query.eq('email_type', emailType);
    }
    if (templateStyle) {
      query = query.eq('template_style', templateStyle);
    }

    const { data: emailLogs } = await query.order('sent_at', { ascending: false });

    return new Response(JSON.stringify({ data: emailLogs }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  } catch (error) {
    console.error('Error:', error);
    return new Response(JSON.stringify({ error: 'Internal server error' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }
});
```

## Export Functionality

The admin dashboard includes CSV and PDF export capabilities:

### CSV Export
- Downloads all filtered email logs with metrics
- Includes: Email ID, Type, Template, Recipient, Sent Date, Open/Click/Unsubscribe status, Counts
- Filename format: `email-analytics-YYYY-MM-DD.csv`

### PDF Export
- Generates comprehensive report with summary metrics and detailed logs
- Includes charts and formatted tables
- Filename format: `email-analytics-YYYY-MM-DD.pdf`

### Required Dependencies
Add to package.json:
```json
{
  "dependencies": {
    "jspdf": "^2.5.1",
    "jspdf-autotable": "^3.8.2"
  }
}
```

## Email Template Updates

Add tracking to your email templates:

```html
<!-- Tracking pixel at end of email -->
<img src="https://YOUR_PROJECT.supabase.co/functions/v1/track-email-open?id=EMAIL_LOG_ID" width="1" height="1" alt="" style="display:block;border:0;outline:none;text-decoration:none;" />

<!-- Tracked links -->
<a href="https://YOUR_PROJECT.supabase.co/functions/v1/track-email-click?id=EMAIL_LOG_ID&url=TARGET_URL&link=LINK_NAME">Click here</a>
```

## Usage

1. Deploy all three edge functions
2. Update email sending functions to log emails to email_logs table with template_style field
3. Add tracking pixel and redirect URLs to email templates
4. Access admin dashboard at /admin
5. Use filters to narrow down analytics by date range, email type, and template style
6. Export reports as CSV or PDF for offline analysis
