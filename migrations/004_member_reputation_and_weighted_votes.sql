-- 004: Member identity + weighted voting

-- Optional lightweight members table if you don't already have one
CREATE TABLE IF NOT EXISTS members (
  member_id BIGSERIAL PRIMARY KEY,
  display_name TEXT NOT NULL,
  email TEXT UNIQUE
);

-- Reputation/weight per member (default 1.0)
CREATE TABLE IF NOT EXISTS member_reputation (
  member_id BIGINT PRIMARY KEY REFERENCES members(member_id) ON DELETE CASCADE,
  expertise_score NUMERIC(4,2) NOT NULL DEFAULT 1.00,
  points INT NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Link feedback to a member_id (keep reviewer TEXT for legacy)
ALTER TABLE image_validation_feedback
  ADD COLUMN IF NOT EXISTS member_id BIGINT REFERENCES members(member_id) ON DELETE SET NULL;

-- Uniqueness: one vote per member per result (nulls ignored)
CREATE UNIQUE INDEX IF NOT EXISTS ux_imgval_vote_unique
  ON image_validation_feedback(result_id, member_id)
  WHERE member_id IS NOT NULL;

-- Weighted consensus view (agrees/disagrees/corrected by expertise_score)
CREATE OR REPLACE VIEW view_imgval_weighted_consensus AS
SELECT
  r.id AS result_id,
  COALESCE(SUM(CASE WHEN f.decision='agree' THEN COALESCE(m.expertise_score,1.0) ELSE 0 END),0) AS w_agree,
  COALESCE(SUM(CASE WHEN f.decision='disagree' THEN COALESCE(m.expertise_score,1.0) ELSE 0 END),0) AS w_disagree,
  COALESCE(SUM(CASE WHEN f.decision='corrected' THEN COALESCE(m.expertise_score,1.0) ELSE 0 END),0) AS w_corrected,
  COUNT(*) AS votes_total
FROM image_validation_results r
LEFT JOIN image_validation_feedback f ON f.result_id = r.id
LEFT JOIN member_reputation m ON m.member_id = f.member_id
GROUP BY r.id;

-- Leaderboard view (simple points rule)
CREATE OR REPLACE VIEW view_member_leaderboard AS
SELECT
  COALESCE(mem.member_id, 0) AS member_id,
  COALESCE(mem.display_name, 'Anonymous') AS display_name,
  SUM(CASE WHEN f.decision='agree' THEN 2
           WHEN f.decision='corrected' THEN 3
           WHEN f.decision='disagree' THEN 1
           ELSE 0 END) AS score,
  COUNT(*) AS votes
FROM image_validation_feedback f
LEFT JOIN members mem ON mem.member_id = f.member_id
GROUP BY mem.member_id, mem.display_name
ORDER BY score DESC, votes DESC;
