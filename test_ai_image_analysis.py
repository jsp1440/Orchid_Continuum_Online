#!/usr/bin/env python3
"""
Test AI Image Analysis on 10 Orchids
Demonstrates metadata extraction capabilities
"""
import os
import sys
import json
import logging
import requests
import tempfile
from datetime import datetime
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import OrchidRecord
from ai_orchid_identification import AIOrchidIdentifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_image(url: str) -> str:
    """Download image from URL and convert to proper format"""
    try:
        from PIL import Image
        import io
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Open image with PIL to detect format
        img = Image.open(io.BytesIO(response.content))
        
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Save as JPEG to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        img.convert('RGB').save(temp_file.name, 'JPEG', quality=95)
        temp_file.close()
        
        logger.info(f"✅ Downloaded and converted image: {img.format} -> JPEG")
        return temp_file.name
    except Exception as e:
        logger.error(f"❌ Failed to download/convert image: {e}")
        return None

def extract_exif_metadata(image_path: str) -> dict:
    """Extract EXIF metadata from image including GPS and timestamp"""
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        
        img = Image.open(image_path)
        exif_data = img._getexif()
        
        if not exif_data:
            return {
                'has_exif': False,
                'timestamp': None,
                'gps_latitude': None,
                'gps_longitude': None,
                'location': None,
                'camera_model': None,
                'note': 'No EXIF data found in image'
            }
        
        # Extract readable EXIF tags
        exif = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value
        
        # Extract GPS coordinates
        gps_latitude = None
        gps_longitude = None
        location_string = None
        
        if 'GPSInfo' in exif:
            gps_info = {}
            for key in exif['GPSInfo'].keys():
                decode = GPSTAGS.get(key, key)
                gps_info[decode] = exif['GPSInfo'][key]
            
            # Convert GPS coordinates to decimal degrees
            if 'GPSLatitude' in gps_info and 'GPSLongitude' in gps_info:
                lat = gps_info['GPSLatitude']
                lon = gps_info['GPSLongitude']
                lat_ref = gps_info.get('GPSLatitudeRef', 'N')
                lon_ref = gps_info.get('GPSLongitudeRef', 'E')
                
                # Convert to decimal degrees
                gps_latitude = lat[0] + lat[1]/60 + lat[2]/3600
                if lat_ref == 'S':
                    gps_latitude = -gps_latitude
                
                gps_longitude = lon[0] + lon[1]/60 + lon[2]/3600
                if lon_ref == 'W':
                    gps_longitude = -gps_longitude
                
                location_string = f"{gps_latitude:.6f}, {gps_longitude:.6f}"
        
        # Extract timestamp
        timestamp = exif.get('DateTime') or exif.get('DateTimeOriginal') or exif.get('DateTimeDigitized')
        
        # Extract camera info
        camera_model = exif.get('Model', 'Unknown')
        camera_make = exif.get('Make', '')
        if camera_make:
            camera_model = f"{camera_make} {camera_model}"
        
        return {
            'has_exif': True,
            'timestamp': timestamp,
            'gps_latitude': gps_latitude,
            'gps_longitude': gps_longitude,
            'location': location_string,
            'camera_model': camera_model,
            'image_width': exif.get('ExifImageWidth'),
            'image_height': exif.get('ExifImageHeight'),
            'iso': exif.get('ISOSpeedRatings'),
            'focal_length': exif.get('FocalLength'),
            'exposure_time': exif.get('ExposureTime')
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Could not extract EXIF data: {e}")
        return {
            'has_exif': False,
            'timestamp': None,
            'gps_latitude': None,
            'gps_longitude': None,
            'location': None,
            'camera_model': None,
            'error': str(e)
        }

def analyze_orchid_batch():
    """Analyze 10 orchids with images and extract metadata"""
    
    with app.app_context():
        # Get 10 orchids with images for testing
        orchids = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.image_url != ''
        ).limit(10).all()
        
        logger.info(f"🔬 Found {len(orchids)} orchids to analyze")
        
        # Initialize AI analyzer
        identifier = AIOrchidIdentifier()
        
        if not identifier.client:
            logger.error("❌ OpenAI API key not configured")
            return
        
        results = []
        
        for idx, orchid in enumerate(orchids, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🌺 Analyzing {idx}/{len(orchids)}: {orchid.genus} {orchid.species}")
            logger.info(f"📸 Image: {orchid.image_url[:80]}...")
            
            try:
                # Download image to temp file
                temp_image = download_image(orchid.image_url)
                if not temp_image:
                    logger.warning(f"⚠️ Failed to download image, skipping")
                    continue
                
                # Extract EXIF metadata (GPS, timestamp, camera info)
                exif_metadata = extract_exif_metadata(temp_image)
                
                if exif_metadata.get('timestamp'):
                    logger.info(f"📅 Photo taken: {exif_metadata['timestamp']}")
                if exif_metadata.get('location'):
                    logger.info(f"📍 GPS Location: {exif_metadata['location']}")
                
                # Analyze the orchid image
                analysis = identifier.identify_orchid_from_image(temp_image)
                
                # Clean up temp file
                os.unlink(temp_image)
                
                if analysis and 'error' not in analysis:
                    # Extract AI metadata with source citations
                    ai_data = analysis.get('ai_identification', {})
                    metadata_ext = ai_data.get('metadata_extraction', {})
                    cultural = ai_data.get('cultural_requirements', {})
                    habitat = ai_data.get('habitat_indicators', {})
                    
                    # Helper to extract value and source
                    def get_cited_value(item, default='Unknown'):
                        if isinstance(item, dict):
                            return item.get('value', default)
                        return item or default
                    
                    def get_source(item):
                        if isinstance(item, dict):
                            return item.get('source', 'Not specified')
                        return 'Not specified'
                    
                    # Extract key metadata with citations
                    metadata = {
                        'orchid_id': orchid.id,
                        'current_name': f"{orchid.genus} {orchid.species}",
                        'image_url': orchid.image_url,
                        'ai_analysis': {
                            'growth_habit': {
                                'value': get_cited_value(metadata_ext.get('growth_habit')),
                                'source': get_source(metadata_ext.get('growth_habit'))
                            },
                            'temperature': {
                                'value': get_cited_value(metadata_ext.get('temperature')),
                                'source': get_source(metadata_ext.get('temperature'))
                            },
                            'light': {
                                'value': get_cited_value(metadata_ext.get('light')),
                                'source': get_source(metadata_ext.get('light'))
                            },
                            'humidity': {
                                'value': get_cited_value(metadata_ext.get('humidity')),
                                'source': get_source(metadata_ext.get('humidity'))
                            },
                            'bloom_season': {
                                'value': get_cited_value(metadata_ext.get('bloom_season')),
                                'source': get_source(metadata_ext.get('bloom_season'))
                            },
                            'difficulty': {
                                'value': get_cited_value(metadata_ext.get('difficulty')),
                                'source': get_source(metadata_ext.get('difficulty'))
                            }
                        },
                        'cultural_requirements': {
                            'watering': {
                                'value': get_cited_value(cultural.get('watering')),
                                'source': get_source(cultural.get('watering'))
                            },
                            'fertilizer': {
                                'value': get_cited_value(cultural.get('fertilizer')),
                                'source': get_source(cultural.get('fertilizer'))
                            },
                            'potting_medium': {
                                'value': get_cited_value(cultural.get('potting_medium')),
                                'source': get_source(cultural.get('potting_medium'))
                            }
                        },
                        'habitat_indicators': {
                            'native_climate': {
                                'value': get_cited_value(habitat.get('native_climate')),
                                'source': get_source(habitat.get('native_climate'))
                            },
                            'elevation': {
                                'value': get_cited_value(habitat.get('elevation_preference')),
                                'source': get_source(habitat.get('elevation_preference'))
                            }
                        },
                        'confidence_score': ai_data.get('confidence_score', 0),
                        'analysis_limitations': ai_data.get('analysis_limitations', 'None'),
                        'photo_quality': ai_data.get('photo_quality_notes', 'Not assessed'),
                        'exif_metadata': exif_metadata
                    }
                    
                    results.append(metadata)
                    
                    # Log summary with sources
                    logger.info(f"✅ Metadata extracted:")
                    logger.info(f"   Growth habit: {metadata['ai_analysis']['growth_habit']['value']}")
                    logger.info(f"     Source: {metadata['ai_analysis']['growth_habit']['source'][:60]}...")
                    logger.info(f"   Temperature: {metadata['ai_analysis']['temperature']['value']}")
                    logger.info(f"     Source: {metadata['ai_analysis']['temperature']['source'][:60]}...")
                    logger.info(f"   Bloom season: {metadata['ai_analysis']['bloom_season']['value']}")
                    logger.info(f"   Confidence: {metadata['confidence_score']}%")
                    
                else:
                    logger.warning(f"⚠️ Analysis failed or returned error")
                    
            except Exception as e:
                logger.error(f"❌ Error analyzing orchid: {str(e)}")
        
        # Save results
        output_file = f"ai_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 ANALYSIS COMPLETE")
        logger.info(f"📁 Results saved to: {output_file}")
        logger.info(f"🌺 Successfully analyzed {len(results)}/{len(orchids)} orchids")
        
        # Print summary statistics
        if results:
            avg_confidence = sum(r['confidence_score'] for r in results) / len(results)
            logger.info(f"📈 Average confidence: {avg_confidence:.1f}%")
            
            # Count what metadata was extracted
            has_bloom_season = sum(1 for r in results if r['ai_analysis']['bloom_season']['value'] != 'Unknown')
            has_temp = sum(1 for r in results if r['ai_analysis']['temperature']['value'] != 'Unknown')
            has_growth = sum(1 for r in results if r['ai_analysis']['growth_habit']['value'] != 'Unknown')
            has_difficulty = sum(1 for r in results if r['ai_analysis']['difficulty']['value'] != 'Unknown')
            total = len(results)
            
            logger.info(f"📊 Metadata extraction success:")
            logger.info(f"   Bloom season: {has_bloom_season}/{total} ({int(has_bloom_season/total*100) if total > 0 else 0}%)")
            logger.info(f"   Temperature: {has_temp}/{total} ({int(has_temp/total*100) if total > 0 else 0}%)")
            logger.info(f"   Growth habit: {has_growth}/{total} ({int(has_growth/total*100) if total > 0 else 0}%)")
            logger.info(f"   Difficulty: {has_difficulty}/{total} ({int(has_difficulty/total*100) if total > 0 else 0}%)")
            
            # Show cost estimate
            cost_per_image = 0.003  # GPT-4o-mini price
            total_cost = len(results) * cost_per_image
            logger.info(f"💰 Estimated cost: ${total_cost:.2f} ({len(results)} images × ${cost_per_image})")
            
            # EXIF metadata statistics
            has_exif = sum(1 for r in results if r.get('exif_metadata', {}).get('has_exif'))
            has_gps = sum(1 for r in results if r.get('exif_metadata', {}).get('gps_latitude'))
            has_timestamp = sum(1 for r in results if r.get('exif_metadata', {}).get('timestamp'))
            
            logger.info(f"\n📸 EXIF Metadata Coverage:")
            logger.info(f"   Photos with EXIF data: {has_exif}/{total} ({int(has_exif/total*100) if total > 0 else 0}%)")
            logger.info(f"   GPS coordinates: {has_gps}/{total} ({int(has_gps/total*100) if total > 0 else 0}%)")
            logger.info(f"   Timestamps: {has_timestamp}/{total} ({int(has_timestamp/total*100) if total > 0 else 0}%)")
            
            if has_gps > 0:
                logger.info(f"\n🗺️ Geographic data available for bloom pattern tracking!")
            if has_timestamp > 0:
                logger.info(f"📅 Temporal data available for seasonal analysis!")

if __name__ == "__main__":
    analyze_orchid_batch()
