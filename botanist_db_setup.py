"""
Database setup for Digital Botanist Vision AI
Ensures botanist_vision_results table exists before queries
"""

import os
import logging
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

def ensure_botanist_table_exists():
    """
    Ensure botanist_vision_results table exists
    Safe to call multiple times - only creates if missing
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not set")
        return False
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'botanist_vision_results'
                )
            """))
            
            exists = result.scalar()
            
            if not exists:
                logger.info("Creating botanist_vision_results table...")
                
                conn.execute(text("""
                    CREATE TABLE botanist_vision_results (
                        id SERIAL PRIMARY KEY,
                        orchid_image_id INTEGER REFERENCES orchid_images(id),
                        image_url TEXT NOT NULL,
                        
                        blind_identification BOOLEAN DEFAULT true,
                        ai_genus VARCHAR(255),
                        ai_species VARCHAR(255),
                        ai_confidence FLOAT,
                        identification_method TEXT,
                        
                        correct_genus BOOLEAN,
                        correct_species BOOLEAN,
                        database_genus VARCHAR(255),
                        database_species VARCHAR(255),
                        identification_accuracy VARCHAR(50),
                        
                        sepal_count INTEGER,
                        sepal_color TEXT,
                        sepal_shape TEXT,
                        petal_count INTEGER,
                        petal_color TEXT,
                        petal_shape TEXT,
                        labellum_shape TEXT,
                        labellum_color TEXT,
                        labellum_markings TEXT,
                        column_visible BOOLEAN,
                        column_position TEXT,
                        spur_present BOOLEAN,
                        spur_length TEXT,
                        inflorescence_type VARCHAR(100),
                        flower_count INTEGER,
                        flower_size VARCHAR(50),
                        flower_orientation VARCHAR(50),
                        
                        growth_habit VARCHAR(100),
                        leaf_arrangement VARCHAR(100),
                        leaf_shape TEXT,
                        leaf_texture TEXT,
                        pseudobulb_present BOOLEAN,
                        roots_visible BOOLEAN,
                        root_type VARCHAR(100),
                        
                        distinctive_features TEXT[],
                        diagnostic_characters TEXT[],
                        botanical_terms_used TEXT[],
                        
                        dichotomous_key_used TEXT,
                        key_characters_observed TEXT[],
                        identification_reasoning TEXT,
                        
                        botanical_description TEXT,
                        
                        model_used VARCHAR(100),
                        tokens_used INTEGER,
                        analysis_cost FLOAT,
                        processing_time_seconds FLOAT,
                        
                        image_quality VARCHAR(50),
                        specimen_completeness VARCHAR(50),
                        characters_visible TEXT[],
                        characters_obscured TEXT[],
                        
                        raw_response JSONB,
                        
                        -- Botanical Drawing Generation (Educational Documentation)
                        botanical_drawing_url TEXT,       -- AI-generated scientific line drawing (B&W, unlabeled)
                        labeled_drawing_url TEXT,         -- Drawing with anatomical labels and arrows
                        artistic_illustration_url TEXT,   -- Watercolor botanical art (colored, beautiful)
                        coloring_page_url TEXT,           -- Thick outline coloring page (for kids/artists)
                        drawing_labels JSONB,             -- {"sepal": [x, y], "petal": [x, y], ...}
                        drawing_metadata JSONB,           -- Generation parameters and model info
                        
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """))
                
                # Create indexes
                conn.execute(text("""
                    CREATE INDEX idx_botanist_results_image_id 
                    ON botanist_vision_results(orchid_image_id)
                """))
                conn.execute(text("""
                    CREATE INDEX idx_botanist_results_genus 
                    ON botanist_vision_results(ai_genus)
                """))
                conn.execute(text("""
                    CREATE INDEX idx_botanist_results_accuracy 
                    ON botanist_vision_results(identification_accuracy)
                """))
                
                conn.commit()
                logger.info("✅ botanist_vision_results table created successfully")
                return True
            else:
                logger.debug("botanist_vision_results table already exists")
                return True
                
    except Exception as e:
        logger.error(f"Error ensuring table exists: {e}")
        return False


def get_botanist_stats():
    """
    Get botanist analysis statistics without initializing heavy objects
    Lightweight function for dashboard status checks
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return None
    
    # Ensure table exists first
    if not ensure_botanist_table_exists():
        return None
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            # Get analysis stats
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_analyzed,
                    COUNT(CASE WHEN identification_accuracy = 'perfect' THEN 1 END) as perfect_ids,
                    COUNT(CASE WHEN identification_accuracy = 'genus_only' THEN 1 END) as genus_only,
                    COUNT(CASE WHEN identification_accuracy = 'incorrect' THEN 1 END) as incorrect,
                    AVG(ai_confidence) as avg_confidence,
                    SUM(analysis_cost) as total_cost,
                    AVG(processing_time_seconds) as avg_time
                FROM botanist_vision_results
            """))
            stats = result.fetchone()
            
            # Get remaining count
            remaining_result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM orchid_images oi
                LEFT JOIN botanist_vision_results bvr ON oi.id = bvr.orchid_image_id
                WHERE oi.image_url IS NOT NULL
                AND oi.gbif_occurrence_key IS NOT NULL
                AND bvr.id IS NULL
            """))
            remaining = remaining_result.scalar()
            
            total_analyzed = stats[0] or 0
            perfect_ids = stats[1] or 0
            genus_only = stats[2] or 0
            incorrect = stats[3] or 0
            
            accuracy_rate = (perfect_ids / total_analyzed * 100) if total_analyzed > 0 else 0
            genus_accuracy = ((perfect_ids + genus_only) / total_analyzed * 100) if total_analyzed > 0 else 0
            
            return {
                'total_analyzed': total_analyzed,
                'remaining': remaining,
                'perfect_identifications': perfect_ids,
                'genus_only': genus_only,
                'incorrect': incorrect,
                'accuracy_rate': round(accuracy_rate, 1),
                'genus_accuracy_rate': round(genus_accuracy, 1),
                'avg_confidence': round(stats[4] or 0.0, 2),
                'total_cost': round(stats[5] or 0.0, 2),
                'avg_processing_time': round(stats[6] or 0.0, 2)
            }
            
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return None
