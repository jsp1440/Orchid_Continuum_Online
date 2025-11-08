#!/usr/bin/env python3
"""
AI Model Comparison Test
========================
Compare GPT-4o-mini (vision) vs GPT-3.5-turbo (text) for orchid metadata extraction

Tests:
1. GPT-4o-mini: Analyzes photos to extract visual metadata
2. GPT-3.5-turbo: Uses genus/species name to provide botanical knowledge
3. Side-by-side comparison of results
4. Cost and accuracy analysis
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List
import tempfile
import requests
from PIL import Image
import io
from openai import OpenAI

from app import app
from models import OrchidRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIModelComparator:
    """Compare different AI models for orchid metadata extraction"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.results = []
    
    def download_image(self, url: str) -> str:
        """Download and convert image"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img.convert('RGB').save(temp_file.name, 'JPEG', quality=95)
            temp_file.close()
            return temp_file.name
        except:
            return None
    
    def test_gpt4o_mini_vision(self, image_path: str, orchid_name: str) -> Dict:
        """Test GPT-4o-mini with vision capabilities"""
        try:
            import base64
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            prompt = """Analyze this orchid photo and extract metadata. Return JSON with:
{
  "growth_habit": "value",
  "temperature": "value", 
  "light": "value",
  "humidity": "value",
  "bloom_season": "value",
  "difficulty": "value",
  "source": "Visual analysis of photo"
}"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                    ]
                }],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            result['cost'] = 0.003
            result['model'] = 'GPT-4o-mini (vision)'
            return result
        except Exception as e:
            logger.error(f"GPT-4o-mini error: {e}")
            return {"error": str(e), "cost": 0.003}
    
    def test_gpt35_turbo_text(self, genus: str, species: str) -> Dict:
        """Test GPT-3.5-turbo with text-only botanical knowledge"""
        try:
            scientific_name = f"{genus} {species}"
            
            prompt = f"""You are an orchid expert. Provide metadata for {scientific_name} based on your botanical knowledge. Return JSON with:
{{
  "growth_habit": "typical growth habit for this genus",
  "temperature": "typical temperature preference",
  "light": "typical light requirements",
  "humidity": "typical humidity needs",
  "bloom_season": "typical bloom season for this species",
  "difficulty": "typical growing difficulty",
  "source": "Botanical knowledge of genus {genus}"
}}

Provide factual information based on what is typical for this genus/species."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert orchidologist. Provide accurate botanical information as JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=500,
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            result['cost'] = 0.0001
            result['model'] = 'GPT-3.5-turbo (text)'
            return result
        except Exception as e:
            logger.error(f"GPT-3.5 error: {e}")
            return {"error": str(e), "cost": 0.0001}
    
    def compare_models(self, orchid: OrchidRecord) -> Dict:
        """Run both models and compare results"""
        logger.info(f"🔬 Testing: {orchid.genus} {orchid.species}")
        
        comparison = {
            'orchid_id': orchid.id,
            'genus': orchid.genus,
            'species': orchid.species,
            'image_url': orchid.image_url,
            'gpt4o_mini': None,
            'gpt35_turbo': None,
            'comparison': {},
            'cost_difference': 0
        }
        
        # Test GPT-4o-mini (vision)
        if orchid.image_url:
            temp_image = self.download_image(orchid.image_url)
            if temp_image:
                comparison['gpt4o_mini'] = self.test_gpt4o_mini_vision(
                    temp_image, 
                    f"{orchid.genus} {orchid.species}"
                )
                os.unlink(temp_image)
                logger.info(f"  ✅ GPT-4o-mini: ${comparison['gpt4o_mini']['cost']:.4f}")
        
        # Test GPT-3.5-turbo (text)
        comparison['gpt35_turbo'] = self.test_gpt35_turbo_text(orchid.genus, orchid.species)
        logger.info(f"  ✅ GPT-3.5-turbo: ${comparison['gpt35_turbo']['cost']:.4f}")
        
        # Compare results
        if comparison['gpt4o_mini'] and comparison['gpt35_turbo']:
            gpt4_data = comparison['gpt4o_mini']
            gpt35_data = comparison['gpt35_turbo']
            
            for field in ['growth_habit', 'temperature', 'light', 'humidity', 'bloom_season', 'difficulty']:
                gpt4_val = gpt4_data.get(field, 'Unknown')
                gpt35_val = gpt35_data.get(field, 'Unknown')
                
                comparison['comparison'][field] = {
                    'gpt4o_mini': gpt4_val,
                    'gpt35_turbo': gpt35_val,
                    'match': gpt4_val.lower() == gpt35_val.lower() if gpt4_val != 'Unknown' and gpt35_val != 'Unknown' else False
                }
            
            # Calculate cost difference
            comparison['cost_difference'] = gpt4_data.get('cost', 0) - gpt35_data.get('cost', 0)
            
            # Determine which is better
            matches = sum(1 for v in comparison['comparison'].values() if v.get('match'))
            comparison['agreement_score'] = matches / len(comparison['comparison']) if comparison['comparison'] else 0
        
        return comparison
    
    def run_comparison_test(self, limit: int = 10):
        """Run comparison test on multiple orchids"""
        with app.app_context():
            orchids = OrchidRecord.query.filter(
                OrchidRecord.image_url.isnot(None),
                OrchidRecord.image_url != ''
            ).limit(limit).all()
            
            logger.info(f"🚀 Comparing AI models on {len(orchids)} orchids\n")
            
            for idx, orchid in enumerate(orchids, 1):
                logger.info(f"{'='*60}")
                logger.info(f"📊 {idx}/{len(orchids)}")
                
                result = self.compare_models(orchid)
                self.results.append(result)
            
            # Save results
            output_file = f"ai_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            # Generate summary
            self.print_summary(output_file)
    
    def print_summary(self, output_file: str):
        """Print comparison summary"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 AI MODEL COMPARISON SUMMARY")
        logger.info(f"{'='*60}\n")
        
        total_orchids = len(self.results)
        total_gpt4_cost = sum(r.get('gpt4o_mini', {}).get('cost', 0) for r in self.results)
        total_gpt35_cost = sum(r.get('gpt35_turbo', {}).get('cost', 0) for r in self.results)
        
        avg_agreement = sum(r.get('agreement_score', 0) for r in self.results) / total_orchids if total_orchids > 0 else 0
        
        logger.info(f"📁 Results saved to: {output_file}")
        logger.info(f"🌺 Orchids tested: {total_orchids}")
        logger.info(f"\n💰 COST COMPARISON:")
        logger.info(f"  GPT-4o-mini (vision): ${total_gpt4_cost:.4f}")
        logger.info(f"  GPT-3.5-turbo (text): ${total_gpt35_cost:.4f}")
        logger.info(f"  Difference: ${total_gpt4_cost - total_gpt35_cost:.4f} ({(total_gpt4_cost/total_gpt35_cost):.0f}x more expensive)")
        
        logger.info(f"\n📈 AGREEMENT SCORE:")
        logger.info(f"  Average agreement: {avg_agreement*100:.1f}%")
        logger.info(f"  (How often both models agree on the same metadata)")
        
        # Field-specific comparison
        field_stats = {}
        for result in self.results:
            for field, data in result.get('comparison', {}).items():
                if field not in field_stats:
                    field_stats[field] = {'matches': 0, 'total': 0}
                field_stats[field]['total'] += 1
                if data.get('match'):
                    field_stats[field]['matches'] += 1
        
        logger.info(f"\n📊 FIELD-BY-FIELD AGREEMENT:")
        for field, stats in sorted(field_stats.items()):
            match_rate = (stats['matches'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"  {field}: {match_rate:.0f}% agreement ({stats['matches']}/{stats['total']})")
        
        logger.info(f"\n🎯 RECOMMENDATION:")
        if avg_agreement > 0.7:
            logger.info(f"  ✅ High agreement ({avg_agreement*100:.0f}%) - GPT-3.5-turbo is 30x cheaper and produces similar results!")
            logger.info(f"     Use GPT-3.5-turbo for text-based metadata (genus/species knowledge)")
            logger.info(f"     Use GPT-4o-mini ONLY when you need visual analysis from photos")
        elif avg_agreement > 0.5:
            logger.info(f"  ⚠️ Moderate agreement ({avg_agreement*100:.0f}%) - Both models provide value")
            logger.info(f"     Hybrid approach: GPT-4o-mini for visual data, GPT-3.5 for genus knowledge")
        else:
            logger.info(f"  ❌ Low agreement ({avg_agreement*100:.0f}%) - Models see different things")
            logger.info(f"     GPT-4o-mini better for photo analysis, GPT-3.5 for species facts")
        
        logger.info(f"\n💡 COST-OPTIMIZED STRATEGY (2,897 orchids):")
        logger.info(f"  All GPT-4o-mini: ${2897 * 0.003:.2f}")
        logger.info(f"  All GPT-3.5-turbo: ${2897 * 0.0001:.2f}")
        logger.info(f"  Hybrid (best of both): ${2897 * (0.003 + 0.0001):.2f}")

if __name__ == "__main__":
    comparator = AIModelComparator()
    comparator.run_comparison_test(limit=10)
