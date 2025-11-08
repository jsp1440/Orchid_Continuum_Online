"""
Download herbarium specimens from Tropicos (Missouri Botanical Garden)
Target: 5,000 high-quality herbarium sheets with collector data
"""
import os
import requests
import psycopg2
import time
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATABASE_URL = os.environ.get('DATABASE_URL')
os.makedirs('attached_assets/tropicos_herbarium', exist_ok=True)

print("🔬 TROPICOS HERBARIUM DOWNLOAD")
print("=" * 60)

# Tropicos API endpoint
base_url = "http://services.tropicos.org/Image/Search"
api_key = "your-free-api-key"  # Tropicos allows anonymous access

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Get list of orchid genera to search
cursor.execute("""
    SELECT DISTINCT genus 
    FROM orchid_taxonomy 
    WHERE genus IS NOT NULL 
    ORDER BY genus 
    LIMIT 100
""")
genera = [row[0] for row in cursor.fetchall()]

downloaded = 0
failed = 0
target = 5000

print(f"📚 Searching {len(genera)} orchid genera...")
print(f"🎯 Target: {target:,} specimens\n")

for genus in genera:
    if downloaded >= target:
        break
        
    try:
        # Search Tropicos for genus images
        params = {
            "name": genus,
            "format": "json"
        }
        
        response = requests.get(base_url, params=params, timeout=30, verify=False)
        if response.status_code == 200:
            images = response.json()
            
            for img in images[:50]:  # Max 50 per genus
                if downloaded >= target:
                    break
                    
                try:
                    image_url = img.get('ImageURL', '')
                    if not image_url:
                        continue
                    
                    # Download image
                    img_response = requests.get(image_url, timeout=15, verify=False)
                    if img_response.status_code == 200:
                        filename = f"tropicos_{downloaded}_{genus}.jpg"
                        local_path = f"attached_assets/tropicos_herbarium/{filename}"
                        
                        with open(local_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        # Check if already exists
                        cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (image_url,))
                        if cursor.fetchone()[0] > 0:
                            continue
                        
                        # Insert to database
                        cursor.execute("""
                            INSERT INTO orchid_images (
                                image_url, local_path, image_source, image_type,
                                image_license, herbarium_catalog_number,
                                image_description
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            image_url,
                            local_path,
                            'Tropicos - Missouri Botanical Garden',
                            'herbarium_sheet',
                            'CC BY-NC-SA',
                            img.get('SpecimenId', ''),
                            f"{genus} - Herbarium specimen from Missouri Botanical Garden"
                        ))
                        
                        if cursor.rowcount > 0:
                            conn.commit()
                            downloaded += 1
                            
                            if downloaded % 25 == 0:
                                print(f"  [{downloaded:,}/{target:,}] ✅ {genus}")
                                
                except Exception as e:
                    failed += 1
                    continue
                    
        time.sleep(0.5)
        
    except Exception as e:
        print(f"  ❌ Error with genus {genus}: {e}")
        time.sleep(2)
        continue

cursor.close()
conn.close()

print(f"\n✅ Tropicos download complete: {downloaded:,} specimens")
