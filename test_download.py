import requests
import json

# Test 1: Check if API is accessible
print("\n🔍 TEST 1: Checking iNaturalist API...")
response = requests.get("https://api.inaturalist.org/v1/observations?taxon_id=47217&quality_grade=research&photos=true&per_page=1")

if response.status_code == 200:
    data = response.json()
    total = data.get('total_results', 0)
    print(f"✅ API Working! Found {total:,} total orchid observations available")
    
    if data.get('results'):
        obs = data['results'][0]
        taxon = obs.get('taxon', {})
        print(f"✅ Sample species: {taxon.get('name', 'Unknown')}")
        print(f"✅ Photos available: {len(obs.get('photos', []))}")
        
        # Show available fields
        print(f"\n📊 Available data fields in observation:")
        print(f"   - observation_id: {obs.get('id')}")
        print(f"   - species: {taxon.get('name')}")
        print(f"   - common_name: {taxon.get('preferred_common_name')}")
        print(f"   - location: {obs.get('place_guess')}")
        print(f"   - coordinates: {obs.get('geojson', {}).get('coordinates')}")
        print(f"   - observed_on: {obs.get('observed_on')}")
        print(f"   - quality_grade: {obs.get('quality_grade')}")
        print(f"   - native: {taxon.get('native')}")
        print(f"   - threatened: {taxon.get('threatened')}")
        print(f"   - wikipedia: {taxon.get('wikipedia_url')}")
        
        # Count total available fields
        all_keys = set()
        all_keys.update(obs.keys())
        all_keys.update(taxon.keys())
        print(f"\n✅ Total unique data fields available: {len(all_keys)}")
        
else:
    print(f"❌ API Error: {response.status_code}")
    
print("\n" + "="*70)
