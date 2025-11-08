import sys
sys.path.insert(0, '/home/runner/workspace')

# Import the Flask app from app.py
import app as app_module
flask_app = app_module.app

if __name__ == '__main__':
    print("🌸 Starting ORCHID Continuum...")
    flask_app.run(host='0.0.0.0', port=5000, debug=False)
