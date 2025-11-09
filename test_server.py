#!/usr/bin/env python
"""
Minimal Test Server - Only BloomBuilder & Culture Sheets
Fast startup for testing specific widgets
"""
import os
import sys
import logging
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

logging.basicConfig(level=logging.INFO)

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create minimal app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "test-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# Health check
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "widgets": ["bloombuilder", "culture_sheets"]}), 200

@app.route('/')
def index():
    return render_template('base.html', title="Orchid Continuum - Widget Test")

# Import and register ONLY the widgets we want to test
with app.app_context():
    try:
        # Import models
        import models
        db.create_all()
        logging.info("✅ Database initialized")
    except Exception as e:
        logging.warning(f"Database init: {e}")
    
    # Register BloomBuilder
    try:
        from routes_bloombuilder import bloombuilder_bp
        app.register_blueprint(bloombuilder_bp)
        logging.info("✅ BloomBuilder registered at /bloombuilder")
    except Exception as e:
        logging.error(f"❌ BloomBuilder failed: {e}")
    
    # Register Culture Sheets
    try:
        from aos_baker_culture_routes import culture_bp
        app.register_blueprint(culture_bp)
        logging.info("✅ Culture Sheets registered at /culture/*")
    except Exception as e:
        logging.error(f"❌ Culture Sheets failed: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*70)
    print("🧪 WIDGET TEST SERVER")
    print("="*70)
    print(f"Health: http://0.0.0.0:{port}/health")
    print(f"BloomBuilder: http://0.0.0.0:{port}/bloombuilder")
    print(f"Culture Demo: http://0.0.0.0:{port}/culture/demo")
    print(f"Culture Species: http://0.0.0.0:{port}/culture/species")
    print("="*70 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)
