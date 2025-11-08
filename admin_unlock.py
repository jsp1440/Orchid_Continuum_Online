"""
Emergency Admin Unlock - URL-based authentication
USE: /unlock-admin?key=YOUR_ADMIN_PASSWORD
"""
import os
from flask import request, session, redirect, jsonify
from app import app

@app.route('/unlock-admin')
def unlock_admin():
    """Emergency admin unlock via URL parameter"""
    key = request.args.get('key')
    if key and key == os.environ.get('ADMIN_PASSWORD'):
        session['admin_authenticated'] = True
        return redirect('/admin')
    return jsonify({"error": "Invalid key"}), 401
