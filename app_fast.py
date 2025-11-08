"""
Fast-loading Flask app for The Orchid Continuum.
Defers heavy initialization until first request.
"""
import os
import logging
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["https://*.neoncrm.com", "http://localhost:*"])

# Configure secrets
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Apply ProxyFix middleware
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = os.environ.get("DATABASE_URL", "")
if database_url:
    if 'postgresql://' in database_url and 'postgresql+pg8000://' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    database_url = database_url.replace('?sslmode=require', '').replace('&sslmode=require', '')

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension  
db.init_app(app)

# Track if we've initialized
_initialized = False

def lazy_init():
    """Initialize heavy components on first request."""
    global _initialized
    if _initialized:
        return
    
    logging.info("🌺 Lazy loading components...")
    
    with app.app_context():
        try:
            import models
            import parentage_models
            db.create_all()
            logging.info("✅ Database initialized")
        except Exception as e:
            logging.error(f"Database init error: {e}")
        
        # Register critical blueprints only
        try:
            from bloombuilder_routes import bloombuilder_bp
            app.register_blueprint(bloombuilder_bp)
            logging.info("✅ BloomBuilder loaded")
        except Exception as e:
            logging.error(f"BloomBuilder error: {e}")
        
        try:
            from routes_julius_monitor import julius_monitor_bp
            app.register_blueprint(julius_monitor_bp)
            logging.info("✅ Julius Monitor loaded")
        except Exception as e:
            logging.error(f"Julius Monitor error: {e}")
    
    _initialized = True
    logging.info("✅ Initialization complete")

# Health check endpoint (no initialization required)
@app.route('/health')
@app.route('/healthz')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "orchid-continuum",
        "initialized": _initialized
    }), 200

# BloomBuilder widget
@app.route('/widget')
@app.route('/bloombuilder')
def widget():
    lazy_init()
    return """
    <html>
    <head><title>BloomBuilder Widget</title></head>
    <body>
        <h1>🌺 BloomBuilder - The Orchid Continuum</h1>
        <p>Widget loading... Please visit <a href="/bloombuilder/api/species">/bloombuilder/api/species</a></p>
    </body>
    </html>
    """

# Julius Monitor
@app.route('/julius/status')
def julius_status():
    lazy_init()
    try:
        return jsonify({
            "status": "active",
            "message": "Julius Monitor ready"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🌸 Starting Fast Orchid Continuum Server...")
    app.run(host='0.0.0.0', port=5000, debug=False)
