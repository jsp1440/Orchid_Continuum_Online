import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from whitenoise import WhiteNoise

logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

CORS(app,
     origins=[
         "https://*.neoncrm.com",
         "https://*.app.neoncrm.com",
         "https://fivecitiesorchidsociety.app.neoncrm.com",
         "http://localhost:*",
         "https://localhost:*"
     ],
     supports_credentials=False,
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

app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise RuntimeError("CRITICAL SECURITY ERROR: SESSION_SECRET environment variable is not set. Application cannot start without a secure session secret.")

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/', index_file=True)

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "frame-ancestors 'self' *.neoncrm.com *.app.neoncrm.com https://fivecitiesorchidsociety.app.neoncrm.com"
    return response

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("CRITICAL ERROR: DATABASE_URL environment variable is not set. Application cannot start without database connection.")

database_url = database_url.replace('sslmode=Require', 'sslmode=require')
if 'postgresql://' in database_url and 'postgresql+pg8000://' not in database_url:
    database_url = database_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    database_url = database_url.replace('postgresql+psycopg2://', 'postgresql+pg8000://')
    database_url = database_url.replace('postgresql+psycopg://', 'postgresql+pg8000://')
    database_url = database_url.replace('?sslmode=require', '')
    database_url = database_url.replace('&sslmode=require', '')
    database_url = database_url.replace('sslmode=require&', '')
    database_url = database_url.replace('sslmode=require', '')

import re
safe_url = re.sub(r':([^:@]+)@', ':****@', database_url)
logging.info(f"📊 Connecting to database: {safe_url}")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_recycle": 300, "pool_pre_ping": True}
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.zip']
app.config['UPLOAD_FOLDER'] = 'temp'

db.init_app(app)
csrf = CSRFProtect(app)

@app.context_processor
def inject_ai_status():
    from app_utils.settings import ORCHID_AI_ENABLED
    from app_utils.ai_utils import get_ai_status
    return {'ORCHID_AI_ENABLED': ORCHID_AI_ENABLED, 'ai_status': get_ai_status()}

with app.app_context():
    try:
        import models
        import parentage_models
        import tracker_models
    except ImportError as e:
        logging.warning(f"Model import issue (will retry): {e}")

    try:
        db.create_all()
        logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Database creation error: {e}")

    try:
        from auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except ImportError as e:
        logging.warning(f"Auth routes not available: {e}")

    try:
        from app_utils.routes_manifest import bp_manifest
        app.register_blueprint(bp_manifest)
        logging.info("Widget manifest endpoints registered: /manifest and /api/manifest")
    except ImportError as e:
        logging.warning(f"Manifest routes not available: {e}")

    try:
        from app_utils.routes_taxonomy import bp_taxonomy
        app.register_blueprint(bp_taxonomy, url_prefix='/api')
        logging.info("✅ Taxonomy Widget Suite API registered at /api/taxonomy/*")
    except ImportError as e:
        logging.warning(f"Taxonomy routes not available: {e}")

    try:
        from gary_photo_demo import gary_demo
        from gary_partnership_api import gary_api
        app.register_blueprint(gary_demo)
        app.register_blueprint(gary_api)
        logging.info("✅ Gary Yong Gee Partnership Demo registered at /gary-photo-demo")
    except ImportError as e:
        logging.warning(f"Gary demo routes not available: {e}")

    try:
        from routes_culture_sheets import culture_sheets_bp
        app.register_blueprint(culture_sheets_bp)
        logging.info("✅ Culture Sheets routes registered at /culture-sheets/*")
    except ImportError as e:
        logging.warning(f"Culture sheets routes not available: {e}")

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

    try:
        from judging_standards import initialize_judging_standards
        initialize_judging_standards()
        print("Judging standards initialized")
    except Exception as e:
        print(f"Judging standards initialization error: {e}")

    try:
        from ai_breeder_assistant_pro import register_ai_breeder_pro
        register_ai_breeder_pro(app)
        print("🧬 AI Breeder Assistant Pro widget initialized with enhanced features")
    except Exception as e:
        print(f"AI Breeder Assistant Pro initialization error: {e}")

    try:
        from routes_fcos_judge import register_fcos_judge_routes
        register_fcos_judge_routes(app)
        print("📱 FCOS Orchid Judge PWA widget initialized")
    except Exception as e:
        print(f"FCOS Judge widget initialization error: {e}")

    try:
        from routes_platform import platform_bp
        app.register_blueprint(platform_bp)
        print("🌸 Platform Template routes initialized (widget container pages)")
    except Exception as e:
        print(f"Platform Template initialization error: {e}")

from user_weather_routes import user_weather_bp
app.register_blueprint(user_weather_bp)

try:
    from aos_glossary_extractor import AOSGlossaryExtractor
    glossary_extractor = AOSGlossaryExtractor()
    logging.info("✅ AOS Glossary system initialized successfully")
except ImportError as e:
    logging.warning(f"⚠️ AOS Glossary system not available: {e}")

if not os.environ.get('SKIP_FULL_ROUTES'):
    try:
        import routes
        logging.info("✅ Full routes module loaded successfully")
    except Exception as e:
        logging.error(f"⚠️ Could not load full routes module: {e}")
        logging.info("💡 TIP: For widget-only testing, run: SKIP_FULL_ROUTES=1 python widget_test_app.py")
else:
    logging.info("🧪 SKIP_FULL_ROUTES enabled - Running in widget-only test mode")

import botanical_routes
import botanical_analysis_route
import admin_system
import simple_admin_login
import emergency_admin
import admin_unlock
import user_registration

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

try:
    from api_v2_routes import api_v2
    app.register_blueprint(api_v2)
    print("API v2 routes initialized - FastAPI-compatible endpoints available")
except Exception as e:
    print(f"API v2 initialization error: {e}")
