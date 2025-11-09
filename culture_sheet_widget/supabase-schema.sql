-- User Profiles Table
CREATE TABLE IF NOT EXISTS user_profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT,
  full_name TEXT,
  avatar_url TEXT,
  favorite_orchids TEXT[],
  email_template_preference TEXT DEFAULT 'detailed' CHECK (email_template_preference IN ('minimal', 'detailed', 'botanical')),
  email_notifications_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);

-- Saved Culture Sheets Table
CREATE TABLE IF NOT EXISTS saved_culture_sheets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  orchid_name TEXT NOT NULL,
  sheet_data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE saved_culture_sheets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own sheets" ON saved_culture_sheets FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own sheets" ON saved_culture_sheets FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own sheets" ON saved_culture_sheets FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own sheets" ON saved_culture_sheets FOR DELETE USING (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_saved_sheets_user_id ON saved_culture_sheets(user_id);
CREATE INDEX IF NOT EXISTS idx_saved_sheets_created_at ON saved_culture_sheets(created_at DESC);
