"""
Multi-AI Vision Analyzer for The Orchid Continuum
Compares GPT-4o Vision, Hugging Face SmolVLM, and Google Gemini for botanical image analysis
"""

import os
import base64
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

# API clients
import openai
from huggingface_hub import InferenceClient
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VisionResult:
    """Result from a vision AI analysis"""
    provider: str
    model: str
    analysis: str
    confidence: Optional[float]
    processing_time: float
    cost_estimate: float
    botanical_terms_found: List[str]
    success: bool
    error: Optional[str] = None


class MultiAIVisionAnalyzer:
    """Unified interface for multiple AI vision providers"""
    
    def __init__(self):
        """Initialize all available AI providers"""
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.hf_key = os.environ.get("HUGGINGFACE_API_KEY")
        self.gemini_key = os.environ.get("GOOGLE_API_KEY")
        
        # Initialize clients
        if self.openai_key:
            openai.api_key = self.openai_key
            logger.info("✓ OpenAI initialized")
        
        if self.hf_key:
            self.hf_client = InferenceClient(token=self.hf_key)
            logger.info("✓ Hugging Face initialized")
        
        if self.gemini_key:
            logger.info("✓ Gemini API key found")
        
        # Cost estimates per 1K tokens/images (approximate)
        self.cost_estimates = {
            "gpt-4o": 0.005,  # $5 per 1K images
            "smolvlm": 0.0,   # Free tier
            "gemini-2.5": 0.0,  # Free tier (generous limits)
        }
    
    def analyze_with_gpt4o(
        self,
        image_path: str,
        prompt: str,
        detail: str = "high"
    ) -> VisionResult:
        """Analyze image using GPT-4o Vision (existing system)"""
        start_time = datetime.now()
        
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Call GPT-4o Vision
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}",
                                "detail": detail
                            }
                        }
                    ]
                }],
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract botanical terms (simple keyword detection)
            botanical_terms = self._extract_botanical_terms(analysis)
            
            return VisionResult(
                provider="OpenAI",
                model="gpt-4o",
                analysis=analysis,
                confidence=None,  # GPT-4o doesn't provide confidence scores
                processing_time=processing_time,
                cost_estimate=self.cost_estimates["gpt-4o"],
                botanical_terms_found=botanical_terms,
                success=True
            )
            
        except Exception as e:
            logger.error(f"GPT-4o analysis failed: {str(e)}")
            return VisionResult(
                provider="OpenAI",
                model="gpt-4o",
                analysis="",
                confidence=None,
                processing_time=(datetime.now() - start_time).total_seconds(),
                cost_estimate=0.0,
                botanical_terms_found=[],
                success=False,
                error=str(e)
            )
    
    def analyze_with_huggingface(
        self,
        image_path: str,
        prompt: str,
        model: str = "HuggingFaceTB/SmolVLM-Instruct"
    ) -> VisionResult:
        """Analyze image using Hugging Face vision models (FREE)"""
        start_time = datetime.now()
        
        try:
            # Read image
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Try image-to-text endpoint first (simpler, often free)
            try:
                result = self.hf_client.image_to_text(
                    image_bytes,
                    model="Salesforce/blip-image-captioning-large"
                )
                analysis = result
                
            except Exception as e1:
                # Fallback: Try visual question answering
                logger.info(f"Image-to-text failed, trying VQA: {str(e1)}")
                try:
                    result = self.hf_client.visual_question_answering(
                        image=image_bytes,
                        question=prompt,
                        model="dandelin/vilt-b32-finetuned-vqa"
                    )
                    analysis = result[0]["answer"] if result else "No analysis available"
                    
                except Exception as e2:
                    # Final fallback: Use inference API directly
                    logger.info(f"VQA failed, using direct API: {str(e2)}")
                    headers = {"Authorization": f"Bearer {self.hf_key}"}
                    api_url = f"https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
                    
                    response = requests.post(
                        api_url,
                        headers=headers,
                        data=image_bytes
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        analysis = result[0]["generated_text"] if isinstance(result, list) else str(result)
                    else:
                        raise Exception(f"API error: {response.status_code} - {response.text}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            botanical_terms = self._extract_botanical_terms(str(analysis))
            
            return VisionResult(
                provider="Hugging Face",
                model="BLIP/ViLT",
                analysis=str(analysis),
                confidence=None,
                processing_time=processing_time,
                cost_estimate=0.0,  # Free!
                botanical_terms_found=botanical_terms,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Hugging Face analysis failed: {str(e)}")
            return VisionResult(
                provider="Hugging Face",
                model="BLIP/ViLT",
                analysis="",
                confidence=None,
                processing_time=(datetime.now() - start_time).total_seconds(),
                cost_estimate=0.0,
                botanical_terms_found=[],
                success=False,
                error=str(e)
            )
    
    def analyze_with_gemini(
        self,
        image_path: str,
        prompt: str
    ) -> VisionResult:
        """Analyze image using Google Gemini 2.5 (FREE with generous limits)"""
        start_time = datetime.now()
        
        if not self.gemini_key:
            return VisionResult(
                provider="Google",
                model="gemini-2.5",
                analysis="",
                confidence=None,
                processing_time=0.0,
                cost_estimate=0.0,
                botanical_terms_found=[],
                success=False,
                error="GOOGLE_API_KEY not set"
            )
        
        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Call Gemini API
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }]
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                analysis = result["candidates"][0]["content"]["parts"][0]["text"]
                processing_time = (datetime.now() - start_time).total_seconds()
                botanical_terms = self._extract_botanical_terms(analysis)
                
                return VisionResult(
                    provider="Google",
                    model="gemini-2.0-flash",
                    analysis=analysis,
                    confidence=None,
                    processing_time=processing_time,
                    cost_estimate=0.0,  # Free tier
                    botanical_terms_found=botanical_terms,
                    success=True
                )
            else:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return VisionResult(
                provider="Google",
                model="gemini-2.5",
                analysis="",
                confidence=None,
                processing_time=(datetime.now() - start_time).total_seconds(),
                cost_estimate=0.0,
                botanical_terms_found=[],
                success=False,
                error=str(e)
            )
    
    def analyze_with_best_free_option(
        self,
        image_path: str,
        prompt: str
    ) -> VisionResult:
        """
        ORCHESTRATOR: Try free providers first, fall back to paid only if needed.
        Priority: Gemini (free) → Hugging Face (free) → GPT-4o (paid)
        """
        logger.info(f"🎯 Analyzing with best free option: {image_path}")
        
        # Try Gemini first (FREE, best quality)
        if self.gemini_key:
            logger.info("→ Trying Gemini (FREE)...")
            result = self.analyze_with_gemini(image_path, prompt)
            if result.success:
                logger.info("✓ Gemini succeeded! Cost: $0.00")
                return result
            else:
                logger.warning(f"✗ Gemini failed: {result.error}")
        
        # Fall back to Hugging Face (FREE, basic)
        if self.hf_key:
            logger.info("→ Trying Hugging Face (FREE)...")
            result = self.analyze_with_huggingface(image_path, prompt)
            if result.success:
                logger.info("✓ Hugging Face succeeded! Cost: $0.00")
                return result
            else:
                logger.warning(f"✗ Hugging Face failed: {result.error}")
        
        # Final fallback to GPT-4o (PAID)
        if self.openai_key:
            logger.info("→ Using GPT-4o (PAID FALLBACK)...")
            result = self.analyze_with_gpt4o(image_path, prompt)
            if result.success:
                logger.warning(f"⚠ Using paid GPT-4o! Cost: ${result.cost_estimate:.4f}")
                return result
            else:
                logger.error(f"✗ GPT-4o failed: {result.error}")
                return result
        
        # No providers available
        return VisionResult(
            provider="None",
            model="N/A",
            analysis="",
            confidence=None,
            processing_time=0.0,
            cost_estimate=0.0,
            botanical_terms_found=[],
            success=False,
            error="No AI providers available or all providers failed"
        )
    
    def compare_all_providers(
        self,
        image_path: str,
        prompt: str
    ) -> Dict[str, VisionResult]:
        """Run the same image through all available providers and compare results"""
        logger.info(f"🔬 Comparing all AI providers for: {image_path}")
        
        results = {}
        
        # Test GPT-4o
        if self.openai_key:
            logger.info("Testing GPT-4o...")
            results["gpt4o"] = self.analyze_with_gpt4o(image_path, prompt)
        
        # Test Hugging Face
        if self.hf_key:
            logger.info("Testing Hugging Face...")
            results["huggingface"] = self.analyze_with_huggingface(image_path, prompt)
        
        # Test Gemini
        if self.gemini_key:
            logger.info("Testing Gemini...")
            results["gemini"] = self.analyze_with_gemini(image_path, prompt)
        
        return results
    
    def _extract_botanical_terms(self, text: str) -> List[str]:
        """Extract botanical terminology from analysis text"""
        # Common botanical terms to look for
        botanical_keywords = [
            "sepal", "petal", "labellum", "column", "anther", "pollinia",
            "dorsal", "lateral", "inflorescence", "pseudobulb", "rhizome",
            "epiphyte", "terrestrial", "sympodial", "monopodial",
            "ovate", "lanceolate", "elliptic", "cordate", "pubescent",
            "glabrous", "ciliate", "terete", "plicate"
        ]
        
        text_lower = text.lower()
        found_terms = [term for term in botanical_keywords if term in text_lower]
        
        return found_terms
    
    def generate_comparison_report(
        self,
        results: Dict[str, VisionResult]
    ) -> str:
        """Generate a comparison report of all provider results"""
        report_lines = [
            "=" * 80,
            "MULTI-AI VISION ANALYSIS COMPARISON REPORT",
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
        report_lines.append("\nDETAILED ANALYSIS RESULTS:")
        report_lines.append("=" * 80)
        
        for key, result in results.items():
            report_lines.append(f"\n{result.provider} ({result.model}):")
            report_lines.append("-" * 80)
            
            if result.success:
                report_lines.append(f"Analysis:\n{result.analysis}\n")
                report_lines.append(f"Botanical terms found: {', '.join(result.botanical_terms_found) if result.botanical_terms_found else 'None'}")
                report_lines.append(f"Processing time: {result.processing_time:.3f}s")
                report_lines.append(f"Estimated cost: ${result.cost_estimate:.4f}")
            else:
                report_lines.append(f"ERROR: {result.error}")
        
        report_lines.append("\n" + "=" * 80)
        
        return "\n".join(report_lines)


# Test function
def test_multi_ai_comparison():
    """Test all AI providers on a sample orchid image"""
    analyzer = MultiAIVisionAnalyzer()
    
    # Use a sample GBIF image from database
    test_prompt = """Analyze this orchid specimen. Identify:
    1. Genus and species if possible
    2. Key botanical features (flower parts, leaf structure)
    3. Growth habit (epiphyte, terrestrial, etc.)
    4. Any visible anatomical structures using proper botanical terminology"""
    
    # Find a test image
    from app import app, db
    from models import OrchidImage
    
    with app.app_context():
        test_image = db.session.query(OrchidImage).filter(
            OrchidImage.local_path.isnot(None)
        ).first()
        
        if test_image and os.path.exists(test_image.local_path):
            logger.info(f"Testing with image: {test_image.scientific_name}")
            results = analyzer.compare_all_providers(test_image.local_path, test_prompt)
            report = analyzer.generate_comparison_report(results)
            
            print(report)
            
            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"ai_comparison_report_{timestamp}.txt"
            with open(report_path, "w") as f:
                f.write(report)
            
            logger.info(f"Report saved to: {report_path}")
            
            return results
        else:
            logger.error("No test images found in database")
            return None


if __name__ == "__main__":
    test_multi_ai_comparison()
