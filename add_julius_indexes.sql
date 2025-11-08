-- JULIUS OPTIMIZATION: Add indexes for faster lookups
-- These improve query performance and reduce lock contention

-- Index for checking duplicates (ON CONFLICT uses this)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orchid_images_url 
ON orchid_images(image_url);

-- Index for taxonomy lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orchid_images_taxonomy 
ON orchid_images(taxonomy_id);

-- Index for job queue queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_harvest_jobs_status_priority 
ON harvest_jobs(status, priority DESC);

-- Index for source analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orchid_images_source 
ON orchid_images(image_source);

