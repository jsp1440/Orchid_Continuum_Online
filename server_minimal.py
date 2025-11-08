"""
Minimal fast-loading Flask server - Production ready.
Application factory pattern with deferred initialization.
"""
import os
import logging
from flask import Flask, jsonify, render_template_string

logging.basicConfig(level=logging.INFO)

def create_app():
    """Application factory - fast startup, no heavy lifting."""
    app = Flask(__name__)
    
    # Minimal config only
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "")
    
    @app.route('/health')
    @app.route('/healthz')
    def health():
        return jsonify({"status": "healthy"}), 200
    
    @app.route('/')
    def index():
        return render_template_string("""
        <html>
        <head>
            <title>🌺 The Orchid Continuum</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #7B2CBF; }
                a { color: #9D4EDD; text-decoration: none; border-bottom: 1px solid; }
                .status { background: #E0AAFF; padding: 15px; border-radius: 8px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>🌺 The Orchid Continuum</h1>
            <div class="status">
                <strong>Status:</strong> Server Running ✅
            </div>
            <h2>Available Services:</h2>
            <ul>
                <li><a href="/bloombuilder">BloomBuilder Widget</a></li>
                <li><a href="/julius/status">Julius AI Monitor</a></li>
                <li><a href="/upload-monitor">📊 Google Drive Upload Monitor</a></li>
                <li><a href="/tracker">Task Tracker</a></li>
                <li><a href="/health">Health Check</a></li>
            </ul>
        </body>
        </html>
        """)
    
    @app.route('/bloombuilder')
    def bloombuilder_stub():
        """Load BloomBuilder on demand."""
        try:
            from bloombuilder_routes import bloombuilder_bp
            if 'bloombuilder' not in [bp.name for bp in app.blueprints.values()]:
                app.register_blueprint(bloombuilder_bp)
                logging.info("✅ BloomBuilder loaded on demand")
            return bloombuilder_bp.send_static_file('index.html')
        except Exception as e:
            return jsonify({"error": str(e), "message": "BloomBuilder loading..."}), 500
    
    @app.route('/julius/status')
    def julius_stub():
        """Load Julius monitor on demand."""
        try:
            from routes_julius_monitor import julius_monitor_bp
            if 'julius_monitor' not in [bp.name for bp in app.blueprints.values()]:
                app.register_blueprint(julius_monitor_bp)
                logging.info("✅ Julius Monitor loaded on demand")
            # Redirect to the actual status page
            from flask import redirect
            return redirect('/julius-ai-monitor')
        except Exception as e:
            return jsonify({"error": str(e), "message": "Julius Monitor loading..."}), 500
    
    @app.route('/tracker')
    def tracker_stub():
        """Tracker page."""
        return jsonify({
            "message": "Task tracker available",
            "tasks": []
        })
    
    # Upload Monitor blueprint - register immediately for clean routing
    try:
        from routes_upload_monitor import upload_monitor_bp
        app.register_blueprint(upload_monitor_bp)
        logging.info("✅ Upload Monitor registered")
    except Exception as e:
        logging.warning(f"Upload Monitor not available: {e}")
    
    logging.info("🌺 App factory complete - ready to serve!")
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    print(f"""
============================================================
🌺 The Orchid Continuum - Minimal Server
============================================================
Server: http://0.0.0.0:{port}
Health: http://0.0.0.0:{port}/health
BloomBuilder: http://0.0.0.0:{port}/bloombuilder
Julius Monitor: http://0.0.0.0:{port}/julius/status
============================================================
""")
    app.run(host='0.0.0.0', port=port, debug=False)
