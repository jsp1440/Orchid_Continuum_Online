-- Migration 003: Extend Image Validation System
-- Add feedback, learning infra, and Julius AI views

ALTER TABLE image_validation_results 
  ADD COLUMN IF NOT EXISTS filename_check JSONB,
  ADD COLUMN IF NOT EXISTS orchid_verifier JSONB;

CREATE TABLE IF NOT EXISTS image_validation_feedback (
  feedback_id BIGSERIAL PRIMARY KEY,
  result_id BIGINT NOT NULL REFERENCES image_validation_results(id) ON DELETE CASCADE,
  reviewer TEXT,
  decision TEXT NOT NULL,
  correct_genus TEXT,
  correct_species TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_imgval_feedback_result_id ON image_validation_feedback(result_id);
CREATE INDEX IF NOT EXISTS idx_imgval_feedback_decision ON image_validation_feedback(decision);

CREATE TABLE IF NOT EXISTS model_weights (
  key TEXT PRIMARY KEY,
  value NUMERIC(5,4) NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO model_weights(key, value) VALUES
  ('w_vision', 0.50),
  ('w_ocr_agree', 0.15),
  ('w_multi_source', 0.35)
ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS training_events (
  event_id BIGSERIAL PRIMARY KEY,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  summary TEXT,
  params JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_training_events_occurred ON training_events(occurred_at DESC);

CREATE OR REPLACE VIEW view_imgval_summary AS
SELECT
  final_genus,
  COUNT(*) as total_predictions,
  AVG(final_confidence) as avg_confidence,
  COUNT(*) FILTER (WHERE status = 'accepted') as accepted_count,
  COUNT(*) FILTER (WHERE status = 'flagged') as flagged_count,
  COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE status = 'accepted') / NULLIF(COUNT(*), 0),
    2
  ) as acceptance_rate_pct
FROM image_validation_results
WHERE final_genus IS NOT NULL
GROUP BY final_genus
ORDER BY total_predictions DESC;

CREATE OR REPLACE VIEW view_imgval_confusion AS
SELECT
  r.final_genus as predicted_genus,
  f.correct_genus as corrected_genus,
  COUNT(*) as occurrence_count,
  AVG(r.final_confidence) as avg_prediction_confidence
FROM image_validation_results r
JOIN image_validation_feedback f ON r.id = f.result_id
WHERE r.final_genus IS NOT NULL 
  AND f.correct_genus IS NOT NULL
  AND f.decision = 'corrected'
GROUP BY r.final_genus, f.correct_genus
ORDER BY occurrence_count DESC;

CREATE OR REPLACE VIEW view_imgval_latency AS
SELECT
  r.id as result_id,
  r.orchid_id,
  r.final_genus,
  r.final_species,
  r.final_confidence,
  r.created_at as prediction_time,
  f.created_at as feedback_time,
  EXTRACT(EPOCH FROM (f.created_at - r.created_at)) as latency_seconds,
  f.decision,
  f.reviewer
FROM image_validation_results r
JOIN LATERAL (
  SELECT * FROM image_validation_feedback
  WHERE result_id = r.id
  ORDER BY created_at ASC
  LIMIT 1
) f ON true
ORDER BY f.created_at DESC;

CREATE INDEX IF NOT EXISTS idx_imgval_results_final_genus ON image_validation_results(final_genus) WHERE final_genus IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_imgval_results_created_at ON image_validation_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_imgval_results_run_id ON image_validation_results(run_id) WHERE run_id IS NOT NULL;

COMMENT ON TABLE image_validation_feedback IS 'Human corrections and feedback for validation results';
COMMENT ON TABLE model_weights IS 'Adjustable confidence scoring weights for learning system';
COMMENT ON TABLE training_events IS 'Audit log for model weight adjustments and retraining events';
