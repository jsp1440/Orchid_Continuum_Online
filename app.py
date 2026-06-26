import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from whitenoise import WhiteNoise

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)

# Configure CORS for Neon One widget embedding
CORS(app, 
     origins=[
         "https://*.neoncrm.com",
         "https://*.app.neoncrm.com", 
         "https://fivecitiesorchidsociety.app.neoncrm.com",
         "http://localhost:*",  # For testing
         "https://localhost:*"  # For testing
     ],
     supports_credentials=False,  # Avoid cookies in widgets
     resources={
         r"/widgets/*": {"origins": [
             "https://*.neoncrm.com",
             "https://*.app.neoncrm.com",
             "https://fivecitiesorchidsociety.app.neoncrm.com"
         ]},
         r"/api/*": {"origins": [
             "https://*.neoncrm.com", 
             "https://*.app.neoncrm.com",
             "https://fivecitiesorchidsociety.app.neoncrm.com"
         ]}
     })

# Critical security: No fallback value for secret key
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise RuntimeError("CRITICAL SECURITY ERROR: SESSION_SECRET environment variable is not set. "
                      "Application cannot start without a secure session secret.")

# Apply ProxyFix middleware for Render deployment
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Apply WhiteNoise middleware for static file serving in production
app.wsgi_app = WhiteNoise(
    app.wsgi_app,
    root='static/',
    prefix='static/',
    index_file=True
)

# Configure CSP headers for iframe embedding (NeonOne compatibility)
@app.after_request
def add_security_headers(response):
    # REMOVE X-Frame-Options to allow Neon One iframe embedding
    # Only use CSP frame-ancestors for iframe control
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self' *.neoncrm.com *.app.neoncrm.com https://fivecitiesorchidsociety.app.neoncrm.com"
    return response

# Configure the database - Use PostgreSQL from environment (no fallback)
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("CRITICAL ERROR: DATABASE_URL environment variable is not set. "
                      "Application cannot start without database connection.")

# Fix sslmode capitalization issue (Render sometimes uses 'Require' instead of 'require')
database_url = database_url.replace('sslmode=Require', 'sslmode=require')

# Use pg8000 driver (pure Python, more stable than psycopg2 in some environments)
if 'postgresql://' in database_url and 'postgresql+pg8000://' not in database_url:
    # Replace with pg8000 driver
    database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    database_url = database_url.replace('postgresql+psycopg2://', 'postgresql+pg8000://')
    database_url = database_url.replace('postgresql+psycopg://', 'postgresql+pg8000://')
    # pg8000 doesn't support sslmode parameter - remove it
    database_url = database_url.replace('?sslmode=require', '')
    database_url = database_url.replace('&sslmode=require', '')
    database_url = database_url.replace('sslmode=require&', '')
    database_url = database_url.replace('sslmode=require', '')

# Log the database being used (hide password)
import re
safe_url = re.sub(r':([^:@]+)@', ':****@', database_url)
logging.info(f"📊 Connecting to database: {safe_url}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size for ZIP uploads
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.zip']
app.config['UPLOAD_FOLDER'] = 'temp'

# Initialize the app with the extension
db.init_app(app)

# Initialize CSRF protection for AI Breeder Pro widget forms
csrf = CSRFProtect(app)

# ============================================================================
# PRODUCTION STABILITY: Inject AI status into all templates
# ============================================================================
@app.context_processor
def inject_ai_status():
    """Make AI status available to all templates for UI banners."""
    from app_utils.settings import ORCHID_AI_ENABLED
    from app_utils.ai_utils import get_ai_status
    return {
        'ORCHID_AI_ENABLED': ORCHID_AI_ENABLED,
        'ai_status': get_ai_status()
    }

with app.app_context():
    # Import models to ensure tables are created - lazy import to avoid circular import
    try:
        import models
        import parentage_models  # Import additional models
    except ImportError as e:
        logging.warning(f"Model import issue (will retry): {e}")
    
    # Initialize database
    try:
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Database creation error: {e}")
    
    # Import and register auth blueprints after db initialization
    try:
        from auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except ImportError as e:
        logging.warning(f"Auth routes not available: {e}")
    
    # Register Widget Deployment Manifest blueprint
    try:
        from app_utils.routes_manifest import bp_manifest
        app.register_blueprint(bp_manifest)
        logging.info("Widget manifest endpoints registered: /manifest and /api/manifest")
    except ImportError as e:
        logging.warning(f"Manifest routes not available: {e}")
    
    # Register Taxonomy Widget Suite API blueprint
    try:
        from app_utils.routes_taxonomy import bp_taxonomy
        app.register_blueprint(bp_taxonomy, url_prefix='/api')
        logging.info("✅ Taxonomy Widget Suite API registered at /api/taxonomy/*")
    except ImportError as e:
        logging.warning(f"Taxonomy routes not available: {e}")
    
    # Register Gary Yong Gee Partnership Demo
    try:
        from gary_photo_demo import gary_demo
        from gary_partnership_api import gary_api
        app.register_blueprint(gary_demo)
        app.register_blueprint(gary_api)
        logging.info("✅ Gary Yong Gee Partnership Demo registered at /gary-photo-demo")
    except ImportError as e:
        logging.warning(f"Gary demo routes not available: {e}")
    
    # Register Culture Sheets blueprint
    try:
        from routes_culture_sheets import culture_sheets_bp
        app.register_blueprint(culture_sheets_bp)
        logging.info("✅ Culture Sheets routes registered at /culture-sheets/*")
    except ImportError as e:
        logging.warning(f"Culture sheets routes not available: {e}")
    
    # Register Replit Auth blueprint (optional - only on Replit)
    try:
        from replit_auth import make_replit_blueprint
        replit_bp = make_replit_blueprint()
        if replit_bp:
            app.register_blueprint(replit_bp, url_prefix="/auth")
            logging.info("✅ Replit Auth initialized successfully")
        else:
            logging.info("⚠️ Replit Auth skipped (REPL_ID not set - running on external platform)")
    except ImportError as e:
        logging.warning(f"⚠️ Replit Auth not available: {e}")
    except Exception as e:
        logging.warning(f"⚠️ Replit Auth initialization error: {e}")
    
    # Initialize judging standards
    try:
        from judging_standards import initialize_judging_standards
        initialize_judging_standards()
        print("Judging standards initialized")
    except Exception as e:
        print(f"Judging standards initialization error: {e}")
    
    # Initialize AI Breeder Assistant Pro widget
    try:
        from ai_breeder_assistant_pro import register_ai_breeder_pro
        register_ai_breeder_pro(app)
        print("🧬 AI Breeder Assistant Pro widget initialized with enhanced features")
    except Exception as e:
        print(f"AI Breeder Assistant Pro initialization error: {e}")
    
    # Register FCOS Judge PWA widget  
    try:
        from routes_fcos_judge import register_fcos_judge_routes
        register_fcos_judge_routes(app)
        print("📱 FCOS Orchid Judge PWA widget initialized")
    except Exception as e:
        print(f"FCOS Judge widget initialization error: {e}")
    
    # Register Platform Template Routes (Famous AI widget migration)
    try:
        from routes_platform import platform_bp
        app.register_blueprint(platform_bp)
        print("🌸 Platform Template routes initialized (widget container pages)")
    except Exception as e:
        print(f"Platform Template initialization error: {e}")

# Auth blueprint is now registered inside app context above

# Register user weather blueprint
from user_weather_routes import user_weather_bp
app.register_blueprint(user_weather_bp)

# Initialize AOS glossary system (crossword blueprint already registered elsewhere)
try:
    from aos_glossary_extractor import AOSGlossaryExtractor
    glossary_extractor = AOSGlossaryExtractor()
    logging.info("✅ AOS Glossary system initialized successfully")
except ImportError as e:
    logging.warning(f"⚠️ AOS Glossary system not available: {e}")

# Import routes after app initialization
# Allow skipping routes.py for widget-only testing (set SKIP_FULL_ROUTES=1)
if not os.environ.get('SKIP_FULL_ROUTES'):
    try:
        import routes  # Full featured routes with complete homepage
        logging.info("✅ Full routes module loaded successfully")
    except Exception as e:
        logging.error(f"⚠️ Could not load full routes module: {e}")
        logging.info("💡 TIP: For widget-only testing, run: SKIP_FULL_ROUTES=1 python widget_test_app.py")
else:
    logging.info("🧪 SKIP_FULL_ROUTES enabled - Running in widget-only test mode")
# import simple_routes  # DISABLED - using full routes instead
import botanical_routes  # Import botanical database routes
import botanical_analysis_route  # Additional botanical analysis integration
import admin_system  # Administrative system with ultimate database control
import simple_admin_login  # Simple admin login without CSRF (emergency access)
import emergency_admin  # Ultra-simple emergency login bypass
import admin_unlock  # URL-based emergency unlock
import user_registration  # User registration and profile system

# Register additional blueprints
try:
    from drive_importer import drive_import_bp
    app.register_blueprint(drive_import_bp)
    print("Google Drive import system initialized")
except Exception as e:
    print(f"Drive import initialization error: {e}")

try:
    from orchid_comparison_system import comparison_bp
    app.register_blueprint(comparison_bp)
    print("Orchid comparison system initialized")
except Exception as e:
    print(f"Comparison system initialization error: {e}")

try:
    from citation_system import citation_bp
    app.register_blueprint(citation_bp)
    print("Citation and attribution system initialized")
except Exception as e:
    print(f"Citation system initialization error: {e}")

try:
    from widget_system import widget_bp
    app.register_blueprint(widget_bp)
    print("Widget system for external integration initialized")
except Exception as e:
    print(f"Widget system initialization error: {e}")

try:
    from youtube_orchid_widget import youtube_widget
    app.register_blueprint(youtube_widget)
    print("YouTube Orchid Widget initialized for FCOS integration")
except Exception as e:
    print(f"YouTube widget initialization error: {e}")

try:
    from neon_one_widget_package import neon_one_widgets
    app.register_blueprint(neon_one_widgets)
    print("Neon One Widget Package initialized for CMS integration")
except Exception as e:
    print(f"Neon One widget package initialization error: {e}")

try:
    from orchid_interaction_routes import orchid_interaction_bp
    app.register_blueprint(orchid_interaction_bp)
    print("Orchid Interaction Explorer system initialized")
except Exception as e:
    print(f"Orchid Interaction Explorer initialization error: {e}")

try:
    from system_monitor_dashboard import monitor_bp, initialize_monitoring
    app.register_blueprint(monitor_bp)
    # Monitoring disabled - can be started manually from dashboard
    # initialize_monitoring()
    print("System Monitor Dashboard initialized (monitoring disabled)")
except Exception as e:
    print(f"System Monitor Dashboard initialization error: {e}")

try:
    from master_tracker import tracker_bp
    app.register_blueprint(tracker_bp)
    print("Master Project Tracker initialized at /tracker and /api/tracker/status")
except Exception as e:
    print(f"Master Project Tracker initialization error: {e}")

try:
    from brain_status_api import brain_status_bp
    app.register_blueprint(brain_status_bp)
    print("Brain Status API initialized at /api/brain/status")
except Exception as e:
    print(f"Brain Status API initialization error: {e}")

try:
    from orchid_games import games_bp
    app.register_blueprint(games_bp)
    print("Orchid Games system initialized")
except Exception as e:
    print(f"Orchid Games initialization error: {e}")

# Temporarily disable discovery game due to import conflicts
# try:
#     from interactive_species_discovery import discovery_bp
#     app.register_blueprint(discovery_bp)
#     print("Interactive Species Discovery game initialized")
# except Exception as e:
#     print(f"Species Discovery initialization error: {e}")

try:
    from api_v2_routes import api_v2
    app.register_blueprint(api_v2)
    print("API v2 routes initialized - FastAPI-compatible endpoints available")
except Exception as e:
    print(f"API v2 initialization error: {e}")
