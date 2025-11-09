-- A/B Testing Database Schema
-- Run this in your Supabase SQL Editor

-- Create tables
CREATE TABLE IF NOT EXISTS ab_tests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  template_a_id TEXT NOT NULL,
  template_b_id TEXT NOT NULL,
  traffic_split INTEGER NOT NULL DEFAULT 50,
  success_metric TEXT NOT NULL,
  target_sample_size INTEGER DEFAULT 1000,
  confidence_level DECIMAL DEFAULT 95.0,
  start_date TIMESTAMPTZ,
  end_date TIMESTAMPTZ,
  duration_days INTEGER,
  winner_variant TEXT,
  promoted_at TIMESTAMPTZ,
  created_by UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab_test_variants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
  variant_name TEXT NOT NULL,
  template_id TEXT NOT NULL,
  template_name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab_test_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
  variant_name TEXT NOT NULL,
  total_sent INTEGER DEFAULT 0,
  total_delivered INTEGER DEFAULT 0,
  total_opened INTEGER DEFAULT 0,
  total_clicked INTEGER DEFAULT 0,
  total_converted INTEGER DEFAULT 0,
  open_rate DECIMAL DEFAULT 0,
  click_rate DECIMAL DEFAULT 0,
  conversion_rate DECIMAL DEFAULT 0,
  improvement_percentage DECIMAL DEFAULT 0,
  confidence_level DECIMAL DEFAULT 0,
  is_significant BOOLEAN DEFAULT FALSE,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(test_id, variant_name)
);

CREATE TABLE IF NOT EXISTS ab_test_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
  variant_name TEXT NOT NULL,
  user_id UUID,
  email TEXT,
  event_type TEXT NOT NULL,
  event_metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created_at ON ab_tests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ab_test_variants_test_id ON ab_test_variants(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_results_test_id ON ab_test_results(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_events_test_id ON ab_test_events(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_events_variant ON ab_test_events(test_id, variant_name);
CREATE INDEX IF NOT EXISTS idx_ab_test_events_type ON ab_test_events(event_type);
CREATE INDEX IF NOT EXISTS idx_ab_test_events_created_at ON ab_test_events(created_at DESC);

-- Enable RLS
ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_events ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Admins full access ab_tests" ON ab_tests FOR ALL TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

CREATE POLICY "Admins full access variants" ON ab_test_variants FOR ALL TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

CREATE POLICY "Admins full access results" ON ab_test_results FOR ALL TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

CREATE POLICY "Admins view events" ON ab_test_events FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

CREATE POLICY "Anyone insert events" ON ab_test_events FOR INSERT TO anon, authenticated WITH CHECK (true);

-- Trigger function
CREATE OR REPLACE FUNCTION update_ab_test_results()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO ab_test_results (test_id, variant_name)
  VALUES (NEW.test_id, NEW.variant_name)
  ON CONFLICT (test_id, variant_name) DO NOTHING;
  
  UPDATE ab_test_results SET
    total_sent = total_sent + CASE WHEN NEW.event_type = 'sent' THEN 1 ELSE 0 END,
    total_delivered = total_delivered + CASE WHEN NEW.event_type = 'delivered' THEN 1 ELSE 0 END,
    total_opened = total_opened + CASE WHEN NEW.event_type = 'opened' THEN 1 ELSE 0 END,
    total_clicked = total_clicked + CASE WHEN NEW.event_type = 'clicked' THEN 1 ELSE 0 END,
    total_converted = total_converted + CASE WHEN NEW.event_type = 'converted' THEN 1 ELSE 0 END,
    open_rate = CASE WHEN total_delivered > 0 THEN (total_opened::DECIMAL / total_delivered) * 100 ELSE 0 END,
    click_rate = CASE WHEN total_delivered > 0 THEN (total_clicked::DECIMAL / total_delivered) * 100 ELSE 0 END,
    conversion_rate = CASE WHEN total_delivered > 0 THEN (total_converted::DECIMAL / total_delivered) * 100 ELSE 0 END,
    updated_at = NOW()
  WHERE test_id = NEW.test_id AND variant_name = NEW.variant_name;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ab_test_results
  AFTER INSERT ON ab_test_events
  FOR EACH ROW EXECUTE FUNCTION update_ab_test_results();
