#!/usr/bin/env python3
"""
Widget-Only Test App
Run the Culture Sheet Widget system without loading the full routes module

Usage:
    python widget_test_app.py
    
    Or start Flask server:
    SKIP_FULL_ROUTES=1 python main.py
"""
import os

# Set flag to skip loading routes.py (which has import errors)
os.environ['SKIP_FULL_ROUTES'] = '1'
os.environ['AI_DISABLED'] = '1'  # Skip AI initialization for faster testing

# Import app (this will skip routes.py due to flag above)
from app import app

if __name__ == '__main__':
    print('\n' + '='*70)
    print('🌺 CULTURE SHEET WIDGET - Test Server')
    print('='*70)
    print('\n✅ Widget-only mode enabled (full routes skipped)')
    print('\nAvailable endpoints:')
    print('  • Widget API: /api/widget/*')
    print('  • Admin Dashboard: /admin/widget/dashboard?admin_password=YOUR_PASSWORD')
    print('\n⚠️  IMPORTANT: Set ADMIN_PASSWORD in Replit Secrets first!')
    print('\nStarting Flask development server on http://0.0.0.0:5000')
    print('='*70 + '\n')
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
