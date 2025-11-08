#!/usr/bin/env python3
"""
AI Vision Enrichment System
Analyzes orchid images using OpenAI GPT-4o Vision to extract visual metadata
Integrates with batch_gbif_eol_enrichment.py for complete data enrichment
"""

import os
import sys
import json
import base64
import logging
from typing import Dict, Optional, Any
from pathlib import Path
from PIL import Image
import io

from openai import OpenAI

# Database integration
from app import app, db
from models import OrchidRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIVisionEnrichment:
    """
    AI-powered visual metadata extraction from orchid images
    Uses OpenAI GPT-4o Vision API to analyze flower characteristics
    """
    
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
        self.client = None
        self.vision_model = "gpt-4o"  # Latest vision model
        
        if self.openai_key:
            try:
                self.client = OpenAI(api_key=self.openai_key)
                logger.info("✅ OpenAI Vision client initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
                self.client = None
        else:
            logger.warning("⚠️ OPENAI_API_KEY not set - AI vision disabled")
        
        # Vision analysis prompt for comprehensive metadata extraction
        self.vision_prompt = """
        You are an expert orchid botanist analyzing orchid photographs to extract comprehensive visual and botanical metadata.
        
        DO NOT attempt species identification - the species is already known. Your job is to extract VISUAL METADATA.
        
        Analyze this orchid image and extract ALL visible characteristics:
        
        **PHASE 1: Color & Visual Features**
        - flower_color: All visible colors (comma-separated: "white, pink, purple")
        - flower_pattern: Patterns visible (solid, spotted, striped, veined, blotched)
        - color_intensity: Color strength (pale, medium, vibrant, deep)
        - petal_texture: Surface appearance (waxy, velvety, glossy, matte)
        
        **PHASE 2: Flower Structure**
        - bloom_stage: Current state (bud, opening, fully_open, past_bloom)
        - inflorescence_type: Cluster type (raceme, panicle, spike, solitary, umbel)
        - inflorescence_position: Flower location (terminal, lateral, basal)
        - flower_count: Number of flowers visible
        - flower_size_cm: Estimated flower diameter in cm
        - labellum_type: Lip structure (simple, lobed, fringed, sac-like, complex)
        - flower_symmetry: Symmetry type (bilateral, radial)
        
        **PHASE 3: Plant Morphology**
        - leaf_shape: Form (lanceolate, ovate, terete, linear, oblong, elliptic)
        - leaf_texture: Appearance (thin, thick, leathery, succulent)
        - pseudobulb_presence: Has pseudobulbs? (true/false)
        - pseudobulb_form: If present (ovoid, conical, cylindrical, fusiform, absent)
        - growth_habit: Type (epiphytic, terrestrial, lithophytic)
        - rhizome_type: Pattern (sympodial, monopodial)
        
        **PHASE 4: Growing Indicators**
        - light_preference: Inferred from leaf color (low, medium, bright, very_bright)
        - temperature_zone: Inferred from leaf thickness (cool, intermediate, warm)
        - humidity_needs: From visible features (low, medium, high)
        - root_type_visible: If roots visible (thick_velamen, thin, aerial, terrestrial)
        
        **PHASE 5: Additional Botanical Features**
        - petal_sepal_difference: Are they different? (similar, distinct, very_distinct)
        - column_visibility: Can you see the column? (visible, partially_visible, not_visible)
        - spur_presence: Has a spur/nectar spur? (true/false/not_visible)
        - fragrance_indicators: Visual clues (likely_fragrant, unlikely_fragrant, unknown)
        - pollinator_syndrome: Likely pollinator (bee, moth, bird, fly, beetle, unknown)
        
        **PHASE 6: Image Quality & Context**
        - image_quality: Overall quality (excellent, good, fair, poor)
        - background_type: Photo context (natural_habitat, greenhouse, studio, garden)
        - photo_angle: Viewpoint (front, side, top, three_quarter)
        - lighting_quality: Illumination (natural, artificial, mixed, backlit)
        - image_caption: 2-3 sentence descriptive caption
        
        Return ONLY valid JSON with this exact structure:
        {
            "color_features": {
                "flower_color": "white, pink",
                "flower_pattern": "spotted",
                "color_intensity": "medium",
                "petal_texture": "waxy"
            },
            "flower_structure": {
                "bloom_stage": "fully_open",
                "inflorescence_type": "raceme",
                "inflorescence_position": "terminal",
                "flower_count": 5,
                "flower_size_cm": 8,
                "labellum_type": "lobed",
                "flower_symmetry": "bilateral"
            },
            "plant_morphology": {
                "leaf_shape": "lanceolate",
                "leaf_texture": "leathery",
                "pseudobulb_presence": true,
                "pseudobulb_form": "ovoid",
                "growth_habit": "epiphytic",
                "rhizome_type": "sympodial"
            },
            "growing_indicators": {
                "light_preference": "bright",
                "temperature_zone": "intermediate",
                "humidity_needs": "medium",
                "root_type_visible": "thick_velamen"
            },
            "botanical_features": {
                "petal_sepal_difference": "similar",
                "column_visibility": "visible",
                "spur_presence": false,
                "fragrance_indicators": "likely_fragrant",
                "pollinator_syndrome": "bee"
            },
            "image_metadata": {
                "image_quality": "excellent",
                "background_type": "greenhouse",
                "photo_angle": "front",
                "lighting_quality": "natural",
                "image_caption": "Beautiful orchid displaying multiple flowers on an arching stem with distinctive spotted pattern on the lip."
            },
            "confidence_score": 85,
            "analysis_notes": "Clear view of flowers, pseudobulbs visible, roots partially visible"
        }
        """
    
    def encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64 for OpenAI API"""
        try:
            # Handle both local file paths and static URLs
            if image_path.startswith('/static/'):
                image_path = image_path.replace('/static/', 'static/')
            
            full_path = Path(image_path)
            if not full_path.exists():
                logger.error(f"Image not found: {image_path}")
                return None
            
            # Read and encode image
            with open(full_path, 'rb') as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
                
        except Exception as e:
            logger.error(f"Image encoding error: {e}")
            return None
    
    def analyze_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Analyze orchid image using OpenAI Vision API"""
        if not self.client:
            logger.warning("OpenAI client not available")
            return None
        
        try:
            # Encode image
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return None
            
            logger.info(f"🔍 Analyzing image with AI vision...")
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse response
            result = response.choices[0].message.content
            
            # Extract JSON from response (handle markdown code blocks)
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(result)
            logger.info(f"✅ AI vision analysis complete (confidence: {analysis.get('confidence_score', 0)}%)")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return None
    
    def apply_vision_metadata(self, orchid: OrchidRecord, analysis: Dict[str, Any]) -> bool:
        """Apply AI vision analysis results to orchid record using existing schema fields"""
        try:
            if not analysis:
                return False
            
            updated = False
            
            # Store FULL analysis in existing ai_extracted_metadata JSON field
            orchid.ai_extracted_metadata = json.dumps(analysis)
            updated = True
            
            # Map to existing OrchidRecord fields only
            
            # Flower structure -> existing fields
            if 'flower_structure' in analysis:
                fs = analysis['flower_structure']
                # Map flower_size_cm to flower_size_mm (convert cm to mm)
                if fs.get('flower_size_cm'):
                    orchid.flower_size_mm = fs['flower_size_cm'] * 10
                    updated = True
                # Map flower_count
                if fs.get('flower_count'):
                    orchid.flower_count = fs['flower_count']
                    updated = True
                # Map bloom_stage to flowering_stage
                if fs.get('bloom_stage'):
                    orchid.flowering_stage = fs['bloom_stage']
                    updated = True
                    orchid.is_flowering = fs['bloom_stage'] in ['opening', 'fully_open', 'past_bloom']
            
            # Plant morphology -> existing fields
            if 'plant_morphology' in analysis:
                pm = analysis['plant_morphology']
                # Map pseudobulb_presence
                if pm.get('pseudobulb_presence') is not None:
                    orchid.pseudobulb_presence = pm['pseudobulb_presence']
                    updated = True
                # Map growth_habit if empty
                if pm.get('growth_habit') and not orchid.growth_habit:
                    orchid.growth_habit = pm['growth_habit']
                    updated = True
                # Map leaf_shape to leaf_form if empty
                if pm.get('leaf_shape') and not orchid.leaf_form:
                    orchid.leaf_form = pm['leaf_shape']
                    updated = True
            
            # Growing indicators -> existing fields
            if 'growing_indicators' in analysis:
                gi = analysis['growing_indicators']
                # Map light_preference to light_requirements if empty
                if gi.get('light_preference') and not orchid.light_requirements:
                    orchid.light_requirements = gi['light_preference']
                    updated = True
                # Map temperature_zone to climate_preference if empty
                if gi.get('temperature_zone') and not orchid.climate_preference:
                    orchid.climate_preference = gi['temperature_zone']
                    updated = True
            
            # AI description - create comprehensive description from analysis
            if not orchid.ai_description:
                description_parts = []
                if 'image_metadata' in analysis and analysis['image_metadata'].get('image_caption'):
                    description_parts.append(analysis['image_metadata']['image_caption'])
                if 'color_features' in analysis:
                    cf = analysis['color_features']
                    if cf.get('flower_color'):
                        description_parts.append(f"Flowers: {cf['flower_color']}")
                if 'flower_structure' in analysis:
                    fs = analysis['flower_structure']
                    if fs.get('inflorescence_type'):
                        description_parts.append(f"Inflorescence: {fs['inflorescence_type']}")
                
                if description_parts:
                    orchid.ai_description = '. '.join(description_parts)
                    updated = True
            
            # Set AI confidence from analysis
            if analysis.get('confidence_score'):
                orchid.ai_confidence = analysis['confidence_score'] / 100.0
                updated = True
            
            if updated:
                db.session.commit()
                logger.info(f"💾 Applied AI vision metadata to orchid {orchid.id}")
                logger.info(f"   📦 Full analysis stored in ai_extracted_metadata JSON field")
            
            return updated
            
        except Exception as e:
            logger.error(f"Error applying vision metadata: {e}")
            db.session.rollback()
            return False
    
    def enrich_orchid_with_vision(self, orchid: OrchidRecord) -> bool:
        """Complete vision enrichment for a single orchid"""
        if not orchid.image_url:
            logger.info(f"Skipping vision analysis - no image for orchid {orchid.id}")
            return False
        
        logger.info(f"🎨 AI Vision Analysis: {orchid.genus} {orchid.species} (ID: {orchid.id})")
        
        # Analyze image
        analysis = self.analyze_image(orchid.image_url)
        if not analysis:
            return False
        
        # Apply metadata
        return self.apply_vision_metadata(orchid, analysis)


if __name__ == '__main__':
    """Test AI vision enrichment on a sample orchid"""
    with app.app_context():
        enricher = AIVisionEnrichment()
        
        # Test on first orchid with an image
        orchid = OrchidRecord.query.filter(OrchidRecord.image_url.isnot(None)).first()
        if orchid:
            logger.info(f"Testing on: {orchid.genus} {orchid.species}")
            success = enricher.enrich_orchid_with_vision(orchid)
            logger.info(f"Result: {'Success' if success else 'Failed'}")
        else:
            logger.warning("No orchids with images found for testing")
