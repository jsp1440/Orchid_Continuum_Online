"""
Simple Admin Login - No CSRF, Direct Password Check
This is a standalone admin login that works without CSRF protection
"""
import os
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from app import app

# Get admin credentials from environment
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD) if ADMIN_PASSWORD else None

@app.route('/admin/simple-login', methods=['GET', 'POST'])
def simple_admin_login():
    """Simple admin login without CSRF - for emergency access"""
    
    if not ADMIN_PASSWORD_HASH:
        return "Admin access disabled - ADMIN_PASSWORD not set", 403
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_authenticated'] = True
            session['admin_login_time'] = 'now'
            flash('Admin access granted!', 'success')
            return redirect('/admin/enrichment/dashboard')
        else:
            return "Invalid password", 403
    
    # Simple HTML form - no CSRF
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <style>
            body { font-family: Arial; max-width: 400px; margin: 100px auto; padding: 20px; }
            input { width: 100%; padding: 10px; margin: 10px 0; font-size: 16px; }
            button { width: 100%; padding: 15px; background: #007bff; color: white; border: none; font-size: 16px; cursor: pointer; }
            button:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🌺 Admin Login</h1>
        <form method="POST">
            <input type="password" name="password" placeholder="Enter admin password" required autofocus>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    '''
