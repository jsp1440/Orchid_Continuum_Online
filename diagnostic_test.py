#!/usr/bin/env python3
"""
Diagnostic script to test why download APIs are failing
Shows actual API responses and errors
"""
import requests
import json

print("=" * 80)
print("ORCHID DOWNLOAD API DIAGNOSTICS")
print("=" * 80)

# Test 1: Wikimedia Commons
print("\n1. TESTING WIKIMEDIA COMMONS API")
print("-" * 80)
headers = {'User-Agent': 'OrchidContinuum/1.0 (research project; contact@orchidcontinuum.org)'}
params = {
    'action': 'query',
    'format': 'json',
    'list': 'search',
    'srsearch': 'Orchidaceae',
    'srnamespace': '6',
    'srlimit': 5
}

try:
    response = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)} bytes")
    
    if response.status_code == 200:
        data = response.json()
        results = data.get('query', {}).get('search', [])
        print(f"✅ Found {len(results)} results")
        if results:
            print(f"First result: {results[0].get('title', 'No title')}")
    else:
        print(f"❌ Error: {response.text[:500]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: ALA Australia
print("\n2. TESTING ALA AUSTRALIA API")
print("-" * 80)
params = {
    'q': 'family:Orchidaceae',
    'fq': 'multimedia:Image',
    'pageSize': 5,
    'startIndex': 0
}

try:
    response = requests.get("https://biocache-ws.ala.org.au/ws/occurrences/search", params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)} bytes")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total Records: {data.get('totalRecords', 0)}")
        occurrences = data.get('occurrences', [])
        print(f"✅ Fetched {len(occurrences)} occurrences")
        
        if occurrences:
            first = occurrences[0]
            print(f"First species: {first.get('scientificName', 'Unknown')}")
            print(f"Has 'image' field: {'image' in first}")
            print(f"Has 'multimedia' field: {'multimedia' in first}")
            
            if 'multimedia' in first and first['multimedia']:
                print(f"Multimedia count: {len(first['multimedia'])}")
                print(f"First multimedia identifier: {first['multimedia'][0].get('identifier', 'None')}")
    else:
        print(f"❌ Error: {response.text[:500]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: EOL API
print("\n3. TESTING EOL API")
print("-" * 80)
try:
    response = requests.get("https://eol.org/api/pages/1.0/100000.json", params={'images_per_page': 5}, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)} bytes")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Scientific Name: {data.get('scientificName', 'None')}")
        print(f"Data Objects: {len(data.get('dataObjects', []))}")
        
        images = [obj for obj in data.get('dataObjects', []) if obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage']
        print(f"✅ Images found: {len(images)}")
        
        if images:
            first_img = images[0]
            print(f"Has 'eolMediaURL': {'eolMediaURL' in first_img}")
            print(f"Has 'mediaURL': {'mediaURL' in first_img}")
            print(f"URL: {first_img.get('eolMediaURL') or first_img.get('mediaURL', 'None')}")
    else:
        print(f"❌ Error: {response.text[:500]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 4: GBIF API
print("\n4. TESTING GBIF API")
print("-" * 80)
params = {
    'familyKey': 7689,  # Orchidaceae
    'mediaType': 'StillImage',
    'limit': 5
}

try:
    response = requests.get("https://api.gbif.org/v1/occurrence/search", params=params, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)} bytes")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total Count: {data.get('count', 0):,}")
        results = data.get('results', [])
        print(f"✅ Fetched {len(results)} results")
        
        if results:
            first = results[0]
            print(f"Species: {first.get('species', 'Unknown')}")
            print(f"Has media: {'media' in first}")
            if 'media' in first and first['media']:
                print(f"Media count: {len(first['media'])}")
                print(f"First media identifier: {first['media'][0].get('identifier', 'None')}")
    else:
        print(f"❌ Error: {response.text[:500]}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTICS COMPLETE")
print("=" * 80)
