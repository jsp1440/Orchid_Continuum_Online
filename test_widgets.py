#!/usr/bin/env python
"""
Widget Testing Script
Run this after starting the Flask server to test widgets
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_widget(name, url):
    """Test if a widget endpoint is accessible"""
    try:
        response = requests.get(f"{BASE_URL}{url}", timeout=5)
        status = "✅" if response.status_code == 200 else f"❌ ({response.status_code})"
        return f"{status} {name}: {url}"
    except Exception as e:
        return f"❌ {name}: {url} - Error: {str(e)[:50]}"

print("🌺 The Orchid Continuum - Widget Testing")
print("=" * 60)
print()

# Test server health
print("Testing server health...")
print(test_widget("Health Check", "/health"))
print(test_widget("Homepage", "/"))
print()

# Test main widgets
print("Testing Widgets...")
print(test_widget("BloomBuilder", "/bloombuilder"))
print(test_widget("Culture Sheets - Demo", "/culture/demo"))
print(test_widget("Culture Sheets - Species List", "/culture/species"))
print(test_widget("Widget Directory", "/widgets"))
print(test_widget("Gallery", "/gallery"))
print()

# Test culture sheet API
print("Testing Culture Sheet API...")
try:
    response = requests.post(
        f"{BASE_URL}/culture/generate",
        json={"species": "Phalaenopsis", "location": {"city": "San Francisco, CA", "latitude": 37.7749, "longitude": -122.4194}},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Culture Sheet Generation - Working!")
            print(f"   Data sources: {', '.join(data.get('culture_sheet', {}).get('data_sources', []))}")
        else:
            print(f"❌ Culture Sheet Generation - {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ Culture Sheet Generation - HTTP {response.status_code}")
except Exception as e:
    print(f"❌ Culture Sheet Generation - Error: {str(e)[:100]}")

print()
print("=" * 60)
print("Testing complete!")
