# Database Setup Instructions

## Setting Up Supabase Tables

To enable database save functionality and email notifications, follow these steps:

### Step 1: Create Database Tables

1. **Open Supabase Dashboard**
   - Go to [https://supabase.com](https://supabase.com)
   - Navigate to your project

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Run the Schema**
   - Open the `supabase-schema.sql` file in this project
   - Copy all the SQL code
   - Paste it into the SQL Editor
   - Click "Run" or press Ctrl/Cmd + Enter

4. **Verify Tables Created**
   - Go to "Table Editor" in the left sidebar
   - You should see two new tables:
     - `user_profiles`
     - `saved_culture_sheets`

### What Gets Created:

- **user_profiles table**: Stores user profile information including email
- **saved_culture_sheets table**: Stores saved culture sheets with all settings
- **Row Level Security (RLS)**: Ensures users can only access their own data
- **Indexes**: For better query performance
- **Triggers**: Automatically update timestamps

### Step 2: Set Up Email Notifications (Optional)

For email confirmation when saving sheets and weekly digests:

1. See `EMAIL_SETUP.md` for complete instructions
2. Requires Resend API key (free tier available)
3. Deploy edge functions using Supabase CLI

### Testing:

After running the schema:
1. Log in to your application
2. Generate a culture sheet
3. Click the "Save" button
4. Check your Dashboard to see the saved sheet
5. Check your email for confirmation (if email setup complete)
6. Try loading a saved sheet to verify all settings are restored

That's it! Your database is ready.
