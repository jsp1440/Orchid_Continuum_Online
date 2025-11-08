"""
Botanical Drawing Generator
Creates scientific line drawings with anatomical labels for educational documentation.

Like botany students who must:
1. Draw the specimen (forces observation of every detail)
2. Label all anatomical parts (proves understanding of terminology)
3. Create permanent learning record (visual proof of comprehension)

The AI should do the same - generating labeled botanical illustrations proves it
understands what it's identifying, not just vocabulary memorization.
"""

import os
import logging
import base64
import io
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from openai import OpenAI

logger = logging.getLogger(__name__)

class BotanicalDrawingGenerator:
    """
    Generates scientific botanical line drawings with anatomical labels.
    
    Output:
    1. Unlabeled line drawing (clean, for printing/aesthetics)
    2. Labeled drawing (with arrows and anatomical terms)
    3. JPEG/PNG export ready
    """
    
    def __init__(self):
        self.openai_api_key = os.environ.get("VISIONAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("VISIONAI_API_KEY or OPENAI_API_KEY required for drawing generation")
        
        self.client = OpenAI(api_key=self.openai_api_key)
        
        # Scientific drawing style (for identification and labeling)
        self.scientific_style = """
        Professional botanical line drawing in the style of scientific botanical illustrations:
        - Fine black ink lines on white background
        - Precise anatomical detail showing all structures clearly
        - Clean, scientific style (like Curtis's Botanical Magazine or Flora illustrations)
        - No shading, no color - pure line work
        - Clear delineation of sepals, petals, labellum, column
        - Educational scientific illustration quality
        """
        
        # Artistic style (for beauty and decoration)
        self.artistic_style = """
        Beautiful watercolor botanical illustration in the style of vintage botanical art:
        - Soft, natural colors with botanical accuracy
        - Curtis's Botanical Magazine or Pierre-Joseph Redouté style
        - Delicate watercolor washes with fine pen & ink details
        - Elegant composition with white background
        - Artistic yet scientifically accurate
        - Museum-quality botanical art
        """
        
        # Coloring page style (for kids and artists)
        self.coloring_page_style = """
        Coloring page outline drawing perfect for coloring:
        - Thick, bold black outlines (suitable for crayons/colored pencils)
        - No shading, no colors - just clean outlines
        - Simple, clear shapes easy to color within the lines
        - Kid-friendly and artist-friendly
        - All anatomical parts clearly defined with bold lines
        - Professional coloring book quality
        """
    
    def generate_botanical_drawing(
        self, 
        original_image_url: str,
        botanical_description: str,
        identified_structures: Dict[str, any]
    ) -> Optional[Dict]:
        """
        Generate scientific line drawing from orchid photo.
        
        Args:
            original_image_url: URL of original orchid photograph
            botanical_description: Professional botanical description with Latin terms
            identified_structures: Dict of anatomical parts identified by Vision AI
        
        Returns:
            Dict with:
            - unlabeled_drawing: PIL Image (clean line drawing)
            - unlabeled_drawing_url: Base64 data URL for storage
            - drawing_metadata: Generation parameters
        """
        try:
            logger.info("🎨 Generating botanical line drawing...")
            
            # Create DALL-E prompt for scientific illustration
            prompt = self._create_drawing_prompt(botanical_description, identified_structures)
            
            # Generate line drawing using DALL-E
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
                response_format="url"
            )
            
            drawing_url = response.data[0].url
            
            # Download and convert to PIL Image
            drawing_response = requests.get(drawing_url)
            unlabeled_drawing = Image.open(io.BytesIO(drawing_response.content))
            
            # Convert to base64 for storage
            buffered = io.BytesIO()
            unlabeled_drawing.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            unlabeled_drawing_url = f"data:image/png;base64,{img_base64}"
            
            metadata = {
                'model': 'dall-e-3',
                'size': '1024x1024',
                'style': 'scientific_botanical_line_drawing',
                'prompt_length': len(prompt),
                'generation_timestamp': datetime.now().isoformat()
            }
            
            logger.info("✅ Botanical drawing generated successfully")
            
            return {
                'unlabeled_drawing': unlabeled_drawing,
                'unlabeled_drawing_url': unlabeled_drawing_url,
                'drawing_metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating botanical drawing: {e}")
            return None
    
    def _create_drawing_prompt(self, botanical_description: str, structures: Dict) -> str:
        """
        Create DALL-E prompt for scientific botanical illustration.
        
        Based on botanical illustration standards from:
        - Curtis's Botanical Magazine
        - Flora of North America illustrations
        - Traditional botanical art education
        """
        # Extract key features for the drawing
        flower_parts = []
        if structures.get('sepal_count'):
            flower_parts.append(f"{structures['sepal_count']} sepals")
        if structures.get('petal_count'):
            flower_parts.append(f"{structures['petal_count']} petals")
        if structures.get('labellum_shape'):
            flower_parts.append(f"labellum ({structures['labellum_shape']})")
        if structures.get('column_visible'):
            flower_parts.append("visible column")
        
        parts_description = ", ".join(flower_parts) if flower_parts else "orchid flower structures"
        
        prompt = f"""
        {self.scientific_style}
        
        Create a detailed botanical line drawing of an orchid flower showing:
        {parts_description}
        
        Botanical details to illustrate:
        {botanical_description[:500]}
        
        Style: Traditional botanical scientific illustration with precise line work.
        Medium: Black ink on white paper, fine detailed lines.
        Perspective: Clear frontal view showing all taxonomic characters.
        No labels, no text - pure illustration only.
        """
        
        return prompt.strip()
    
    def generate_artistic_illustration(
        self,
        original_image_url: str,
        botanical_description: str,
        identified_structures: Dict[str, any]
    ) -> Optional[Dict]:
        """
        Generate beautiful watercolor botanical illustration (artistic, colorful).
        Perfect for printing, gifts, decoration, and art collectors.
        """
        try:
            logger.info("🌺 Generating artistic watercolor illustration...")
            
            # Extract key features
            flower_parts = []
            if identified_structures.get('sepal_color'):
                flower_parts.append(f"sepals: {identified_structures['sepal_color']}")
            if identified_structures.get('petal_color'):
                flower_parts.append(f"petals: {identified_structures['petal_color']}")
            if identified_structures.get('labellum_color'):
                flower_parts.append(f"labellum: {identified_structures['labellum_color']}")
            
            colors_description = ", ".join(flower_parts) if flower_parts else "natural orchid colors"
            
            prompt = f"""
            {self.artistic_style}
            
            Create a beautiful watercolor botanical illustration of an orchid with:
            {colors_description}
            
            Botanical description:
            {botanical_description[:400]}
            
            Style: Vintage botanical art, Curtis's Botanical Magazine quality
            Medium: Watercolor with pen & ink details
            Colors: Soft, natural, botanically accurate
            Composition: Elegant, museum-quality
            """
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt.strip(),
                size="1024x1024",
                quality="hd",  # Higher quality for artistic versions
                n=1,
                response_format="url"
            )
            
            drawing_url = response.data[0].url
            drawing_response = requests.get(drawing_url)
            artistic_image = Image.open(io.BytesIO(drawing_response.content))
            
            # Convert to base64
            buffered = io.BytesIO()
            artistic_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            artistic_url = f"data:image/png;base64,{img_base64}"
            
            logger.info("✅ Artistic illustration generated successfully")
            
            return {
                'artistic_illustration': artistic_image,
                'artistic_illustration_url': artistic_url,
                'metadata': {
                    'model': 'dall-e-3',
                    'quality': 'hd',
                    'style': 'watercolor_botanical_art',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating artistic illustration: {e}")
            return None
    
    def generate_coloring_page(
        self,
        original_image_url: str,
        botanical_description: str,
        identified_structures: Dict[str, any]
    ) -> Optional[Dict]:
        """
        Generate coloring page with thick outlines (perfect for kids and artists).
        Can be printed and colored with crayons, colored pencils, or digital tools.
        """
        try:
            logger.info("🖍️  Generating coloring page...")
            
            # Extract structural details
            flower_parts = []
            if identified_structures.get('sepal_count'):
                flower_parts.append(f"{identified_structures['sepal_count']} sepals")
            if identified_structures.get('petal_count'):
                flower_parts.append(f"{identified_structures['petal_count']} petals")
            if identified_structures.get('labellum_shape'):
                flower_parts.append(f"labellum with {identified_structures['labellum_shape']} shape")
            
            parts_description = ", ".join(flower_parts) if flower_parts else "orchid flower"
            
            prompt = f"""
            {self.coloring_page_style}
            
            Create a coloring page outline drawing of an orchid showing:
            {parts_description}
            
            Requirements:
            - Thick, bold black outlines (perfect for coloring)
            - No colors, no shading - just clean black outlines on white
            - Simple enough for kids, detailed enough for adults
            - All parts clearly separated with bold lines
            - Professional coloring book quality
            
            Based on: {botanical_description[:300]}
            """
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt.strip(),
                size="1024x1024",
                quality="standard",
                n=1,
                response_format="url"
            )
            
            drawing_url = response.data[0].url
            drawing_response = requests.get(drawing_url)
            coloring_image = Image.open(io.BytesIO(drawing_response.content))
            
            # Convert to base64
            buffered = io.BytesIO()
            coloring_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            coloring_url = f"data:image/png;base64,{img_base64}"
            
            logger.info("✅ Coloring page generated successfully")
            
            return {
                'coloring_page': coloring_image,
                'coloring_page_url': coloring_url,
                'metadata': {
                    'model': 'dall-e-3',
                    'style': 'coloring_page',
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating coloring page: {e}")
            return None
    
    def add_anatomical_labels(
        self,
        unlabeled_drawing: Image.Image,
        structures: Dict[str, any],
        botanical_terms: List[str]
    ) -> Tuple[Image.Image, Dict]:
        """
        Add anatomical labels with arrows to the line drawing.
        
        Args:
            unlabeled_drawing: PIL Image of clean line drawing
            structures: Identified anatomical structures
            botanical_terms: Latin botanical terms to label
        
        Returns:
            Tuple of (labeled_image, label_positions_dict)
        """
        try:
            logger.info("🏷️  Adding anatomical labels to drawing...")
            
            # Create copy for labeling
            labeled_drawing = unlabeled_drawing.copy()
            draw = ImageDraw.Draw(labeled_drawing)
            
            # Try to load a clean font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Italic.ttf", 14)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            width, height = labeled_drawing.size
            
            # Define label positions for common orchid structures
            # (These are approximate - would be improved with actual object detection)
            labels_to_add = self._determine_labels_to_add(structures)
            
            label_positions = {}
            y_offset = 0
            
            for i, (term, description) in enumerate(labels_to_add.items()):
                # Position labels around the image with leader lines
                # Top labels
                if i % 4 == 0:
                    x, y = width - 250, 30 + y_offset
                # Right labels
                elif i % 4 == 1:
                    x, y = width - 250, height // 2 + y_offset
                # Bottom labels
                elif i % 4 == 2:
                    x, y = 50, height - 100 + y_offset
                # Left labels
                else:
                    x, y = 50, height // 3 + y_offset
                    y_offset += 30
                
                # Draw label text
                label_text = f"{term}: {description}"
                draw.text((x, y), label_text, fill='black', font=small_font)
                
                # Draw arrow/leader line (simple line for now)
                # In production, would use actual structure detection
                target_x = width // 2 + (i * 30 - 60)
                target_y = height // 2 + (i * 20 - 40)
                draw.line([(x, y), (target_x, target_y)], fill='black', width=1)
                
                label_positions[term] = [x, y]
            
            logger.info(f"✅ Added {len(labels_to_add)} anatomical labels")
            
            return labeled_drawing, label_positions
            
        except Exception as e:
            logger.error(f"❌ Error adding labels: {e}")
            return unlabeled_drawing, {}
    
    def _determine_labels_to_add(self, structures: Dict) -> Dict[str, str]:
        """
        Determine which anatomical labels to add based on identified structures.
        
        Returns dict of {term: description}
        """
        labels = {}
        
        # Sepals
        if structures.get('sepal_count'):
            sepal_desc = f"{structures.get('sepal_shape', 'shape observed')}"
            if structures.get('sepal_color'):
                sepal_desc += f", {structures['sepal_color']}"
            labels['Sepal'] = sepal_desc
        
        # Petals
        if structures.get('petal_count'):
            petal_desc = f"{structures.get('petal_shape', 'shape observed')}"
            if structures.get('petal_color'):
                petal_desc += f", {structures['petal_color']}"
            labels['Petal'] = petal_desc
        
        # Labellum (lip)
        if structures.get('labellum_shape'):
            lip_desc = structures['labellum_shape']
            if structures.get('labellum_markings'):
                lip_desc += f", {structures['labellum_markings']}"
            labels['Labellum'] = lip_desc
        
        # Column
        if structures.get('column_visible'):
            col_desc = structures.get('column_position', 'visible')
            labels['Column'] = col_desc
        
        # Spur
        if structures.get('spur_present'):
            spur_desc = structures.get('spur_length', 'present')
            labels['Spur'] = spur_desc
        
        # Inflorescence
        if structures.get('inflorescence_type'):
            labels['Inflorescence'] = structures['inflorescence_type']
        
        return labels
    
    def save_as_jpeg(self, image: Image.Image, quality: int = 95) -> str:
        """
        Convert PIL Image to JPEG base64 data URL for storage/export.
        
        Args:
            image: PIL Image
            quality: JPEG quality (1-100)
        
        Returns:
            Base64 data URL string
        """
        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=quality)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/jpeg;base64,{img_base64}"
    
    def generate_complete_documentation(
        self,
        original_image_url: str,
        botanical_description: str,
        identified_structures: Dict,
        generate_artistic: bool = False,
        generate_coloring: bool = False
    ) -> Optional[Dict]:
        """
        Generate complete botanical documentation with 4 visualization modes:
        1. Scientific line drawing (unlabeled) - for quizzes, clean documentation
        2. Labeled scientific drawing - for learning, verification
        3. Artistic watercolor illustration - for beauty, printing, gifts (optional)
        4. Coloring page - for kids and artists (optional)
        
        All versions exportable as JPEG and PNG.
        
        Args:
            generate_artistic: If True, also generates watercolor art version
            generate_coloring: If True, also generates coloring page version
        
        Returns:
            Dict with all requested drawing variations and metadata
        """
        try:
            result = {}
            
            # Step 1: Generate scientific line drawing (unlabeled)
            logger.info("📐 Generating scientific line drawing...")
            drawing_result = self.generate_botanical_drawing(
                original_image_url,
                botanical_description,
                identified_structures
            )
            
            if not drawing_result:
                logger.error("Failed to generate scientific drawing")
                return None
            
            unlabeled_drawing = drawing_result['unlabeled_drawing']
            result['scientific_drawing_url'] = drawing_result['unlabeled_drawing_url']
            
            # Step 2: Create labeled version
            logger.info("🏷️  Adding anatomical labels...")
            labeled_drawing, label_positions = self.add_anatomical_labels(
                unlabeled_drawing,
                identified_structures,
                identified_structures.get('botanical_terms_used', [])
            )
            
            buffered = io.BytesIO()
            labeled_drawing.save(buffered, format="PNG")
            labeled_png = f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"
            result['labeled_drawing_url'] = labeled_png
            result['label_positions'] = label_positions
            
            # Step 3: Generate artistic illustration (optional)
            if generate_artistic:
                logger.info("🎨 Generating artistic watercolor illustration...")
                artistic_result = self.generate_artistic_illustration(
                    original_image_url,
                    botanical_description,
                    identified_structures
                )
                if artistic_result:
                    result['artistic_illustration_url'] = artistic_result['artistic_illustration_url']
                else:
                    result['artistic_illustration_url'] = None
            else:
                result['artistic_illustration_url'] = None
            
            # Step 4: Generate coloring page (optional)
            if generate_coloring:
                logger.info("🖍️  Generating coloring page...")
                coloring_result = self.generate_coloring_page(
                    original_image_url,
                    botanical_description,
                    identified_structures
                )
                if coloring_result:
                    result['coloring_page_url'] = coloring_result['coloring_page_url']
                else:
                    result['coloring_page_url'] = None
            else:
                result['coloring_page_url'] = None
            
            # Metadata
            result['metadata'] = {
                'scientific_drawing': drawing_result['drawing_metadata'],
                'artistic_generated': generate_artistic,
                'coloring_generated': generate_coloring,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Complete documentation generated (artistic: {generate_artistic}, coloring: {generate_coloring})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error generating complete documentation: {e}")
            return None
