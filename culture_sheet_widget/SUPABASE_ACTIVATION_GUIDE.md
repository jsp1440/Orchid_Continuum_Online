# Supabase Project Activation Guide

## Current Status
🔴 **Project Status:** INACTIVE
**Project ID:** `osuffulpfwdndathiaik`

## Why Edge Functions Failed to Deploy
The Supabase project is currently in an INACTIVE state. Edge functions cannot be deployed to inactive projects.

## How to Activate Your Project

### Step 1: Access Your Supabase Dashboard
Visit: https://supabase.com/dashboard/project/osuffulpfwdndathiaik

### Step 2: Activate the Project
1. Log in to your Supabase account
2. You should see a notification that the project is paused/inactive
3. Click the **"Restore Project"** or **"Activate Project"** button
4. Wait 2-5 minutes for the project to fully activate

### Step 3: Verify Activation
Once active, you should see:
- ✅ Green status indicator
- Database is accessible
- API endpoints are responding
- Edge functions can be deployed

## After Activation: Deploy Edge Functions

Once your project is active, the three A/B testing edge functions are ready to deploy:

### Option 1: Automatic Deployment (Recommended)
The edge function code is already prepared. Simply request deployment again and the system will automatically deploy:
- `record-test-event` - Records user interactions
- `calculate-significance` - Calculates statistical significance
- `promote-winner` - Promotes winning variants

### Option 2: Manual Deployment via Supabase CLI
If you prefer manual deployment:

```bash
# Install Supabase CLI (if not already installed)
npm install -g supabase

# Link your project
supabase link --project-ref osuffulpfwdndathiaik

# Deploy functions
supabase functions deploy record-test-event
supabase functions deploy calculate-significance
supabase functions deploy promote-winner

# Verify deployment
supabase functions list
```

## Database Setup

After activation, also run the database schema:

```bash
# Connect to your Supabase project
psql postgresql://postgres:[YOUR-PASSWORD]@db.osuffulpfwdndathiaik.supabase.co:5432/postgres

# Or use the Supabase SQL Editor and paste the contents of:
# supabase-ab-testing-schema.sql
```

## Troubleshooting

### Project Won't Activate
- Check your Supabase billing status
- Ensure you have an active subscription
- Contact Supabase support if issues persist

### Edge Functions Still Won't Deploy
- Verify project is fully active (green status)
- Check that you have the correct permissions
- Ensure your Supabase CLI is up to date

## What Happens After Activation

Once activated and deployed:
1. ✅ Edge functions will be live and callable
2. ✅ Admin dashboard can create A/B tests
3. ✅ Test events will be recorded in real-time
4. ✅ Statistical significance calculations will run automatically
5. ✅ Winning variants can be promoted with one click

## Need Help?

- Supabase Documentation: https://supabase.com/docs
- Supabase Support: https://supabase.com/support
- Project Dashboard: https://supabase.com/dashboard/project/osuffulpfwdndathiaik
