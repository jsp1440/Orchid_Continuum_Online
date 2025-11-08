"""
EMERGENCY ADMIN LOGIN - Ultra-simple, no dependencies
"""
import os
from flask import request, session, redirect, render_template_string
from app import app, csrf

EMERGENCY_PASSWORD = os.environ.get('ADMIN_PASSWORD')

@app.route('/emergency-admin', methods=['GET', 'POST'])
@csrf.exempt
def emergency_admin():
    if request.method == 'POST':
        if request.form.get('password') == EMERGENCY_PASSWORD:
            session['admin_authenticated'] = True
            return redirect('/admin')
        return "Wrong password", 401
    
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>Emergency Admin</title></head>
<body>
    <h1>Emergency Admin Access</h1>
    <form method="POST">
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
</body>
</html>
''')
