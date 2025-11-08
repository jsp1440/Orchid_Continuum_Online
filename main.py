import os
import sys

# Add bloombuilder_standalone to Python path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bloombuilder_standalone'))

# PRODUCTION FIX: Use minimal fast-loading server instead of heavy app.py
# The original app.py has 43 blueprints loading during import, causing timeouts
from server_minimal import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("🌺 BloomBuilder - The Orchid Continuum")
    print("="*60)
    print(f"Server will be available at: http://0.0.0.0:{port}")
    print(f"BloomBuilder: http://0.0.0.0:{port}/bloombuilder")
    print(f"Julius Monitor: http://0.0.0.0:{port}/julius/status")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)