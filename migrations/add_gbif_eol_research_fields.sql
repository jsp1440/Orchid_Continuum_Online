-- =====================================================================
-- ORCHID CONTINUUM - GBIF/EOL RESEARCH INTEGRATION MIGRATION
-- Comprehensive Scientific Research Database Enhancement
-- =====================================================================
-- Implements architect-recommended CRITICAL and HIGH priority fields
-- for complete GBIF and EOL data integration with conservation genetics
-- 
-- SAFE TO RE-RUN: Uses IF NOT EXISTS checks for idempotency
-- Compatible with: PostgreSQL 12+
-- =====================================================================

BEGIN;

-- =====================================================================
-- SECTION 1: ORCHID_TAXONOMY - COMPLETE TAXONOMIC HIERARCHY
-- =====================================================================
-- CRITICAL: Full taxonomic classification from kingdom to subspecies

ALTER TABLE public.orchid_taxonomy
  ADD COLUMN IF NOT EXISTS kingdom VARCHAR(120),
  ADD COLUMN IF NOT EXISTS phylum VARCHAR(120),
  ADD COLUMN IF NOT EXISTS class VARCHAR(120),
  ADD COLUMN IF NOT EXISTS "order" VARCHAR(120),  -- 'order' is SQL keyword, needs quotes
  ADD COLUMN IF NOT EXISTS family VARCHAR(120),
  ADD COLUMN IF NOT EXISTS subspecies VARCHAR(120),
  ADD COLUMN IF NOT EXISTS variety VARCHAR(120),
  ADD COLUMN IF NOT EXISTS taxonomic_status VARCHAR(50),  -- ACCEPTED, SYNONYM, DOUBTFUL
  ADD COLUMN IF NOT EXISTS gbif_taxon_key BIGINT,         -- GBIF unique species identifier
  ADD COLUMN IF NOT EXISTS eol_page_id VARCHAR(32),       -- Encyclopedia of Life page ID
  ADD COLUMN IF NOT EXISTS gbif_occurrence_count INTEGER DEFAULT 0;  -- Number of wild observations

-- =====================================================================
-- SECTION 2: ORCHID_TAXONOMY - MULTILINGUAL & STRUCTURED DATA
-- =====================================================================
-- HIGH PRIORITY: JSONB fields for complex data structures

-- Vernacular names in multiple languages
-- Example: [{"name": "Flor de Mayo", "language": "es", "source": "GBIF"}, ...]
ALTER TABLE public.orchid_taxonomy
  ADD COLUMN IF NOT EXISTS vernacular_names JSONB DEFAULT '[]'::jsonb;

-- Scientific synonyms array (upgrade from TEXT to JSONB)
-- Example: ["Cattleya trianaei", "Laelia trianae"]
ALTER TABLE public.orchid_taxonomy
  ADD COLUMN IF NOT EXISTS synonyms_json JSONB DEFAULT '[]'::jsonb;

-- Data synchronization tracking
ALTER TABLE public.orchid_taxonomy
  ADD COLUMN IF NOT EXISTS gbif_last_synced_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS eol_last_synced_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS last_taxonomic_update TIMESTAMP DEFAULT NOW();

-- =====================================================================
-- SECTION 3: ORCHID_RECORD - GBIF OCCURRENCE METADATA
-- =====================================================================
-- CRITICAL: Complete GBIF occurrence data capture

-- Geographic precision and elevation
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS elevation_m NUMERIC;  -- Altitude in meters

-- GBIF collection/specimen metadata
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS institution_code VARCHAR(100),      -- Museum/herbarium code
  ADD COLUMN IF NOT EXISTS collection_code VARCHAR(100),       -- Collection within institution
  ADD COLUMN IF NOT EXISTS catalog_number VARCHAR(150),        -- Specimen catalog number
  ADD COLUMN IF NOT EXISTS recorded_by VARCHAR(200),           -- Collector name
  ADD COLUMN IF NOT EXISTS record_number VARCHAR(120),         -- Field collection number
  ADD COLUMN IF NOT EXISTS basis_of_record VARCHAR(40);        -- PRESERVED_SPECIMEN, OBSERVATION, etc.

-- GBIF data provenance
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS gbif_dataset_key VARCHAR(64),       -- Which GBIF dataset
  ADD COLUMN IF NOT EXISTS gbif_publishing_org_key VARCHAR(64), -- Who published the data
  ADD COLUMN IF NOT EXISTS gbif_occurrence_key BIGINT;          -- GBIF occurrence unique ID

-- Data synchronization tracking
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS gbif_last_synced_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS eol_last_synced_at TIMESTAMP,
  ADD COLUMN IF NOT EXISTS ai_last_synced_at TIMESTAMP;

-- =====================================================================
-- SECTION 4: ORCHID_RECORD - EOL TRAITBANK CONSERVATION GENETICS
-- =====================================================================
-- HIGH PRIORITY: Conservation genetics and phenotypic variation data

-- EOL TraitBank - Population Genetics
-- Example: {"genetic_diversity": "high", "effective_population_size": 500, "gene_flow": "moderate"}
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS eol_population_genetics JSONB DEFAULT '{}'::jsonb;

-- EOL TraitBank - Morphological Variation
-- Example: {"flower_size_variation": "high", "color_polymorphism": true, "plant_height_variation": "20-40cm"}
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS eol_morphological_variation JSONB DEFAULT '{}'::jsonb;

-- EOL TraitBank - Environmental Adaptation
-- Example: {"elevation_tolerance": "500-2000m", "soil_pH": "5.5-6.5", "drought_resistance": "moderate"}
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS eol_environmental_adaptation JSONB DEFAULT '{}'::jsonb;

-- EOL TraitBank - Conservation Status
-- Example: {"population_trend": "declining", "threats": ["habitat_loss"], "protection_status": "CITES_Appendix_II"}
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS eol_conservation_status JSONB DEFAULT '{}'::jsonb;

-- =====================================================================
-- SECTION 5: ORCHID_RECORD - RICH DESCRIPTIVE DATA
-- =====================================================================
-- HIGH PRIORITY: Multilingual descriptions and citations

-- EOL text descriptions with full attribution
-- Example: [{"description": "...", "subject": "morphology", "language": "en", "source": "Flora of...", "license": "CC-BY"}]
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS eol_descriptions JSONB DEFAULT '[]'::jsonb;

-- GBIF distribution data
-- Example: {"countries": ["Colombia", "Ecuador"], "habitats": ["cloud_forest"], "occurrence_heatmap": {...}}
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS gbif_distribution JSONB DEFAULT '{}'::jsonb;

-- ISO country/region codes for filtering
-- Example: ["CO", "EC", "PE"]
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS region_codes JSONB DEFAULT '[]'::jsonb;

-- Media provenance with full attribution
-- Example: [{"url": "...", "creator": "John Doe", "license": "CC-BY-4.0", "rightsHolder": "...", "source": "GBIF"}]
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS media_provenance JSONB DEFAULT '[]'::jsonb;

-- =====================================================================
-- SECTION 6: ORCHID_RECORD - DATA QUALITY & ANALYTICS
-- =====================================================================
-- MEDIUM PRIORITY: Quality assessment and analytics support

-- Trait confidence scoring
-- Example: {"flower_color": 0.95, "habitat": 0.8, "elevation": 0.9}
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS trait_confidence JSONB DEFAULT '{}'::jsonb;

-- Data origin tracking (field -> source mapping)
-- Example: {"genus": {"source": "GBIF", "last_updated": "2024-01-15"}, "habitat": {"source": "EOL", "last_updated": "2024-01-16"}}
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS data_origin JSONB DEFAULT '{}'::jsonb;

-- Conservation priority score (calculated)
ALTER TABLE public.orchid_record
  ADD COLUMN IF NOT EXISTS conservation_priority_score NUMERIC;

-- Geospatial quality indicator
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'geospatial_quality_enum') THEN
    CREATE TYPE geospatial_quality_enum AS ENUM ('verified', 'estimated', 'low_confidence', 'unknown');
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'orchid_record' 
    AND column_name = 'geospatial_quality'
  ) THEN
    ALTER TABLE public.orchid_record 
      ADD COLUMN geospatial_quality geospatial_quality_enum DEFAULT 'unknown';
  END IF;
END $$;

-- =====================================================================
-- SECTION 7: PERFORMANCE INDEXES
-- =====================================================================

-- Taxonomic hierarchy indexes for fast filtering
CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_kingdom 
  ON public.orchid_taxonomy(kingdom);

CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_order 
  ON public.orchid_taxonomy("order");

CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_family 
  ON public.orchid_taxonomy(family);

-- GBIF taxon key for API lookups
CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_gbif_key 
  ON public.orchid_taxonomy(gbif_taxon_key) 
  WHERE gbif_taxon_key IS NOT NULL;

-- EOL page ID for API lookups
CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_eol_page 
  ON public.orchid_taxonomy(eol_page_id) 
  WHERE eol_page_id IS NOT NULL;

-- Taxonomic status for filtering accepted vs synonyms
CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_status 
  ON public.orchid_taxonomy(taxonomic_status);

-- Elevation index for ecological queries
CREATE INDEX IF NOT EXISTS idx_orchid_record_elevation 
  ON public.orchid_record(elevation_m) 
  WHERE elevation_m IS NOT NULL;

-- GBIF occurrence key for deduplication
CREATE INDEX IF NOT EXISTS idx_orchid_record_gbif_occurrence 
  ON public.orchid_record(gbif_occurrence_key) 
  WHERE gbif_occurrence_key IS NOT NULL;

-- Institution code for specimen tracking
CREATE INDEX IF NOT EXISTS idx_orchid_record_institution 
  ON public.orchid_record(institution_code);

-- Basis of record for filtering observation types
CREATE INDEX IF NOT EXISTS idx_orchid_record_basis 
  ON public.orchid_record(basis_of_record);

-- Conservation priority for research prioritization
CREATE INDEX IF NOT EXISTS idx_orchid_record_conservation_priority 
  ON public.orchid_record(conservation_priority_score DESC) 
  WHERE conservation_priority_score IS NOT NULL;

-- GIN indexes for JSONB fields (fast containment queries)
CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_vernacular_gin 
  ON public.orchid_taxonomy USING GIN(vernacular_names);

CREATE INDEX IF NOT EXISTS idx_orchid_taxonomy_synonyms_gin 
  ON public.orchid_taxonomy USING GIN(synonyms_json);

CREATE INDEX IF NOT EXISTS idx_orchid_record_eol_genetics_gin 
  ON public.orchid_record USING GIN(eol_population_genetics);

CREATE INDEX IF NOT EXISTS idx_orchid_record_distribution_gin 
  ON public.orchid_record USING GIN(gbif_distribution);

CREATE INDEX IF NOT EXISTS idx_orchid_record_data_origin_gin 
  ON public.orchid_record USING GIN(data_origin);

-- =====================================================================
-- SECTION 8: DATA INTEGRITY CONSTRAINTS
-- =====================================================================

-- Ensure elevation is realistic (Mount Everest is 8,849m)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.check_constraints 
    WHERE constraint_name = 'check_elevation_realistic'
  ) THEN
    ALTER TABLE public.orchid_record 
      ADD CONSTRAINT check_elevation_realistic 
      CHECK (elevation_m >= -500 AND elevation_m <= 9000);
  END IF;
END $$;

-- Ensure conservation priority score is 0-100
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.check_constraints 
    WHERE constraint_name = 'check_conservation_score'
  ) THEN
    ALTER TABLE public.orchid_record 
      ADD CONSTRAINT check_conservation_score 
      CHECK (conservation_priority_score >= 0 AND conservation_priority_score <= 100);
  END IF;
END $$;

-- Ensure GBIF occurrence count is non-negative
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.check_constraints 
    WHERE constraint_name = 'check_occurrence_count'
  ) THEN
    ALTER TABLE public.orchid_taxonomy 
      ADD CONSTRAINT check_occurrence_count 
      CHECK (gbif_occurrence_count >= 0);
  END IF;
END $$;

-- =====================================================================
-- SECTION 9: HELPER VIEWS FOR RESEARCH QUERIES
-- =====================================================================

-- View: Complete taxonomy with all hierarchy levels
CREATE OR REPLACE VIEW v_orchid_complete_taxonomy AS
SELECT 
  id,
  scientific_name,
  kingdom,
  phylum,
  class,
  "order",
  family,
  genus,
  species,
  subspecies,
  variety,
  authority,
  taxon_rank,
  taxonomic_status,
  gbif_taxon_key,
  eol_page_id,
  gbif_occurrence_count,
  vernacular_names,
  synonyms_json,
  external_ids,
  gbif_last_synced_at,
  eol_last_synced_at
FROM public.orchid_taxonomy;

-- View: Research-ready orchid records with full metadata
CREATE OR REPLACE VIEW v_orchid_research_records AS
SELECT 
  r.id,
  r.display_name,
  r.scientific_name,
  r.genus,
  r.species,
  r.latitude,
  r.longitude,
  r.elevation_m,
  r.coordinate_uncertainty_m,
  r.geospatial_quality,
  r.country,
  r.region_codes,
  r.observation_date,
  r.basis_of_record,
  r.institution_code,
  r.catalog_number,
  r.gbif_occurrence_key,
  r.source_dataset,
  r.record_verification_status,
  r.conservation_priority_score,
  r.eol_conservation_status,
  r.data_origin,
  t.taxonomic_status,
  t.gbif_taxon_key,
  t.eol_page_id
FROM public.orchid_record r
LEFT JOIN public.orchid_taxonomy t ON r.taxonomy_id = t.id;

-- View: Conservation priority orchids
CREATE OR REPLACE VIEW v_orchid_conservation_priority AS
SELECT 
  r.id,
  r.display_name,
  r.scientific_name,
  r.conservation_priority_score,
  r.eol_conservation_status,
  r.country,
  r.latitude,
  r.longitude,
  r.gbif_occurrence_key,
  t.gbif_occurrence_count,
  t.taxonomic_status
FROM public.orchid_record r
LEFT JOIN public.orchid_taxonomy t ON r.taxonomy_id = t.id
WHERE r.conservation_priority_score IS NOT NULL
ORDER BY r.conservation_priority_score DESC;

-- =====================================================================
-- MIGRATION COMPLETE
-- =====================================================================

COMMIT;

-- =====================================================================
-- VERIFICATION QUERIES
-- =====================================================================
-- Run these to verify successful migration:
-- 
-- Check new taxonomy columns:
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'orchid_taxonomy' AND column_name IN 
-- ('kingdom', 'gbif_taxon_key', 'vernacular_names', 'eol_page_id')
-- ORDER BY column_name;
--
-- Check new orchid_record columns:
-- SELECT column_name, data_type FROM information_schema.columns 
-- WHERE table_name = 'orchid_record' AND column_name IN 
-- ('elevation_m', 'eol_population_genetics', 'gbif_distribution', 'conservation_priority_score')
-- ORDER BY column_name;
--
-- Check new indexes:
-- SELECT indexname FROM pg_indexes 
-- WHERE tablename IN ('orchid_record', 'orchid_taxonomy') 
-- AND indexname LIKE 'idx_%' 
-- ORDER BY indexname;
--
-- Check research views:
-- SELECT * FROM v_orchid_complete_taxonomy LIMIT 5;
-- SELECT * FROM v_orchid_research_records LIMIT 5;
-- SELECT * FROM v_orchid_conservation_priority LIMIT 10;
-- =====================================================================
