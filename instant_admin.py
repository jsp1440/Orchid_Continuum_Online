"""
Instant Admin Access - Ultra-lightweight, no heavy imports
This file runs BEFORE app.py loads to provide instant login
"""
import os
from flask import Flask, session, redirect, request, render_template_string
from werkzeug.security import check_password_hash, generate_password_hash

# Create minimal Flask app
instant_app = Flask(__name__)
instant_app.secret_key = os.environ.get("SESSION_SECRET")

# Hash password once
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', ''))

@instant_app.route('/instant-admin', methods=['GET', 'POST'])
def instant_admin():
    if request.method == 'POST':
        if check_password_hash(ADMIN_PASSWORD_HASH, request.form.get('password', '')):
            session['admin_authenticated'] = True
            return '<h1>✅ Logged In!</h1><p>Go to: <a href="/admin">/admin</a></p>'
        return '<h1>❌ Wrong Password</h1><a href="/instant-admin">Try Again</a>', 401
    
    return render_template_string('''
    <!DOCTYPE html>
    <html><head><title>Instant Admin</title></head>
    <body style="font-family:Arial; max-width:400px; margin:100px auto;">
        <h1>🚀 Instant Admin</h1>
        <form method="POST">
            <input type="password" name="password" placeholder="Password" required style="width:100%; padding:10px; margin:10px 0; font-size:16px;">
            <button type="submit" style="width:100%; padding:15px; background:#007bff; color:white; border:none; font-size:16px;">Login</button>
        </form>
    </body></html>
    ''')

if __name__ == '__main__':
    instant_app.run(host='0.0.0.0', port=5001)
