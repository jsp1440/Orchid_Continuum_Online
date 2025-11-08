"""
Vision AI Image Analyzer System
Analyzes 10,534 GBIF orchid specimen images using OpenAI GPT-4 Vision
Works directly with image URLs - no download needed!
"""

import os
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from openai import OpenAI
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionAIAnalyzer:
    """Analyzes orchid images using OpenAI GPT-4 Vision"""
    
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        self.engine = create_engine(self.database_url)
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        
        self.stats = {
            'total_processed': 0,
            'successful_analysis': 0,
            'failed_analysis': 0,
            'api_errors': 0,
            'start_time': None,
            'estimated_cost': 0.0
        }
    
    def setup_results_table(self):
        """Create table to store vision AI analysis results"""
        logger.info("📊 Setting up vision_ai_results table...")
        
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vision_ai_results (
                    id SERIAL PRIMARY KEY,
                    orchid_image_id INTEGER REFERENCES orchid_images(id),
                    image_url TEXT NOT NULL,
                    
                    -- AI Analysis Results
                    identified_genus VARCHAR(255),
                    identified_species VARCHAR(255),
                    confidence_score FLOAT,
                    ai_description TEXT,
                    
                    -- Detailed Features
                    flower_color TEXT,
                    flower_structure TEXT,
                    leaf_characteristics TEXT,
                    growth_habit TEXT,
                    distinctive_features TEXT[],
                    
                    -- Comparison with Database
                    matches_database_taxonomy BOOLEAN,
                    database_genus VARCHAR(255),
                    database_species VARCHAR(255),
                    taxonomy_confidence VARCHAR(50),
                    
                    -- Metadata
                    model_used VARCHAR(100),
                    prompt_used TEXT,
                    tokens_used INTEGER,
                    analysis_cost FLOAT,
                    processing_time_seconds FLOAT,
                    
                    -- Quality Indicators
                    image_quality VARCHAR(50),
                    specimen_completeness VARCHAR(50),
                    identification_difficulty VARCHAR(50),
                    
                    -- Full AI Response
                    raw_response JSONB,
                    
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            
            # Create indexes for faster queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_vision_results_image_id 
                ON vision_ai_results(orchid_image_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_vision_results_genus 
                ON vision_ai_results(identified_genus)
            """))
            
            conn.commit()
            logger.info("✅ vision_ai_results table ready")
    
    def analyze_image_with_vision(self, image_url: str, database_taxonomy: Dict = None) -> Optional[Dict]:
        """
        Analyze a single orchid image using GPT-4 Vision
        
        Args:
            image_url: URL of the image to analyze
            database_taxonomy: Known taxonomy from database (for comparison)
        
        Returns:
            Dictionary with analysis results or None if failed
        """
        try:
            start_time = time.time()
            
            # Build prompt for orchid identification
            prompt = self._build_identification_prompt(database_taxonomy)
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Latest vision model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "low"  # Low detail = cheaper, still accurate for orchid ID
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3  # Lower temperature for more factual responses
            )
            
            # Extract response
            ai_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Estimate cost (GPT-4o Vision pricing: ~$0.002 per image with low detail)
            # Input: $0.0025/1K tokens, Output: $0.01/1K tokens (avg ~500 tokens total)
            cost = tokens_used * 0.000005  # More accurate for low detail
            
            processing_time = time.time() - start_time
            
            # Parse AI response
            analysis = self._parse_ai_response(ai_text, database_taxonomy)
            
            # Add metadata
            analysis['tokens_used'] = tokens_used
            analysis['analysis_cost'] = cost
            analysis['processing_time_seconds'] = processing_time
            analysis['model_used'] = 'gpt-4o'
            analysis['prompt_used'] = prompt
            analysis['raw_response'] = {
                'text': ai_text,
                'finish_reason': response.choices[0].finish_reason
            }
            
            logger.info(f"✅ Analyzed image: {analysis.get('identified_genus')} {analysis.get('identified_species')} (confidence: {analysis.get('confidence_score', 0):.2f})")
            
            self.stats['estimated_cost'] += cost
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Vision AI error for {image_url}: {e}")
            self.stats['api_errors'] += 1
            return None
    
    def _build_identification_prompt(self, database_taxonomy: Dict = None) -> str:
        """Build detailed prompt for orchid identification"""
        
        base_prompt = """You are an expert botanist specializing in orchid taxonomy. Analyze this orchid specimen image and provide:

1. IDENTIFICATION:
   - Genus (most likely)
   - Species (if identifiable, or "sp." if uncertain)
   - Confidence score (0.0-1.0)

2. VISUAL FEATURES:
   - Flower color and patterns
   - Flower structure (sepals, petals, lip/labellum characteristics)
   - Leaf characteristics
   - Growth habit (epiphytic, terrestrial, lithophytic)
   - Any distinctive features

3. IMAGE QUALITY ASSESSMENT:
   - Image quality: excellent/good/fair/poor
   - Specimen completeness: complete/partial/fragment
   - Identification difficulty: easy/moderate/difficult/impossible

Format your response as JSON:
{
  "identified_genus": "Genus name",
  "identified_species": "species or sp.",
  "confidence_score": 0.85,
  "flower_color": "description",
  "flower_structure": "description",
  "leaf_characteristics": "description",
  "growth_habit": "epiphytic/terrestrial/lithophytic",
  "distinctive_features": ["feature1", "feature2"],
  "image_quality": "good",
  "specimen_completeness": "complete",
  "identification_difficulty": "moderate",
  "ai_description": "Detailed botanical description"
}"""
        
        # Add database comparison if available
        if database_taxonomy:
            genus = database_taxonomy.get('genus', 'Unknown')
            species = database_taxonomy.get('species', 'Unknown')
            base_prompt += f"\n\nNOTE: This specimen is recorded in our database as {genus} {species}. Please verify if your identification matches, and indicate your confidence in this classification."
        
        return base_prompt
    
    def _parse_ai_response(self, ai_text: str, database_taxonomy: Dict = None) -> Dict:
        """Parse AI response into structured data"""
        try:
            # Try to parse as JSON
            if '{' in ai_text and '}' in ai_text:
                # Extract JSON from response
                start = ai_text.find('{')
                end = ai_text.rfind('}') + 1
                json_str = ai_text[start:end]
                data = json.loads(json_str)
            else:
                # Fallback: create basic structure
                data = {
                    'identified_genus': 'Unknown',
                    'identified_species': 'sp.',
                    'confidence_score': 0.0,
                    'ai_description': ai_text
                }
            
            # Compare with database taxonomy if available
            if database_taxonomy:
                db_genus = database_taxonomy.get('genus', '').lower()
                db_species = database_taxonomy.get('species', '').lower()
                ai_genus = data.get('identified_genus', '').lower()
                ai_species = data.get('identified_species', '').lower()
                
                genus_match = db_genus == ai_genus
                species_match = db_species == ai_species
                
                data['matches_database_taxonomy'] = genus_match and species_match
                data['database_genus'] = database_taxonomy.get('genus')
                data['database_species'] = database_taxonomy.get('species')
                
                if genus_match and species_match:
                    data['taxonomy_confidence'] = 'confirmed'
                elif genus_match:
                    data['taxonomy_confidence'] = 'genus_match'
                else:
                    data['taxonomy_confidence'] = 'mismatch'
            
            return data
            
        except json.JSONDecodeError:
            logger.warning(f"Could not parse AI response as JSON: {ai_text[:200]}")
            return {
                'identified_genus': 'Parse Error',
                'identified_species': 'sp.',
                'confidence_score': 0.0,
                'ai_description': ai_text
            }
    
    def process_gbif_images(self, batch_size: int = 50, limit: Optional[int] = None, 
                           resume: bool = True):
        """
        Process all GBIF images with Vision AI
        
        Args:
            batch_size: Number of images to process before pausing
            limit: Maximum images to process (None = all)
            resume: Skip already analyzed images
        """
        logger.info("🤖 Starting Vision AI analysis of GBIF images...")
        
        # Setup results table
        self.setup_results_table()
        
        with self.engine.connect() as conn:
            # Get images to process
            if resume:
                # Skip already analyzed images
                query = text("""
                    SELECT 
                        oi.id,
                        oi.image_url,
                        ot.genus,
                        ot.species,
                        ot.scientific_name
                    FROM orchid_images oi
                    LEFT JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
                    LEFT JOIN vision_ai_results var ON oi.id = var.orchid_image_id
                    WHERE oi.image_url IS NOT NULL
                    AND oi.gbif_occurrence_key IS NOT NULL
                    AND var.id IS NULL
                    ORDER BY oi.id
                    LIMIT :limit
                """)
            else:
                # Process all images
                query = text("""
                    SELECT 
                        oi.id,
                        oi.image_url,
                        ot.genus,
                        ot.species,
                        ot.scientific_name
                    FROM orchid_images oi
                    LEFT JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
                    WHERE oi.image_url IS NOT NULL
                    AND oi.gbif_occurrence_key IS NOT NULL
                    ORDER BY oi.id
                    LIMIT :limit
                """)
            
            result = conn.execute(query, {'limit': limit or 1000000})
            images = result.fetchall()
            
            total_images = len(images)
            logger.info(f"📊 Found {total_images} GBIF images to analyze")
            
            if total_images == 0:
                logger.info("✅ All images already analyzed!")
                return self.stats
            
            self.stats['start_time'] = datetime.now()
            processed = 0
            
            for idx, row in enumerate(images, 1):
                image_id, url, genus, species, sci_name = row
                
                logger.info(f"🔍 [{idx}/{total_images}] Analyzing: {sci_name or genus or 'Unknown'}...")
                
                # Prepare database taxonomy for comparison
                db_taxonomy = {
                    'genus': genus,
                    'species': species,
                    'scientific_name': sci_name
                } if genus else None
                
                # Analyze with Vision AI
                analysis = self.analyze_image_with_vision(url, db_taxonomy)
                
                if analysis:
                    # Save results to database
                    self._save_analysis_result(conn, image_id, url, analysis)
                    self.stats['successful_analysis'] += 1
                else:
                    self.stats['failed_analysis'] += 1
                
                processed += 1
                self.stats['total_processed'] = processed
                
                # Rate limiting: OpenAI allows ~500 requests/minute
                # With high-detail images, be conservative
                time.sleep(0.5)  # 2 images per second = 120/minute (well under limit)
                
                # Pause between batches
                if processed % batch_size == 0:
                    elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = total_images - processed
                    eta_seconds = remaining / rate if rate > 0 else 0
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"BATCH COMPLETE: {processed}/{total_images}")
                    logger.info(f"Success: {self.stats['successful_analysis']} | Failed: {self.stats['failed_analysis']}")
                    logger.info(f"Rate: {rate:.2f} images/sec | ETA: {eta_seconds/60:.1f} minutes")
                    logger.info(f"Estimated cost so far: ${self.stats['estimated_cost']:.2f}")
                    logger.info(f"{'='*60}\n")
                    
                    # Pause for a moment
                    time.sleep(2)
            
            # Final summary
            elapsed_time = datetime.now() - self.stats['start_time']
            logger.info("\n" + "="*60)
            logger.info("VISION AI ANALYSIS COMPLETE")
            logger.info("="*60)
            logger.info(f"✅ Total processed: {self.stats['total_processed']}")
            logger.info(f"✅ Successful: {self.stats['successful_analysis']}")
            logger.info(f"❌ Failed: {self.stats['failed_analysis']}")
            logger.info(f"⏱️  Time elapsed: {elapsed_time}")
            logger.info(f"💰 Estimated cost: ${self.stats['estimated_cost']:.2f}")
            logger.info("="*60 + "\n")
            
            return self.stats
    
    def _save_analysis_result(self, conn, image_id: int, image_url: str, analysis: Dict):
        """Save vision AI analysis to database"""
        try:
            query = text("""
                INSERT INTO vision_ai_results (
                    orchid_image_id, image_url,
                    identified_genus, identified_species, confidence_score, ai_description,
                    flower_color, flower_structure, leaf_characteristics, growth_habit,
                    distinctive_features,
                    matches_database_taxonomy, database_genus, database_species, taxonomy_confidence,
                    model_used, prompt_used, tokens_used, analysis_cost, processing_time_seconds,
                    image_quality, specimen_completeness, identification_difficulty,
                    raw_response
                ) VALUES (
                    :image_id, :image_url,
                    :genus, :species, :confidence, :description,
                    :flower_color, :flower_structure, :leaf_chars, :growth_habit,
                    :features,
                    :matches_db, :db_genus, :db_species, :tax_confidence,
                    :model, :prompt, :tokens, :cost, :time,
                    :image_quality, :specimen_complete, :id_difficulty,
                    :raw_response
                )
            """)
            
            conn.execute(query, {
                'image_id': image_id,
                'image_url': image_url,
                'genus': analysis.get('identified_genus'),
                'species': analysis.get('identified_species'),
                'confidence': analysis.get('confidence_score', 0.0),
                'description': analysis.get('ai_description'),
                'flower_color': analysis.get('flower_color'),
                'flower_structure': analysis.get('flower_structure'),
                'leaf_chars': analysis.get('leaf_characteristics'),
                'growth_habit': analysis.get('growth_habit'),
                'features': analysis.get('distinctive_features', []),
                'matches_db': analysis.get('matches_database_taxonomy'),
                'db_genus': analysis.get('database_genus'),
                'db_species': analysis.get('database_species'),
                'tax_confidence': analysis.get('taxonomy_confidence'),
                'model': analysis.get('model_used'),
                'prompt': analysis.get('prompt_used'),
                'tokens': analysis.get('tokens_used'),
                'cost': analysis.get('analysis_cost'),
                'time': analysis.get('processing_time_seconds'),
                'image_quality': analysis.get('image_quality'),
                'specimen_complete': analysis.get('specimen_completeness'),
                'id_difficulty': analysis.get('identification_difficulty'),
                'raw_response': json.dumps(analysis.get('raw_response', {}))
            })
            conn.commit()
            
        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
    
    def get_analysis_progress(self) -> Dict[str, Any]:
        """Get current analysis progress statistics"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_analyzed,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(CASE WHEN matches_database_taxonomy = true THEN 1 END) as taxonomy_matches,
                    SUM(analysis_cost) as total_cost,
                    AVG(processing_time_seconds) as avg_processing_time
                FROM vision_ai_results
            """))
            stats = result.fetchone()
            
            # Get remaining count
            remaining_result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM orchid_images oi
                LEFT JOIN vision_ai_results var ON oi.id = var.orchid_image_id
                WHERE oi.image_url IS NOT NULL
                AND oi.gbif_occurrence_key IS NOT NULL
                AND var.id IS NULL
            """))
            remaining = remaining_result.scalar()
            
            return {
                'total_analyzed': stats[0] or 0,
                'remaining': remaining,
                'avg_confidence': round(stats[1] or 0.0, 2),
                'taxonomy_matches': stats[2] or 0,
                'total_cost': round(stats[3] or 0.0, 2),
                'avg_processing_time': round(stats[4] or 0.0, 2)
            }


def start_vision_analysis(batch_size: int = 50, limit: Optional[int] = None):
    """Start Vision AI analysis process"""
    analyzer = VisionAIAnalyzer()
    return analyzer.process_gbif_images(batch_size=batch_size, limit=limit)
