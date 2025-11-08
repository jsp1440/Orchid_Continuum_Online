"""
Multi-AI Image Generator for The Orchid Continuum
Compares DALL-E 3, FLUX (Replicate), and Together AI for botanical illustration generation
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import requests
import openai
import replicate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ImageGenResult:
    """Result from an AI image generation"""
    provider: str
    model: str
    image_url: str
    prompt_used: str
    processing_time: float
    cost_estimate: float
    success: bool
    error: Optional[str] = None
    style_quality: Optional[str] = None  # "excellent", "good", "fair", "poor"


class MultiAIImageGenerator:
    """Unified interface for multiple AI image generation providers"""
    
    def __init__(self):
        """Initialize all available image generation providers"""
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.replicate_token = os.environ.get("REPLICATE_API_KEY")
        self.together_key = os.environ.get("TOGETHER_AI_API_KEY")
        
        # Initialize clients
        if self.openai_key:
            openai.api_key = self.openai_key
            logger.info("✓ OpenAI (DALL-E 3) initialized")
        
        if self.replicate_token:
            os.environ["REPLICATE_API_TOKEN"] = self.replicate_token
            logger.info("✓ Replicate (FLUX) initialized")
        
        if self.together_key:
            logger.info("✓ Together AI initialized")
        
        # Cost estimates per image (approximate)
        self.cost_estimates = {
            "dall-e-3": 0.040,  # Standard quality
            "dall-e-3-hd": 0.080,  # HD quality
            "flux-schnell": 0.003,  # Fast FLUX
            "flux-dev": 0.010,  # Quality FLUX
            "flux-pro": 0.055,  # Professional FLUX
            "together-flux": 0.0,  # Free tier (3 months unlimited)
        }
    
    def generate_with_dalle3(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard"
    ) -> ImageGenResult:
        """Generate botanical illustration with DALL-E 3 (current system)"""
        start_time = datetime.now()
        
        try:
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
            
            image_url = response.data[0].url
            processing_time = (datetime.now() - start_time).total_seconds()
            cost_key = "dall-e-3-hd" if quality == "hd" else "dall-e-3"
            
            return ImageGenResult(
                provider="OpenAI",
                model="DALL-E 3",
                image_url=image_url,
                prompt_used=prompt,
                processing_time=processing_time,
                cost_estimate=self.cost_estimates[cost_key],
                success=True
            )
            
        except Exception as e:
            logger.error(f"DALL-E 3 generation failed: {str(e)}")
            return ImageGenResult(
                provider="OpenAI",
                model="DALL-E 3",
                image_url="",
                prompt_used=prompt,
                processing_time=(datetime.now() - start_time).total_seconds(),
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def generate_with_flux_replicate(
        self,
        prompt: str,
        model: str = "schnell",  # "schnell", "dev", or "pro"
        aspect_ratio: str = "1:1"
    ) -> ImageGenResult:
        """Generate botanical illustration with FLUX via Replicate (FREE $5 credits)"""
        start_time = datetime.now()
        
        # Model mapping
        model_map = {
            "schnell": "black-forest-labs/flux-schnell",  # Fastest, cheapest
            "dev": "black-forest-labs/flux-dev",  # Best quality/price ratio
            "pro": "black-forest-labs/flux-1.1-pro"  # Professional quality
        }
        
        model_id = model_map.get(model, model_map["schnell"])
        
        try:
            # Run FLUX model
            output = replicate.run(
                model_id,
                input={
                    "prompt": prompt,
                    "aspect_ratio": aspect_ratio,
                    "output_format": "png",
                    "output_quality": 100
                }
            )
            
            # Get image URL (output can be a URL or a file)
            if isinstance(output, list):
                image_url = output[0] if output else ""
            else:
                image_url = str(output)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            cost_key = f"flux-{model}"
            
            return ImageGenResult(
                provider="Replicate",
                model=f"FLUX {model.upper()}",
                image_url=image_url,
                prompt_used=prompt,
                processing_time=processing_time,
                cost_estimate=self.cost_estimates.get(cost_key, 0.01),
                success=True
            )
            
        except Exception as e:
            logger.error(f"FLUX Replicate generation failed: {str(e)}")
            return ImageGenResult(
                provider="Replicate",
                model=f"FLUX {model.upper()}",
                image_url="",
                prompt_used=prompt,
                processing_time=(datetime.now() - start_time).total_seconds(),
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def generate_with_together_ai(
        self,
        prompt: str,
        model: str = "flux-schnell"
    ) -> ImageGenResult:
        """Generate botanical illustration with Together AI (FREE for 3 months!)"""
        start_time = datetime.now()
        
        # Model mapping for Together AI
        model_map = {
            "flux-schnell": "black-forest-labs/FLUX.1-schnell-Free",
            "flux-dev": "black-forest-labs/FLUX.1-dev"
        }
        
        model_id = model_map.get(model, model_map["flux-schnell"])
        
        try:
            headers = {
                "Authorization": f"Bearer {self.together_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model_id,
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "steps": 4 if "schnell" in model else 28,
                "n": 1
            }
            
            response = requests.post(
                "https://api.together.xyz/v1/images/generations",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                image_url = result["data"][0]["url"]
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return ImageGenResult(
                    provider="Together AI",
                    model=f"FLUX {model.split('-')[1].upper()}",
                    image_url=image_url,
                    prompt_used=prompt,
                    processing_time=processing_time,
                    cost_estimate=0.0,  # Free for 3 months!
                    success=True
                )
            else:
                raise Exception(f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Together AI generation failed: {str(e)}")
            return ImageGenResult(
                provider="Together AI",
                model=f"FLUX {model.split('-')[1].upper()}",
                image_url="",
                prompt_used=prompt,
                processing_time=(datetime.now() - start_time).total_seconds(),
                cost_estimate=0.0,
                success=False,
                error=str(e)
            )
    
    def compare_all_generators(
        self,
        base_prompt: str,
        style: str = "scientific"  # "scientific", "artistic", "coloring", "labeled"
    ) -> Dict[str, ImageGenResult]:
        """Generate the same botanical illustration across all providers"""
        logger.info(f"🎨 Comparing all image generators for style: {style}")
        
        # Build style-specific prompts
        style_prompts = {
            "scientific": f"{base_prompt}, precise black ink botanical line drawing, scientific illustration, white background, detailed anatomical accuracy, high contrast, clean lines, no labels",
            
            "artistic": f"{base_prompt}, watercolor botanical illustration, Curtis's Botanical Magazine style, vibrant natural colors, museum quality, artistic rendering, detailed and elegant",
            
            "coloring": f"{base_prompt}, thick black outline coloring page, simple clear lines, white background, no shading, perfect for coloring books, kid-friendly, bold outlines",
            
            "labeled": f"{base_prompt}, scientific botanical diagram, black ink illustration with anatomical labels, arrows pointing to parts, educational diagram, detailed annotations"
        }
        
        prompt = style_prompts.get(style, base_prompt)
        results = {}
        
        # Test DALL-E 3
        if self.openai_key:
            logger.info("Generating with DALL-E 3...")
            results["dalle3"] = self.generate_with_dalle3(prompt)
        
        # Test FLUX via Replicate
        if self.replicate_token:
            logger.info("Generating with FLUX (Replicate)...")
            results["flux_replicate"] = self.generate_with_flux_replicate(prompt, model="schnell")
        
        # Test FLUX via Together AI
        if self.together_key:
            logger.info("Generating with FLUX (Together AI)...")
            results["flux_together"] = self.generate_with_together_ai(prompt, model="flux-schnell")
        
        return results
    
    def generate_comparison_report(
        self,
        results: Dict[str, ImageGenResult]
    ) -> str:
        """Generate a comparison report of all image generation results"""
        report_lines = [
            "=" * 80,
            "MULTI-AI IMAGE GENERATION COMPARISON REPORT",
            "=" * 80,
            ""
        ]
        
        # Summary table
        report_lines.append("PROVIDER SUMMARY:")
        report_lines.append("-" * 80)
        report_lines.append(f"{'Provider':<20} {'Model':<20} {'Success':<10} {'Time (s)':<12} {'Cost':<10}")
        report_lines.append("-" * 80)
        
        for key, result in results.items():
            status = "✓ Pass" if result.success else "✗ Fail"
            report_lines.append(
                f"{result.provider:<20} {result.model:<20} {status:<10} "
                f"{result.processing_time:<12.3f} ${result.cost_estimate:<9.4f}"
            )
        
        report_lines.append("")
        
        # Detailed results
        report_lines.append("\nDETAILED GENERATION RESULTS:")
        report_lines.append("=" * 80)
        
        total_cost = 0.0
        
        for key, result in results.items():
            report_lines.append(f"\n{result.provider} ({result.model}):")
            report_lines.append("-" * 80)
            
            if result.success:
                report_lines.append(f"Image URL: {result.image_url}")
                report_lines.append(f"Prompt: {result.prompt_used[:100]}...")
                report_lines.append(f"Processing time: {result.processing_time:.3f}s")
                report_lines.append(f"Estimated cost: ${result.cost_estimate:.4f}")
                total_cost += result.cost_estimate
            else:
                report_lines.append(f"ERROR: {result.error}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append(f"TOTAL COST FOR COMPARISON: ${total_cost:.4f}")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


# Test function
def test_multi_generator_comparison():
    """Test all image generators on a sample botanical prompt"""
    generator = MultiAIImageGenerator()
    
    # Test prompt
    test_species = "Paphiopedilum rothschildianum"
    base_prompt = f"A detailed botanical illustration of {test_species}, showing the distinctive flower with its characteristic pouch-shaped labellum and striped petals"
    
    # Test all styles
    styles = ["scientific", "artistic", "coloring", "labeled"]
    
    all_results = {}
    
    for style in styles:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing style: {style.upper()}")
        logger.info(f"{'='*80}")
        
        results = generator.compare_all_generators(base_prompt, style=style)
        all_results[style] = results
        
        report = generator.generate_comparison_report(results)
        print(f"\n{report}\n")
        
        # Save individual report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"image_gen_comparison_{style}_{timestamp}.txt"
        with open(report_path, "w") as f:
            f.write(report)
        
        logger.info(f"Report saved to: {report_path}")
    
    return all_results


if __name__ == "__main__":
    test_multi_generator_comparison()
