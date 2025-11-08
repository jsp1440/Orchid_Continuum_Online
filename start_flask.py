#!/usr/bin/env python
"""
Simple Flask server startup script
Resolves naming conflict between app.py and app/ directory
"""
import sys
import os

# Ensure we're in the right directory
os.chdir('/home/runner/workspace')

# Import Flask app directly from app.py file
import importlib.util
spec = importlib.util.spec_from_file_location("flask_app", "/home/runner/workspace/app.py")
flask_app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flask_app_module)

# Get the Flask app instance
application = flask_app_module.app

if __name__ == '__main__':
    print("🌸 Starting ORCHID Continuum Flask Server...")
    print(f"📍 Server will be available at: http://0.0.0.0:5000")
    application.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
