#!/usr/bin/env python3
"""
Simple server to quickly test the Gary demo page
"""
from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return '''
    <html>
    <body>
    <h1>Gary Demo Test Server</h1>
    <p><a href="/static/gary-demo-live.html">View Gary Demo</a></p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Simple Demo Server Starting")
    print("="*60)
    print("Demo URL: http://0.0.0.0:5000/static/gary-demo-live.html")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
