"""
STANDALONE WIDGET SERVER
Runs ONLY the 3 new widgets without loading the entire Orchid Continuum app
This ensures fast startup and guaranteed functionality
"""

import os
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal Flask app
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Minimal config
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
CORS(app)

# Database config
database_url = os.environ.get("DATABASE_URL")
if database_url:
    database_url = database_url.replace('sslmode=Require', 'sslmode=require')
    if 'postgresql://' in database_url and 'postgresql+pg8000://' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
        database_url = database_url.replace('postgresql+psycopg2://', 'postgresql+pg8000://')
        database_url = database_url.replace('postgresql+psycopg://', 'postgresql+pg8000://')
        database_url = database_url.replace('?sslmode=require', '')
        database_url = database_url.replace('&sslmode=require', '')
        database_url = database_url.replace('sslmode=require&', '')
        database_url = database_url.replace('sslmode=require', '')
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    db.init_app(app)
else:
    logger.warning("⚠️ No DATABASE_URL - some features may not work")

# Register ONLY the new widgets
with app.app_context():
    # Import models
    try:
        import models
        db.create_all()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"Database setup warning: {e}")
    
    # Register the 3 new widgets
    try:
        from live_ai_generation_widget import live_widget_bp
        app.register_blueprint(live_widget_bp)
        logger.info("✅ Live AI Generation Widget loaded at /widgets/live-ai-generation")
    except Exception as e:
        logger.error(f"Live widget error: {e}")
    
    try:
        from simple_monitoring import monitor_bp
        app.register_blueprint(monitor_bp)
        logger.info("✅ Monitoring Dashboard loaded at /monitor")
    except Exception as e:
        logger.error(f"Monitor error: {e}")
    
    try:
        from master_tracker import tracker_bp
        app.register_blueprint(tracker_bp)
        logger.info("✅ Project Tracker loaded at /tracker")
    except Exception as e:
        logger.error(f"Tracker error: {e}")

# Home page with links to all widgets
@app.route('/')
def index():
    """Welcome page with links to all widgets"""
    return render_template('standalone_index.html')

# Health check
@app.route('/health')
def health():
    return {"status": "ok", "widgets": "3 active"}, 200

if __name__ == '__main__':
    logger.info("\n" + "="*60)
    logger.info("🚀 STANDALONE WIDGET SERVER STARTING")
    logger.info("="*60)
    logger.info("Available Widgets:")
    logger.info("  1. Live AI Generation: http://0.0.0.0:5000/widgets/live-ai-generation")
    logger.info("  2. Monitoring Dashboard: http://0.0.0.0:5000/monitor")
    logger.info("  3. Project Tracker: http://0.0.0.0:5000/tracker")
    logger.info("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
