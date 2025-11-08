"""Lightweight BloomBuilder-only application"""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.orm import DeclarativeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

with app.app_context():
    import models
    db.create_all()
    logger.info("✅ Database initialized")

# Register BloomBuilder
from routes_bloombuilder import bloombuilder_bp
app.register_blueprint(bloombuilder_bp)
logger.info("🌺 BloomBuilder registered at /bloombuilder")

# Simple homepage redirect
@app.route('/')
def index():
    from flask import redirect, url_for
    return redirect(url_for('bloombuilder.index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
