#!/usr/bin/env python3
"""
Test all harvester APIs with known orchid species
Diagnose exactly why each source isn't returning images
"""
import os
import requests
import json

# Test species known to have images
TEST_SPECIES = [
    "Dendrobium speciosum",    # Common Australian orchid
    "Cattleya labiata",        # Famous orchid
    "Phalaenopsis amabilis",   # Moth orchid
    "Vanilla planifolia",      # Vanilla orchid
]

TROPICOS_KEY = os.environ.get('TROPICOS_API_KEY', '')
BHL_KEY = os.environ.get('BHL_API_KEY', '')

def test_idigbio(name):
    """Test iDigBio API"""
    print(f"\n{'='*70}")
    print(f"🏛️  TESTING iDIGBIO: {name}")
    print('='*70)
    
    try:
        search_url = "https://search.idigbio.org/v2/search/records"
        query = {
            'rq': {
                'scientificname': name,
                'hasImage': True
            },
            'limit': 5
        }
        
        resp = requests.post(search_url, json=query, headers={'Content-Type': 'application/json'}, timeout=20)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('items', [])
            print(f"✅ Found {len(items)} records with images")
            
            if items:
                item = items[0]
                uuid = item.get('uuid')
                print(f"   First UUID: {uuid}")
                
                # Try to get image
                media_url = f"https://search.idigbio.org/v2/view/records/{uuid}"
                media_resp = requests.get(media_url, timeout=10)
                
                if media_resp.status_code == 200:
                    media_data = media_resp.json()
                    
                    # Check multiple possible locations for image URL
                    img_url = None
                    if media_data.get('data', {}).get('ac:accessURI'):
                        img_url = media_data['data']['ac:accessURI']
                        print(f"   Found image in data.ac:accessURI: {img_url[:80]}")
                    elif media_data.get('mediarecords'):
                        for media in media_data['mediarecords']:
                            if media.get('accessuri'):
                                img_url = media['accessuri']
                                print(f"   Found image in mediarecords: {img_url[:80]}")
                                break
                    
                    if not img_url:
                        print("   ⚠️ No image URL found in media record!")
                        print(f"   Media data keys: {list(media_data.keys())}")
                else:
                    print(f"   ❌ Media fetch failed: {media_resp.status_code}")
            else:
                print("   ⚠️ No records found")
        else:
            print(f"❌ API error: {resp.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_tropicos(name):
    """Test Tropicos API"""
    print(f"\n{'='*70}")
    print(f"🌿 TESTING TROPICOS: {name}")
    print('='*70)
    
    if not TROPICOS_KEY:
        print("⚠️ TROPICOS_API_KEY not set!")
        return
    
    try:
        # Step 1: Search for name
        search_url = "http://services.tropicos.org/Name/Search"
        params = {'apikey': TROPICOS_KEY, 'name': name, 'type': 'wildcard', 'format': 'json'}
        resp = requests.get(search_url, params=params, timeout=15)
        print(f"Search status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                name_id = data[0].get('NameId')
                print(f"✅ Found NameId: {name_id}")
                
                # Step 2: Get images for this name
                images_url = f"http://services.tropicos.org/Name/{name_id}/Images"
                params = {'apikey': TROPICOS_KEY, 'format': 'json', 'pagesize': 5}
                resp = requests.get(images_url, params=params, timeout=15)
                print(f"Images status: {resp.status_code}")
                
                if resp.status_code == 200:
                    images_data = resp.json()
                    if isinstance(images_data, list):
                        print(f"✅ Found {len(images_data)} images")
                        if images_data:
                            img = images_data[0]
                            print(f"   First image URL: {img.get('Url', 'NO URL')[:80]}")
                    else:
                        print(f"   ⚠️ Unexpected response type: {type(images_data)}")
                else:
                    print(f"   ❌ Images fetch failed: {resp.text[:200]}")
            else:
                print("   ⚠️ No name matches found")
        else:
            print(f"❌ Search failed: {resp.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_bhl(name):
    """Test BHL API"""
    print(f"\n{'='*70}")
    print(f"📚 TESTING BHL: {name}")
    print('='*70)
    
    if not BHL_KEY:
        print("⚠️ BHL_API_KEY not set!")
        return
    
    try:
        search_url = "https://www.biodiversitylibrary.org/api3"
        params = {'op': 'NameSearch', 'name': name, 'apikey': BHL_KEY, 'format': 'json'}
        resp = requests.get(search_url, params=params, timeout=15)
        print(f"Search status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('Result', [])
            print(f"✅ Found {len(results)} name matches")
            
            if results:
                result = results[0]
                page_id = result.get('PageID')
                print(f"   First PageID: {page_id}")
                
                if page_id:
                    # Get page metadata
                    page_params = {'op': 'GetPageMetadata', 'pageid': page_id, 'apikey': BHL_KEY, 'format': 'json'}
                    page_resp = requests.get(search_url, params=page_params, timeout=10)
                    
                    if page_resp.status_code == 200:
                        page_data = page_resp.json()
                        if page_data.get('Result'):
                            img_url = page_data['Result'][0].get('PageUrl')
                            print(f"   ✅ Page URL: {img_url[:80] if img_url else 'NO URL'}")
                        else:
                            print("   ⚠️ No page data in result")
                    else:
                        print(f"   ❌ Page fetch failed: {page_resp.status_code}")
            else:
                print("   ⚠️ No results found")
        else:
            print(f"❌ Search failed: {resp.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_eol(name):
    """Test EOL API"""
    print(f"\n{'='*70}")
    print(f"🌎 TESTING EOL: {name}")
    print('='*70)
    
    try:
        # Step 1: Search for species
        search_url = "https://eol.org/api/search/1.0.json"
        params = {'q': name, 'page': 1, 'exact': True}
        resp = requests.get(search_url, params=params, timeout=10)
        print(f"Search status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', [])
            print(f"✅ Found {len(results)} search results")
            
            if results:
                page_id = results[0].get('id')
                print(f"   First page ID: {page_id}")
                
                # Step 2: Get page data with images
                page_url = f"https://eol.org/api/pages/1.0/{page_id}.json"
                params = {'images': 5, 'videos': 0, 'details': True}
                resp = requests.get(page_url, params=params, timeout=15)
                print(f"   Page status: {resp.status_code}")
                
                if resp.status_code == 200:
                    page_data = resp.json()
                    data_objects = page_data.get('dataObjects', [])
                    
                    images = [obj for obj in data_objects if obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage']
                    print(f"   ✅ Found {len(images)} images")
                    
                    if images:
                        img = images[0]
                        print(f"   First image URL: {img.get('mediaURL', 'NO URL')[:80]}")
                else:
                    print(f"   ❌ Page fetch failed")
            else:
                print("   ⚠️ No search results")
        else:
            print(f"❌ Search failed: {resp.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

def test_ala(name):
    """Test ALA API"""
    print(f"\n{'='*70}")
    print(f"🦘 TESTING ALA (Australia): {name}")
    print('='*70)
    
    try:
        search_url = "https://biocache.ala.org.au/ws/occurrences/search"
        params = {
            'q': f'scientificName:"{name}"',
            'fq': 'multimedia:Image',
            'pageSize': 5
        }
        
        resp = requests.get(search_url, params=params, timeout=15)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            occurrences = data.get('occurrences', [])
            print(f"✅ Found {len(occurrences)} occurrences with images")
            
            if occurrences:
                occ = occurrences[0]
                img_url = occ.get('image')
                if not img_url:
                    images = occ.get('images', [])
                    if images:
                        img_url = images[0]
                
                if img_url:
                    print(f"   ✅ Image URL: {img_url[:80]}")
                else:
                    print("   ⚠️ No image URL in occurrence")
                    print(f"   Occurrence keys: {list(occ.keys())[:10]}")
            else:
                print("   ⚠️ No occurrences found")
        else:
            print(f"❌ API error: {resp.text[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

# Run tests
print("\n" + "="*70)
print("🔬 COMPREHENSIVE API DIAGNOSTIC TEST")
print("="*70)
print(f"\nTesting {len(TEST_SPECIES)} known orchid species across 5 APIs")
print(f"TROPICOS_API_KEY: {'SET ✅' if TROPICOS_KEY else 'NOT SET ❌'}")
print(f"BHL_API_KEY: {'SET ✅' if BHL_KEY else 'NOT SET ❌'}")

for species in TEST_SPECIES:
    print(f"\n\n{'#'*70}")
    print(f"# TESTING SPECIES: {species}")
    print(f"{'#'*70}")
    
    test_idigbio(species)
    test_tropicos(species)
    test_bhl(species)
    test_eol(species)
    test_ala(species)

print("\n\n" + "="*70)
print("✅ DIAGNOSTIC TEST COMPLETE")
print("="*70)
