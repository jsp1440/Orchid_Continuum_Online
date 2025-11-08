#!/usr/bin/env python
"""
Full Flask App Startup - Includes ALL widgets and features
This loads the complete app.py with all routes including:
- BloomBuilder
- Culture Sheets (AOS/Baker integration)
- All other widgets
"""
import os
import sys

# Add bloombuilder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bloombuilder_standalone'))

# Import the FULL app (not minimal)
from app import app
import routes  # This loads ALL routes including culture sheets

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*70)
    print("🌺 The Orchid Continuum - FULL APPLICATION")
    print("="*70)
    print(f"Server: http://0.0.0.0:{port}")
    print(f"")
    print("🎨 WIDGETS TO TEST:")
    print(f"  - BloomBuilder: http://0.0.0.0:{port}/bloombuilder")
    print(f"  - Culture Sheets Demo: http://0.0.0.0:{port}/culture/demo")
    print(f"  - Culture Sheet Generator: http://0.0.0.0:{port}/culture/generate (POST)")
    print(f"  - Widget Directory: http://0.0.0.0:{port}/widgets")
    print(f"  - Gallery: http://0.0.0.0:{port}/gallery")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
