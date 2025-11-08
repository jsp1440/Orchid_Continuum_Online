"""
WSGI entrypoint for production deployment.
This file is used by gunicorn and other WSGI servers.
"""
from server_minimal import create_app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    # For direct execution (development)
    app.run(host='0.0.0.0', port=5000, debug=False)
