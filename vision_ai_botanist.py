"""
Digital Botanist Vision AI System
Enhanced orchid identification using botanical knowledge base:
- 1,763 botanical glossary terms with Latin etymology
- 90 dichotomous key sources for 27 genera
- Blind identification workflow (no species hints)
- Taxonomic character extraction using proper botanical terminology
- Botanical drawing generation (like botany students - visual proof of understanding)
"""

import os
import logging
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, text
from openai import OpenAI

from botanical_knowledge_loader import BotanicalKnowledgeLoader
from botanical_drawing_generator import BotanicalDrawingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BotanistVisionAI:
    """
    Enhanced Vision AI that acts like a trained botanist:
    - Uses botanical terminology and Latin names
    - Follows dichotomous keys for identification
    - Extracts taxonomic characters
    - Validates identification accuracy
    - Generates labeled botanical drawings (educational documentation)
    """
    
    def __init__(self, enable_drawings: bool = False, generate_artistic: bool = False, generate_coloring: bool = False):
        """
        Initialize Digital Botanist Vision AI
        
        Args:
            enable_drawings: If True, generates scientific botanical line drawings (costs API calls)
            generate_artistic: If True, also generates artistic watercolor illustrations (costs extra)
            generate_coloring: If True, also generates coloring pages (costs extra)
        """
        self.database_url = os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
            
        self.engine = create_engine(self.database_url)
        self.openai_api_key = os.environ.get("VISIONAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("VISIONAI_API_KEY or OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Load botanical knowledge base
        logger.info("🌺 Initializing Digital Botanist Vision AI...")
        self.knowledge = BotanicalKnowledgeLoader()
        self.knowledge.load_all_knowledge()
        
        # Initialize botanical drawing generator (optional)
        self.enable_drawings = enable_drawings
        self.generate_artistic = generate_artistic
        self.generate_coloring = generate_coloring
        
        if enable_drawings:
            self.drawing_generator = BotanicalDrawingGenerator()
            modes = []
            if enable_drawings:
                modes.append("scientific line drawings")
            if generate_artistic:
                modes.append("artistic watercolors")
            if generate_coloring:
                modes.append("coloring pages")
            logger.info(f"🎨 Botanical Drawing Generator enabled - creating: {', '.join(modes)}")
        else:
            self.drawing_generator = None
            logger.info("📸 Botanical Drawing Generator disabled - using photos only")
        
        self.stats = {
            'total_processed': 0,
            'successful_analysis': 0,
            'failed_analysis': 0,
            'correct_identifications': 0,
            'genus_matches': 0,
            'species_matches': 0,
            'drawings_generated': 0,
            'start_time': None,
            'estimated_cost': 0.0
        }
    
    def generate_botanical_drawing_for_analysis(self, image_url: str, analysis: Dict) -> Optional[Dict]:
        """
        Generate botanical line drawing with anatomical labels for a completed analysis.
        
        This creates visual proof that the AI understood what it identified, not just vocabulary.
        Like a botany student's labeled specimen drawing in a lab notebook.
        
        Args:
            image_url: Original specimen photo
            analysis: Completed botanical analysis with identified structures
        
        Returns:
            Dict with drawing URLs and metadata, or None if disabled/failed
        """
        if not self.enable_drawings or not self.drawing_generator:
            return None
        
        try:
            logger.info("🎨 Generating botanical drawing documentation...")
            
            # Extract identified structures for the drawing
            structures = {
                'sepal_count': analysis.get('sepal_count'),
                'sepal_shape': analysis.get('sepal_shape'),
                'sepal_color': analysis.get('sepal_color'),
                'petal_count': analysis.get('petal_count'),
                'petal_shape': analysis.get('petal_shape'),
                'petal_color': analysis.get('petal_color'),
                'labellum_shape': analysis.get('labellum_shape'),
                'labellum_color': analysis.get('labellum_color'),
                'labellum_markings': analysis.get('labellum_markings'),
                'column_visible': analysis.get('column_visible'),
                'column_position': analysis.get('column_position'),
                'spur_present': analysis.get('spur_present'),
                'spur_length': analysis.get('spur_length'),
                'inflorescence_type': analysis.get('inflorescence_type'),
                'botanical_terms_used': analysis.get('botanical_terms_used', [])
            }
            
            # Generate complete documentation (scientific + labeled + artistic + coloring)
            drawing_result = self.drawing_generator.generate_complete_documentation(
                image_url,
                analysis.get('botanical_description', ''),
                structures,
                generate_artistic=self.generate_artistic,
                generate_coloring=self.generate_coloring
            )
            
            if drawing_result:
                self.stats['drawings_generated'] += 1
                
                # Log which types were generated
                types_generated = []
                if drawing_result.get('scientific_drawing_url'):
                    types_generated.append("scientific")
                if drawing_result.get('artistic_illustration_url'):
                    types_generated.append("artistic")
                if drawing_result.get('coloring_page_url'):
                    types_generated.append("coloring")
                
                logger.info(f"✅ Botanical drawings generated: {', '.join(types_generated)}")
                return drawing_result
            else:
                logger.warning("⚠️  Drawing generation failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating botanical drawing: {e}")
            return None
    
    def setup_results_table(self):
        """Create enhanced results table for botanical analysis"""
        logger.info("📊 Setting up botanist_vision_results table...")
        
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS botanist_vision_results (
                    id SERIAL PRIMARY KEY,
                    orchid_image_id INTEGER REFERENCES orchid_images(id),
                    image_url TEXT NOT NULL,
                    
                    -- Blind Identification (AI doesn't know answer first)
                    blind_identification BOOLEAN DEFAULT true,
                    ai_genus VARCHAR(255),
                    ai_species VARCHAR(255),
                    ai_confidence FLOAT,
                    identification_method TEXT,  -- "dichotomous key", "morphology", "comparison"
                    
                    -- Validation Against Database
                    correct_genus BOOLEAN,
                    correct_species BOOLEAN,
                    database_genus VARCHAR(255),
                    database_species VARCHAR(255),
                    identification_accuracy VARCHAR(50),  -- "perfect", "genus_only", "incorrect"
                    
                    -- Taxonomic Characters Extracted (Botanical Lab Practical Style)
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
                    
                    -- Vegetative Characters
                    growth_habit VARCHAR(100),
                    leaf_arrangement VARCHAR(100),
                    leaf_shape TEXT,
                    leaf_texture TEXT,
                    pseudobulb_present BOOLEAN,
                    roots_visible BOOLEAN,
                    root_type VARCHAR(100),
                    
                    -- Diagnostic Features
                    distinctive_features TEXT[],
                    diagnostic_characters TEXT[],
                    botanical_terms_used TEXT[],  -- Latin terms used in description
                    
                    -- Key Following Process
                    dichotomous_key_used TEXT,  -- Which key source was referenced
                    key_characters_observed TEXT[],  -- Characters from the key that were visible
                    identification_reasoning TEXT,  -- Step-by-step key following process
                    
                    -- Full Botanical Description
                    botanical_description TEXT,  -- Professional botanical description with Latin terms
                    
                    -- Botanical Drawing Generation (Educational Documentation)
                    botanical_drawing_url TEXT,  -- AI-generated scientific line drawing (unlabeled)
                    labeled_drawing_url TEXT,    -- Same drawing with anatomical labels and arrows
                    drawing_labels JSONB,        -- {"sepal": [x, y], "petal": [x, y], ...}
                    drawing_metadata JSONB,      -- Generation parameters and model info
                    
                    -- Metadata
                    model_used VARCHAR(100),
                    tokens_used INTEGER,
                    analysis_cost FLOAT,
                    processing_time_seconds FLOAT,
                    
                    -- Image Quality
                    image_quality VARCHAR(50),
                    specimen_completeness VARCHAR(50),
                    characters_visible TEXT[],  -- Which taxonomic characters were visible
                    characters_obscured TEXT[],  -- Which were missing/unclear
                    
                    -- Full Response
                    raw_response JSONB,
                    
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            
            # Indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_botanist_results_image_id 
                ON botanist_vision_results(orchid_image_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_botanist_results_genus 
                ON botanist_vision_results(ai_genus)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_botanist_results_accuracy 
                ON botanist_vision_results(identification_accuracy)
            """))
            
            conn.commit()
            logger.info("✅ botanist_vision_results table ready")
    
    def analyze_specimen_blind(self, image_url: str, actual_taxonomy: Optional[Dict] = None, generate_drawing: Optional[bool] = None) -> Optional[Dict]:
        """
        Perform BLIND botanical identification (like a lab practical exam)
        
        Args:
            image_url: URL of specimen image
            actual_taxonomy: Actual genus/species (for validation AFTER identification)
            generate_drawing: Override class setting for drawing generation
        
        Returns:
            Analysis results with identification accuracy and optional botanical drawing
        """
        try:
            start_time = time.time()
            
            # Build botanical prompt WITHOUT giving away the answer
            prompt = self._build_botanist_prompt(blind=True)
            
            # Call Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
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
                                    "detail": "low"  # Cost-efficient mode
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,  # Increased for detailed botanical analysis
                temperature=0.3
            )
            
            # Extract response
            ai_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            cost = tokens_used * 0.000005
            processing_time = time.time() - start_time
            
            # Parse botanical analysis
            if ai_text:
                analysis = self._parse_botanical_response(ai_text)
            else:
                logger.error("No response text from Vision API")
                return None
            
            # VALIDATION: Compare AI identification to actual taxonomy
            if actual_taxonomy:
                analysis = self._validate_identification(analysis, actual_taxonomy)
            
            # Add metadata
            analysis['tokens_used'] = tokens_used
            analysis['analysis_cost'] = cost
            analysis['processing_time_seconds'] = processing_time
            analysis['model_used'] = 'gpt-4o'
            analysis['blind_identification'] = True
            analysis['raw_response'] = {
                'text': ai_text,
                'finish_reason': response.choices[0].finish_reason
            }
            
            logger.info(f"✅ Identified: {analysis.get('ai_genus')} {analysis.get('ai_species')} "
                       f"(confidence: {analysis.get('ai_confidence', 0):.2f}) "
                       f"| Accuracy: {analysis.get('identification_accuracy', 'unknown')}")
            
            self.stats['estimated_cost'] += cost
            
            # OPTIONAL: Generate botanical drawing (visual proof of understanding)
            should_generate = generate_drawing if generate_drawing is not None else self.enable_drawings
            
            if should_generate:
                drawing_result = self.generate_botanical_drawing_for_analysis(image_url, analysis)
                if drawing_result:
                    # Store all 4 drawing types (scientific, labeled, artistic, coloring)
                    analysis['botanical_drawing_url'] = drawing_result.get('scientific_drawing_url')
                    analysis['labeled_drawing_url'] = drawing_result.get('labeled_drawing_url')
                    analysis['artistic_illustration_url'] = drawing_result.get('artistic_illustration_url')
                    analysis['coloring_page_url'] = drawing_result.get('coloring_page_url')
                    analysis['drawing_labels'] = drawing_result.get('label_positions')
                    analysis['drawing_metadata'] = drawing_result.get('metadata')
                else:
                    analysis['botanical_drawing_url'] = None
                    analysis['labeled_drawing_url'] = None
                    analysis['artistic_illustration_url'] = None
                    analysis['coloring_page_url'] = None
                    analysis['drawing_labels'] = None
                    analysis['drawing_metadata'] = None
            else:
                analysis['botanical_drawing_url'] = None
                analysis['labeled_drawing_url'] = None
                analysis['artistic_illustration_url'] = None
                analysis['coloring_page_url'] = None
                analysis['drawing_labels'] = None
                analysis['drawing_metadata'] = None
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Botanical analysis error for {image_url}: {e}")
            return None
    
    def _build_botanist_prompt(self, blind: bool = True, genus_hint: Optional[str] = None) -> str:
        """Build enhanced botanical prompt with knowledge base"""
        
        # Load botanical terminology
        botanical_context = ""
        if self.knowledge.latin_terminology:
            # Sample key morphological terms
            key_terms = list(self.knowledge.latin_terminology.items())[:30]
            botanical_context = "## BOTANICAL TERMINOLOGY TO USE:\n"
            for term, data in key_terms:
                botanical_context += f"- **{term}**: {data['definition']}\n"
        
        # Add genus-specific key characters if hint provided
        genus_context = ""
        if genus_hint and genus_hint in self.knowledge.dichotomous_keys:
            genus_context = f"\n{self.knowledge.build_botanical_context(genus_hint)}\n"
        
        base_prompt = f"""You are a professional botanist conducting a LAB PRACTICAL EXAMINATION on an orchid specimen.

{botanical_context}

## YOUR TASK:
Identify this orchid specimen using proper botanical methodology and terminology.

### 1. INITIAL OBSERVATION (Describe what you see using botanical terms):
Examine the specimen systematically:

**Flower Morphology:**
- Sepal count, color, shape (use Latin descriptors)
- Petal count, color, shape
- Labellum (lip) characteristics: shape, color, markings, lobes
- Column: visible? position? shape?
- Spur: present? length?
- Inflorescence type: raceme, panicle, spike, solitary?
- Flower count, size, orientation

**Vegetative Features:**
- Growth habit: epiphytic, terrestrial, lithophytic?
- Leaves: arrangement, shape, texture
- Pseudobulbs: present? shape?
- Roots: visible? aerial? type?

### 2. IDENTIFICATION USING MORPHOLOGICAL CHARACTERS:
Based on the characters you observed, determine:
- **Genus** (with confidence 0.0-1.0)
- **Species** (with confidence 0.0-1.0)
- **Identification Method**: dichotomous key / morphological comparison / diagnostic characters

### 3. DIAGNOSTIC REASONING:
Explain your identification step-by-step:
- Which characters were most diagnostic?
- Which key features led you to this genus/species?
- What characters were visible vs. obscured?

### 4. BOTANICAL DESCRIPTION:
Write a professional botanical description using proper Latin terminology.

{genus_context}

## RESPONSE FORMAT (JSON):
```json
{{
  "ai_genus": "Genus",
  "ai_species": "species",
  "ai_confidence": 0.85,
  "identification_method": "morphological comparison",
  "sepal_count": 3,
  "sepal_color": "white with purple stripes",
  "sepal_shape": "lanceolate",
  "petal_count": 3,
  "petal_color": "white",
  "petal_shape": "linear",
  "labellum_shape": "trilobed",
  "labellum_color": "purple",
  "labellum_markings": "yellow crest",
  "column_visible": true,
  "column_position": "central, curved",
  "spur_present": false,
  "spur_length": null,
  "inflorescence_type": "raceme",
  "flower_count": 5,
  "flower_size": "medium (5-8cm)",
  "flower_orientation": "horizontal",
  "growth_habit": "epiphytic",
  "leaf_arrangement": "distichous",
  "leaf_shape": "linear-lanceolate",
  "leaf_texture": "coriaceous",
  "pseudobulb_present": false,
  "roots_visible": true,
  "root_type": "aerial, silvery velamen",
  "distinctive_features": ["trilobed labellum", "yellow crest", "purple stripes on sepals"],
  "diagnostic_characters": ["column shape", "labellum markings", "spur absent"],
  "botanical_terms_used": ["lanceolate", "trilobed", "coriaceous", "velamen"],
  "dichotomous_key_used": "Flora of North America Orchidaceae key",
  "key_characters_observed": ["resupinate flowers", "lateral sepals free", "labellum with basal spur"],
  "identification_reasoning": "Step-by-step reasoning process...",
  "botanical_description": "Full professional botanical description with Latin terms...",
  "image_quality": "excellent",
  "specimen_completeness": "flowers and leaves visible",
  "characters_visible": ["sepals", "petals", "labellum", "column", "leaves"],
  "characters_obscured": ["roots", "pseudobulb base"]
}}
```

**CRITICAL COUNTING INSTRUCTIONS:**
- For flower_count, sepal_count, petal_count: ALWAYS provide an integer number, never text like "numerous" or "many"
- If you cannot count exact number, estimate conservatively (e.g., 8-10 visible flowers → use 9)
- If truly impossible to count, use null instead of text
"""
        
        return base_prompt
    
    def _parse_botanical_response(self, ai_text: str) -> Dict:
        """Parse JSON response from Vision API"""
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in ai_text:
                json_start = ai_text.find("```json") + 7
                json_end = ai_text.find("```", json_start)
                json_str = ai_text[json_start:json_end].strip()
            elif "```" in ai_text:
                json_start = ai_text.find("```") + 3
                json_end = ai_text.find("```", json_start)
                json_str = ai_text[json_start:json_end].strip()
            else:
                # Try to find JSON object directly
                json_start = ai_text.find("{")
                json_end = ai_text.rfind("}") + 1
                json_str = ai_text[json_start:json_end]
            
            data = json.loads(json_str)
            return data
            
        except Exception as e:
            logger.error(f"❌ JSON parsing error: {e}")
            logger.error(f"Response text: {ai_text[:500]}")
            return {
                'ai_genus': 'Unknown',
                'ai_species': 'unknown',
                'ai_confidence': 0.0,
                'botanical_description': ai_text[:1000]
            }
    
    def _validate_identification(self, analysis: Dict, actual_taxonomy: Dict) -> Dict:
        """
        Validate AI identification against actual taxonomy.
        
        This is like grading a student's lab practical exam.
        """
        actual_genus = actual_taxonomy.get('genus', '').strip()
        actual_species = actual_taxonomy.get('species', '').strip()
        
        ai_genus = analysis.get('ai_genus', '').strip()
        ai_species = analysis.get('ai_species', '').strip()
        
        # Case-insensitive comparison
        genus_match = ai_genus.lower() == actual_genus.lower() if (ai_genus and actual_genus) else False
        species_match = ai_species.lower() == actual_species.lower() if (ai_species and actual_species) else False
        
        # Determine accuracy level
        if genus_match and species_match:
            accuracy = "perfect"
            self.stats['correct_identifications'] += 1
            self.stats['genus_matches'] += 1
            self.stats['species_matches'] += 1
        elif genus_match:
            accuracy = "genus_only"
            self.stats['genus_matches'] += 1
        else:
            accuracy = "incorrect"
        
        analysis['correct_genus'] = genus_match
        analysis['correct_species'] = species_match
        analysis['database_genus'] = actual_genus
        analysis['database_species'] = actual_species
        analysis['identification_accuracy'] = accuracy
        
        return analysis
    
    def batch_analyze_specimens(self, limit: Optional[int] = None, batch_size: int = 50, enable_drawings: Optional[bool] = None) -> Dict:
        """
        Batch analyze unprocessed specimens from database.
        
        Args:
            limit: Maximum number to process (None = all unprocessed)
            batch_size: Progress logging interval
            enable_drawings: Override class setting for drawing generation
        
        Returns:
            Statistics dict
        """
        with self.engine.connect() as conn:
            # Find unprocessed images
            query = text("""
                SELECT 
                    oi.id,
                    oi.image_url,
                    ot.genus,
                    ot.species,
                    ot.scientific_name
                FROM orchid_images oi
                LEFT JOIN orchid_taxonomy ot ON oi.taxonomy_id = ot.id
                LEFT JOIN botanist_vision_results bvr ON oi.id = bvr.orchid_image_id
                WHERE oi.image_url IS NOT NULL
                AND oi.gbif_occurrence_key IS NOT NULL
                AND bvr.id IS NULL
                ORDER BY oi.id
                LIMIT :limit
            """)
            
            result = conn.execute(query, {'limit': limit or 1000000})
            images = result.fetchall()
            
            total = len(images)
            logger.info(f"📊 Found {total} images for blind identification")
            
            if total == 0:
                logger.info("✅ All images already analyzed!")
                return self.stats
            
            self.stats['start_time'] = datetime.now()
            
            # Determine if we should generate drawings for this batch
            should_draw = enable_drawings if enable_drawings is not None else self.enable_drawings
            
            for idx, row in enumerate(images, 1):
                image_id, url, genus, species, sci_name = row
                
                logger.info(f"🔍 [{idx}/{total}] Analyzing specimen (actual: {genus} {species})...")
                
                # Prepare actual taxonomy (for validation AFTER identification)
                actual_taxonomy = {
                    'genus': genus,
                    'species': species,
                    'scientific_name': sci_name
                } if genus else None
                
                # Perform BLIND identification (with optional drawing)
                analysis = self.analyze_specimen_blind(url, actual_taxonomy, generate_drawing=should_draw)
                
                if analysis:
                    self._save_botanical_result(conn, image_id, url, analysis)
                    self.stats['successful_analysis'] += 1
                else:
                    self.stats['failed_analysis'] += 1
                
                self.stats['total_processed'] += 1
                
                # Rate limiting
                time.sleep(0.5)
                
                # Progress report
                if self.stats['total_processed'] % batch_size == 0:
                    self._log_progress(total)
                    time.sleep(2)
            
            self._log_final_stats()
            return self.stats
    
    def _safe_int(self, value) -> Optional[int]:
        """Convert value to int, return None if not possible"""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return None
        return None
    
    def _save_botanical_result(self, conn, image_id: int, url: str, analysis: Dict):
        """Save botanical analysis to database with optional botanical drawing"""
        try:
            query = text("""
                INSERT INTO botanist_vision_results (
                    orchid_image_id, image_url, blind_identification,
                    ai_genus, ai_species, ai_confidence, identification_method,
                    correct_genus, correct_species, database_genus, database_species, identification_accuracy,
                    sepal_count, sepal_color, sepal_shape,
                    petal_count, petal_color, petal_shape,
                    labellum_shape, labellum_color, labellum_markings,
                    column_visible, column_position,
                    spur_present, spur_length,
                    inflorescence_type, flower_count, flower_size, flower_orientation,
                    growth_habit, leaf_arrangement, leaf_shape, leaf_texture,
                    pseudobulb_present, roots_visible, root_type,
                    distinctive_features, diagnostic_characters, botanical_terms_used,
                    dichotomous_key_used, key_characters_observed, identification_reasoning,
                    botanical_description,
                    botanical_drawing_url, labeled_drawing_url, artistic_illustration_url, coloring_page_url, drawing_labels, drawing_metadata,
                    model_used, tokens_used, analysis_cost, processing_time_seconds,
                    image_quality, specimen_completeness, characters_visible, characters_obscured,
                    raw_response
                ) VALUES (
                    :image_id, :url, :blind,
                    :ai_genus, :ai_species, :confidence, :method,
                    :correct_genus, :correct_species, :db_genus, :db_species, :accuracy,
                    :sepal_cnt, :sepal_col, :sepal_shape,
                    :petal_cnt, :petal_col, :petal_shape,
                    :lab_shape, :lab_col, :lab_mark,
                    :col_vis, :col_pos,
                    :spur_pres, :spur_len,
                    :inflor_type, :flr_cnt, :flr_size, :flr_orient,
                    :growth, :leaf_arr, :leaf_shape, :leaf_tex,
                    :pseudo, :roots_vis, :root_type,
                    :features, :diag_chars, :terms,
                    :key_used, :key_chars, :reasoning,
                    :description,
                    :bot_draw, :lab_draw, :art_illust, :color_page, :draw_labels, :draw_meta,
                    :model, :tokens, :cost, :time,
                    :quality, :complete, :vis_chars, :obs_chars,
                    :raw
                )
            """)
            
            conn.execute(query, {
                'image_id': image_id,
                'url': url,
                'blind': analysis.get('blind_identification', True),
                'ai_genus': analysis.get('ai_genus'),
                'ai_species': analysis.get('ai_species'),
                'confidence': analysis.get('ai_confidence', 0.0),
                'method': analysis.get('identification_method'),
                'correct_genus': analysis.get('correct_genus'),
                'correct_species': analysis.get('correct_species'),
                'db_genus': analysis.get('database_genus'),
                'db_species': analysis.get('database_species'),
                'accuracy': analysis.get('identification_accuracy'),
                'sepal_cnt': self._safe_int(analysis.get('sepal_count')),
                'sepal_col': analysis.get('sepal_color'),
                'sepal_shape': analysis.get('sepal_shape'),
                'petal_cnt': self._safe_int(analysis.get('petal_count')),
                'petal_col': analysis.get('petal_color'),
                'petal_shape': analysis.get('petal_shape'),
                'lab_shape': analysis.get('labellum_shape'),
                'lab_col': analysis.get('labellum_color'),
                'lab_mark': analysis.get('labellum_markings'),
                'col_vis': analysis.get('column_visible'),
                'col_pos': analysis.get('column_position'),
                'spur_pres': analysis.get('spur_present'),
                'spur_len': analysis.get('spur_length'),
                'inflor_type': analysis.get('inflorescence_type'),
                'flr_cnt': self._safe_int(analysis.get('flower_count')),
                'flr_size': analysis.get('flower_size'),
                'flr_orient': analysis.get('flower_orientation'),
                'growth': analysis.get('growth_habit'),
                'leaf_arr': analysis.get('leaf_arrangement'),
                'leaf_shape': analysis.get('leaf_shape'),
                'leaf_tex': analysis.get('leaf_texture'),
                'pseudo': analysis.get('pseudobulb_present'),
                'roots_vis': analysis.get('roots_visible'),
                'root_type': analysis.get('root_type'),
                'features': analysis.get('distinctive_features'),
                'diag_chars': analysis.get('diagnostic_characters'),
                'terms': analysis.get('botanical_terms_used'),
                'key_used': analysis.get('dichotomous_key_used'),
                'key_chars': analysis.get('key_characters_observed'),
                'reasoning': analysis.get('identification_reasoning'),
                'description': analysis.get('botanical_description'),
                # Botanical drawings (4 types: scientific, labeled, artistic, coloring)
                'bot_draw': analysis.get('botanical_drawing_url'),
                'lab_draw': analysis.get('labeled_drawing_url'),
                'art_illust': analysis.get('artistic_illustration_url'),
                'color_page': analysis.get('coloring_page_url'),
                'draw_labels': json.dumps(analysis.get('drawing_labels')) if analysis.get('drawing_labels') else None,
                'draw_meta': json.dumps(analysis.get('drawing_metadata')) if analysis.get('drawing_metadata') else None,
                # Metadata
                'model': analysis.get('model_used'),
                'tokens': analysis.get('tokens_used'),
                'cost': analysis.get('analysis_cost'),
                'time': analysis.get('processing_time_seconds'),
                'quality': analysis.get('image_quality'),
                'complete': analysis.get('specimen_completeness'),
                'vis_chars': analysis.get('characters_visible'),
                'obs_chars': analysis.get('characters_obscured'),
                'raw': json.dumps(analysis.get('raw_response'))
            })
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
    
    def _log_progress(self, total: int):
        """Log progress statistics"""
        stats = self.stats
        pct = (stats['total_processed'] / total * 100) if total > 0 else 0
        
        accuracy_pct = (stats['correct_identifications'] / stats['successful_analysis'] * 100) if stats['successful_analysis'] > 0 else 0
        genus_pct = (stats['genus_matches'] / stats['successful_analysis'] * 100) if stats['successful_analysis'] > 0 else 0
        
        logger.info(f"""
        ============================================================
        PROGRESS: {stats['total_processed']}/{total} ({pct:.1f}%)
        ✅ Successful: {stats['successful_analysis']}
        ❌ Failed: {stats['failed_analysis']}
        🎯 Perfect ID: {stats['correct_identifications']} ({accuracy_pct:.1f}%)
        📊 Genus Match: {stats['genus_matches']} ({genus_pct:.1f}%)
        🎨 Drawings: {stats.get('drawings_generated', 0)}
        💰 Estimated Cost: ${stats['estimated_cost']:.2f}
        ============================================================
        """)
    
    def _log_final_stats(self):
        """Log final statistics"""
        if not self.stats['start_time']:
            return
        
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        stats = self.stats
        
        accuracy_pct = (stats['correct_identifications'] / stats['successful_analysis'] * 100) if stats['successful_analysis'] > 0 else 0
        genus_pct = (stats['genus_matches'] / stats['successful_analysis'] * 100) if stats['successful_analysis'] > 0 else 0
        
        logger.info(f"""
        
        ╔══════════════════════════════════════════════════════════════╗
        ║           DIGITAL BOTANIST VISION AI - FINAL REPORT         ║
        ╚══════════════════════════════════════════════════════════════╝
        
        📊 ANALYSIS RESULTS:
           Total Processed:     {stats['total_processed']}
           Successful:          {stats['successful_analysis']}
           Failed:              {stats['failed_analysis']}
        
        🎯 IDENTIFICATION ACCURACY:
           Perfect Match:       {stats['correct_identifications']} ({accuracy_pct:.1f}%)
           Genus Match:         {stats['genus_matches']} ({genus_pct:.1f}%)
           Species Match:       {stats['species_matches']}
        
        🎨 BOTANICAL DRAWINGS:
           Generated:           {stats.get('drawings_generated', 0)}
        
        ⏱️  PERFORMANCE:
           Duration:            {duration:.1f} seconds
           Avg per image:       {duration/stats['total_processed']:.1f}s
        
        💰 COST:
           Estimated Total:     ${stats['estimated_cost']:.2f}
        
        """)


if __name__ == "__main__":
    # Example: Run Digital Botanist on 10 specimens WITHOUT botanical drawings
    # (Drawings can be enabled by setting enable_drawings=True)
    
    botanist = BotanistVisionAI(enable_drawings=False)  # Disable drawings for speed
    botanist.setup_results_table()
    
    # Process 10 specimens
    results = botanist.batch_analyze_specimens(limit=10)
    
    print("\n✅ Analysis complete!")
    print(f"Check the monitoring dashboard at: /botanist/monitor")
