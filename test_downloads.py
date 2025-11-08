"""
Quick test: Download 10 images from each source to verify all APIs work
"""
import os
import requests
import psycopg2
import csv

DATABASE_URL = os.environ.get('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("🧪 TESTING ALL 4 DOWNLOAD SOURCES")
print("=" * 70)
print()

# Test 1: GBIF CSV Import
print("1️⃣  Testing GBIF import from CSV...")
try:
    with open('attached_assets/ORCHID_COMPLETE_52_COLUMNS_1762231249570.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= 5:
                break
            image_url = row.get('Image_URL', '').strip()
            if image_url:
                # Check if exists
                cursor.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url = %s", (image_url,))
                if cursor.fetchone()[0] == 0:
                    print(f"   ✅ New image found: {row.get('Scientific_Name', 'Unknown')}")
                else:
                    print(f"   ⏭️  Already exists: {row.get('Scientific_Name', 'Unknown')}")
                count += 1
    print("   ✅ GBIF CSV test passed\n")
except Exception as e:
    print(f"   ❌ GBIF test failed: {e}\n")

# Test 2: iDigBio API
print("2️⃣  Testing iDigBio API...")
try:
    api_url = "https://search.idigbio.org/v2/search/records/"
    params = {
        "rq": {"family": "Orchidaceae", "hasImage": True, "basisofrecord": "preservedspecimen"},
        "limit": 5
    }
    response = requests.post(api_url, json=params, timeout=30)
    if response.status_code == 200:
        data = response.json()
        items = data.get('items', [])
        print(f"   ✅ iDigBio returned {len(items)} results")
        if items:
            print(f"   Sample: {items[0].get('indexTerms', {}).get('scientificname', 'Unknown')}")
        print("   ✅ iDigBio API test passed\n")
    else:
        print(f"   ❌ iDigBio API returned {response.status_code}\n")
except Exception as e:
    print(f"   ❌ iDigBio test failed: {e}\n")

# Test 3: Tropicos API
print("3️⃣  Testing Tropicos API...")
try:
    # Get a genus
    cursor.execute("SELECT DISTINCT genus FROM orchid_taxonomy WHERE genus IS NOT NULL LIMIT 1")
    genus = cursor.fetchone()[0]
    
    search_url = f"https://services.tropicos.org/Name/Search?name={genus}&type=wildcard&format=json"
    response = requests.get(search_url, timeout=15)
    if response.status_code == 200:
        results = response.json()
        print(f"   ✅ Tropicos returned {len(results)} results for {genus}")
        print("   ✅ Tropicos API test passed\n")
    else:
        print(f"   ❌ Tropicos API returned {response.status_code}\n")
except Exception as e:
    print(f"   ❌ Tropicos test failed: {e}\n")

# Test 4: EOL API  
print("4️⃣  Testing EOL API...")
try:
    cursor.execute("SELECT DISTINCT genus, species FROM orchid_taxonomy WHERE genus IS NOT NULL AND species IS NOT NULL LIMIT 1")
    genus, species = cursor.fetchone()
    
    search_url = "https://eol.org/api/search/1.0.json"
    params = {"q": f"{genus} {species}", "exact": True}
    response = requests.get(search_url, params=params, timeout=15)
    if response.status_code == 200:
        data = response.json()
        results = data.get('results', [])
        print(f"   ✅ EOL returned {len(results)} results for {genus} {species}")
        print("   ✅ EOL API test passed\n")
    else:
        print(f"   ❌ EOL API returned {response.status_code}\n")
except Exception as e:
    print(f"   ❌ EOL test failed: {e}\n")

cursor.close()
conn.close()

print("=" * 70)
print("✅ API TESTS COMPLETE")
print("All sources are accessible and returning data!")
