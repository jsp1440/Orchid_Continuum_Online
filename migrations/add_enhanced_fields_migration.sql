-- =====================================================================
-- ORCHID CONTINUUM DATABASE MIGRATION
-- Enhanced Fields for Research-Grade Data Collection
-- =====================================================================
-- This migration adds GBIF/EOL integration fields, specimen metadata,
-- and enhanced observation tracking to support scientific research
-- 
-- SAFE TO RE-RUN: Uses IF NOT EXISTS checks for idempotency
-- Compatible with: PostgreSQL 12+
-- =====================================================================

BEGIN;

-- =====================================================================
-- SECTION 1: ORCHID_RECORD TABLE ENHANCEMENTS
-- =====================================================================

-- Data Source & Verification Fields
-- Tracks which dataset provided the data and verification status
ALTER TABLE public.orchid_record 
  ADD COLUMN IF NOT EXISTS source_dataset TEXT,
  ADD COLUMN IF NOT EXISTS record_verification_status TEXT,
  ADD COLUMN IF NOT EXISTS identified_by TEXT,
  ADD COLUMN IF NOT EXISTS identification_date TIMESTAMP,
  ADD COLUMN IF NOT EXISTS revision_notes TEXT;

-- Observation & Collection Metadata
-- Enhanced temporal and spatial precision for research
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS observation_date TIMESTAMP;

-- Geographic Precision Fields
-- Replaces limited decimal_latitude/longitude with full precision
-- Note: Using NUMERIC for maximum precision (GBIF standard)
DO $$ 
BEGIN
  -- Only add if not exists (PostgreSQL doesn't support IF NOT EXISTS for type changes)
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'orchid_record' 
    AND column_name = 'latitude' 
    AND table_schema = 'public'
  ) THEN
    ALTER TABLE public.orchid_record ADD COLUMN latitude NUMERIC;
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'orchid_record' 
    AND column_name = 'longitude' 
    AND table_schema = 'public'
  ) THEN
    ALTER TABLE public.orchid_record ADD COLUMN longitude NUMERIC;
  END IF;
END $$;

-- Location Quality Metrics
-- Critical for assessing data reliability in research
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS coordinate_uncertainty_m NUMERIC,
  ADD COLUMN IF NOT EXISTS location_protocol TEXT;

-- Specimen/Voucher Information
-- Links to physical specimens in herbaria/museums
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS voucher_type TEXT,
  ADD COLUMN IF NOT EXISTS voucher_institution TEXT,
  ADD COLUMN IF NOT EXISTS voucher_catalog_number TEXT;

-- Asset Management Integration
-- Links to image/media assets system
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'orchid_record' 
    AND column_name = 'asset_id' 
    AND table_schema = 'public'
  ) THEN
    ALTER TABLE public.orchid_record ADD COLUMN asset_id INTEGER;
    
    -- Add foreign key constraint if assets table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'assets' AND table_schema = 'public') THEN
      ALTER TABLE public.orchid_record 
        ADD CONSTRAINT fk_orchid_record_asset 
        FOREIGN KEY (asset_id) REFERENCES public.assets(id) ON DELETE SET NULL;
    END IF;
  END IF;
END $$;

-- Plant Morphology Measurements
-- Quantitative botanical observations
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS leaf_count INTEGER,
  ADD COLUMN IF NOT EXISTS plant_height_mm NUMERIC,
  ADD COLUMN IF NOT EXISTS pseudobulb_count INTEGER,
  ADD COLUMN IF NOT EXISTS pseudobulb_size_mm NUMERIC;

-- Pollination Observations
-- Links to pollinator relationship tracking
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS pollination_observed BOOLEAN,
  ADD COLUMN IF NOT EXISTS pollinator_observed_id INTEGER;

-- Cultivation & Context Metadata
-- Distinguishes wild vs. cultivated specimens
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS record_context TEXT,
  ADD COLUMN IF NOT EXISTS cultivar_name TEXT,
  ADD COLUMN IF NOT EXISTS growing_medium TEXT,
  ADD COLUMN IF NOT EXISTS container_type TEXT,
  ADD COLUMN IF NOT EXISTS exposure TEXT;

-- Data Licensing & Privacy
-- Essential for legal compliance and data sharing
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS data_license TEXT,
  ADD COLUMN IF NOT EXISTS sensitive_flag BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS public_display_location TEXT;

-- Phenology Tracking
-- Precise bloom timing for climate research
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS bloom_start_month SMALLINT,
  ADD COLUMN IF NOT EXISTS bloom_end_month SMALLINT,
  ADD COLUMN IF NOT EXISTS bloom_intensity NUMERIC;

-- =====================================================================
-- SECTION 2: ORCHID_TAXONOMY TABLE ENHANCEMENTS
-- =====================================================================

-- Taxonomic Authority & Rank
-- Complete GBIF/EOL integration fields
ALTER TABLE public.orchid_taxonomy
  ADD COLUMN IF NOT EXISTS authority TEXT,
  ADD COLUMN IF NOT EXISTS taxon_rank TEXT;

-- External Database IDs
-- Stores GBIF key, EOL page ID, and other external identifiers
ALTER TABLE public.orchid_taxonomy
  ADD COLUMN IF NOT EXISTS external_ids JSONB;

-- =====================================================================
-- SECTION 3: ASSETS TABLE ENHANCEMENTS
-- =====================================================================

-- Media Metadata & Attribution
-- Critical for image licensing and copyright compliance
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'assets' AND table_schema = 'public') THEN
    ALTER TABLE public.assets
      ADD COLUMN IF NOT EXISTS capture_date TIMESTAMP,
      ADD COLUMN IF NOT EXISTS copyright_holder TEXT,
      ADD COLUMN IF NOT EXISTS license TEXT;
  END IF;
END $$;

-- =====================================================================
-- SECTION 4: POLLINATOR RELATIONSHIPS TABLE ENHANCEMENTS
-- =====================================================================

-- Enhanced Pollinator Taxonomy & Evidence
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_name = 'advanced_orchid_pollinator_relationships' 
    AND table_schema = 'public'
  ) THEN
    ALTER TABLE public.advanced_orchid_pollinator_relationships
      ADD COLUMN IF NOT EXISTS pollinator_taxon_rank TEXT,
      ADD COLUMN IF NOT EXISTS interaction_evidence TEXT,
      ADD COLUMN IF NOT EXISTS observer_id INTEGER,
      ADD COLUMN IF NOT EXISTS location_id INTEGER;
  END IF;
END $$;

-- =====================================================================
-- SECTION 5: PERFORMANCE INDEXES
-- =====================================================================

-- Index on observation_date for temporal queries
CREATE INDEX IF NOT EXISTS idx_orchid_record_observation_date 
  ON public.orchid_record(observation_date);

-- Spatial index on latitude/longitude for geographic queries
CREATE INDEX IF NOT EXISTS idx_orchid_record_lat_lon 
  ON public.orchid_record(latitude, longitude) 
  WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Index on bloom timing for phenology research
CREATE INDEX IF NOT EXISTS idx_orchid_record_bloom_months 
  ON public.orchid_record(bloom_start_month, bloom_end_month);

-- Taxonomy rank index for hierarchical queries
CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_rank 
  ON public.orchid_taxonomy(taxon_rank);

-- External IDs index for API lookups (GIN index for JSONB)
CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_external_ids 
  ON public.orchid_taxonomy USING GIN(external_ids);

-- Source dataset index for filtering by data provider
CREATE INDEX IF NOT EXISTS idx_orchid_record_source_dataset 
  ON public.orchid_record(source_dataset);

-- Verification status index for quality control queries
CREATE INDEX IF NOT EXISTS idx_orchid_record_verification 
  ON public.orchid_record(record_verification_status);

-- =====================================================================
-- SECTION 6: DATA INTEGRITY CONSTRAINTS
-- =====================================================================

-- Ensure bloom months are valid (1-12)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.check_constraints 
    WHERE constraint_name = 'check_bloom_start_month'
  ) THEN
    ALTER TABLE public.orchid_record 
      ADD CONSTRAINT check_bloom_start_month 
      CHECK (bloom_start_month >= 1 AND bloom_start_month <= 12);
  END IF;
  
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.check_constraints 
    WHERE constraint_name = 'check_bloom_end_month'
  ) THEN
    ALTER TABLE public.orchid_record 
      ADD CONSTRAINT check_bloom_end_month 
      CHECK (bloom_end_month >= 1 AND bloom_end_month <= 12);
  END IF;
END $$;

-- Ensure coordinate uncertainty is non-negative
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.check_constraints 
    WHERE constraint_name = 'check_coordinate_uncertainty'
  ) THEN
    ALTER TABLE public.orchid_record 
      ADD CONSTRAINT check_coordinate_uncertainty 
      CHECK (coordinate_uncertainty_m >= 0);
  END IF;
END $$;

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================

COMMIT;

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================
-- Run these to verify successful migration:
-- 
-- Check new orchid_record columns:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'orchid_record' 
-- ORDER BY ordinal_position;
--
-- Check new indexes:
-- SELECT indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'orchid_record';
--
-- Check constraints:
-- SELECT constraint_name, constraint_type 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'orchid_record';
-- =====================================================================
