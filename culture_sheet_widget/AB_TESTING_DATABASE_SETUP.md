# A/B Testing Database Setup

## Overview
This document contains the complete database schema for the A/B testing system. Run these SQL commands in your Supabase SQL editor.

## Tables

### 1. ab_tests
Stores A/B test metadata and configuration.

```sql
CREATE TABLE IF NOT EXISTS ab_tests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'draft', -- draft, running, completed, stopped
  template_a_id TEXT NOT NULL,
  template_b_id TEXT NOT NULL,
  traffic_split INTEGER NOT NULL DEFAULT 50, -- percentage for variant A
  success_metric TEXT NOT NULL, -- open_rate, click_rate, conversion_rate
  target_sample_size INTEGER DEFAULT 1000,
  confidence_level DECIMAL DEFAULT 95.0,
  start_date TIMESTAMPTZ,
  end_date TIMESTAMPTZ,
  duration_days INTEGER,
  winner_variant TEXT, -- 'A', 'B', or NULL
  promoted_at TIMESTAMPTZ,
  created_by UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. ab_test_variants
Links templates to test variants.

```sql
CREATE TABLE IF NOT EXISTS ab_test_variants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
  variant_name TEXT NOT NULL, -- 'A' or 'B'
  template_id TEXT NOT NULL,
  template_name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3. ab_test_results
Aggregated performance metrics per variant.

```sql
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
```

### 4. ab_test_events
Individual user interaction events.

```sql
CREATE TABLE IF NOT EXISTS ab_test_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
  variant_name TEXT NOT NULL,
  user_id UUID,
  email TEXT,
  event_type TEXT NOT NULL, -- sent, delivered, opened, clicked, converted, bounced
  event_metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Indexes

```sql
CREATE INDEX idx_ab_tests_status ON ab_tests(status);
CREATE INDEX idx_ab_tests_created_at ON ab_tests(created_at DESC);
CREATE INDEX idx_ab_test_variants_test_id ON ab_test_variants(test_id);
CREATE INDEX idx_ab_test_results_test_id ON ab_test_results(test_id);
CREATE INDEX idx_ab_test_events_test_id ON ab_test_events(test_id);
CREATE INDEX idx_ab_test_events_variant ON ab_test_events(test_id, variant_name);
CREATE INDEX idx_ab_test_events_type ON ab_test_events(event_type);
CREATE INDEX idx_ab_test_events_created_at ON ab_test_events(created_at DESC);
```

## Row Level Security (RLS)

Enable RLS on all tables:

```sql
ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_events ENABLE ROW LEVEL SECURITY;
```

### Admin-only policies for ab_tests

```sql
CREATE POLICY "Admins can view all A/B tests"
  ON ab_tests FOR SELECT TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM auth.users
      WHERE auth.users.id = auth.uid()
      AND auth.users.raw_user_meta_data->>'role' = 'admin'
    )
  );

CREATE POLICY "Admins can create A/B tests"
  ON ab_tests FOR INSERT TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM auth.users
      WHERE auth.users.id = auth.uid()
      AND auth.users.raw_user_meta_data->>'role' = 'admin'
    )
  );

CREATE POLICY "Admins can update A/B tests"
  ON ab_tests FOR UPDATE TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM auth.users
      WHERE auth.users.id = auth.uid()
      AND auth.users.raw_user_meta_data->>'role' = 'admin'
    )
  );

CREATE POLICY "Admins can delete A/B tests"
  ON ab_tests FOR DELETE TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM auth.users
      WHERE auth.users.id = auth.uid()
      AND auth.users.raw_user_meta_data->>'role' = 'admin'
    )
  );
```

### Policies for other tables

```sql
-- ab_test_variants
CREATE POLICY "Admins can view variants" ON ab_test_variants FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

CREATE POLICY "Admins can create variants" ON ab_test_variants FOR INSERT TO authenticated
  WITH CHECK (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

-- ab_test_results
CREATE POLICY "Admins can view results" ON ab_test_results FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

CREATE POLICY "Admins can modify results" ON ab_test_results FOR ALL TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

-- ab_test_events
CREATE POLICY "Admins can view events" ON ab_test_events FOR SELECT TO authenticated
  USING (EXISTS (SELECT 1 FROM auth.users WHERE auth.users.id = auth.uid() AND auth.users.raw_user_meta_data->>'role' = 'admin'));

CREATE POLICY "Anyone can insert events" ON ab_test_events FOR INSERT TO anon, authenticated WITH CHECK (true);
```

## Trigger Function

Automatically update aggregated results when events are inserted:

```sql
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
```
