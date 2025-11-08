"""BloomBuilder - Digital Orchid Morphology Lab (Standalone)"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-bloombuilder-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS for React frontend
CORS(app, resources={r"/*": {"origins": "*"}})

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    db.create_all()
    logger.info("✅ Database tables created")

# Register BloomBuilder routes
from routes_bloombuilder import bloombuilder_bp
from routes_traits import traits_bp
from routes_documents import documents_bp

app.register_blueprint(bloombuilder_bp)
app.register_blueprint(traits_bp)
app.register_blueprint(documents_bp)
logger.info("🌺 BloomBuilder registered at /bloombuilder")
logger.info("🧬 Trait Toggle System registered at /bloombuilder/api/traits")
logger.info("📄 Document Access registered at /documents")

# Serve React BloomBuilder Widget
@app.route('/widget')
@app.route('/widget/<path:path>')
def serve_widget(path='index.html'):
    from flask import send_from_directory
    import os
    static_folder = app.static_folder or 'static'
    widget_dir = os.path.join(static_folder, 'bloombuilder_app')
    if path != 'index.html' and not os.path.exists(os.path.join(widget_dir, path)):
        path = 'index.html'
    return send_from_directory(widget_dir, path)

# Homepage redirect to BloomBuilder
@app.route('/')
def index():
    from flask import redirect
    return redirect('/widget')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
