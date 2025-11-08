import requests, csv, os, time

os.makedirs("test_images", exist_ok=True)

# Download just 3 observations to test
response = requests.get("https://api.inaturalist.org/v1/observations?taxon_id=47217&quality_grade=research&photos=true&per_page=3")
data = response.json()

# Create CSV
with open("test_data.csv", 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['obs_id', 'species', 'common_name', 'location', 'latitude', 'longitude', 
                     'date', 'quality', 'native', 'threatened', 'image_url', 'filename'])

print("\n🧪 MINI TEST DOWNLOAD (3 observations)")
print("="*60)

for obs in data['results']:
    obs_id = obs['id']
    taxon = obs.get('taxon', {})
    species = taxon.get('name', 'Unknown')
    common = taxon.get('preferred_common_name', '')
    location = obs.get('place_guess', '')
    coords = obs.get('geojson', {}).get('coordinates', [None, None])
    lat, lon = coords[1], coords[0]
    date = obs.get('observed_on', '')
    quality = obs.get('quality_grade', '')
    native = taxon.get('native', '')
    threatened = taxon.get('threatened', '')
    
    photos = obs.get('photos', [])
    
    print(f"\n📥 Downloading: {species}")
    print(f"   Common name: {common}")
    print(f"   Location: {location}")
    print(f"   Photos: {len(photos)}")
    
    for idx, photo in enumerate(photos):
        img_url = photo.get('url', '').replace('square', 'original')
        filename = f"{obs_id}_{species.replace(' ', '_')}_{idx+1}.jpg"
        
        # Download image
        img_data = requests.get(img_url, timeout=30)
        if img_data.status_code == 200:
            with open(f"test_images/{filename}", 'wb') as f:
                f.write(img_data.content)
            print(f"   ✅ Image saved: {filename}")
            
            # Save to CSV
            with open("test_data.csv", 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([obs_id, species, common, location, lat, lon, 
                               date, quality, native, threatened, img_url, filename])
        
        time.sleep(0.2)

print("\n" + "="*60)
print("✅ TEST COMPLETE!")
print("="*60)
print(f"📁 Images: test_images/")
print(f"📊 Data: test_data.csv")
print("="*60 + "\n")

# Show results
import subprocess
print("📊 CSV CONTENTS:")
subprocess.run(["cat", "test_data.csv"])
print("\n📁 DOWNLOADED IMAGES:")
subprocess.run(["ls", "-lh", "test_images/"])
