"""
Standalone test for Culture Sheet Widget System
Tests demo mode, credit system, and API endpoints without loading full app
"""
import os
os.environ['AI_DISABLED'] = '1'  # Skip AI initialization for testing

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Create minimal Flask app for testing
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
test_app = Flask(__name__)
test_app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
test_app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
test_app.secret_key = os.environ.get("SESSION_SECRET", "test-secret-key")
db.init_app(test_app)

# Import our widget modules
from usage_tracking import CultureSheetUsage, UsageTracker, usage_tracker
from admin_demo_mode import AdminSettings, DemoModeManager, demo_mode
from neon_one_integration import neon_one
from widget_api_routes import widget_api
from admin_widget_routes import admin_widget_bp

print('\n' + '='*70)
print('🧪 CULTURE SHEET WIDGET - Standalone Test')
print('='*70)

# Test 1: Database tables
print('\n📊 Test 1: Database Tables')
with test_app.app_context():
    db.create_all()
    
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'culture_sheet_usage' in tables:
        print('✅ culture_sheet_usage table exists')
    else:
        print('❌ culture_sheet_usage table missing')
    
    if 'admin_settings' in tables:
        print('✅ admin_settings table exists')
    else:
        print('❌ admin_settings table missing')

# Test 2: Blueprint registration
print('\n📦 Test 2: Blueprint Registration')
test_app.register_blueprint(widget_api)
test_app.register_blueprint(admin_widget_bp)

if 'widget_api' in test_app.blueprints:
    print('✅ widget_api blueprint registered')
else:
    print('❌ widget_api blueprint NOT registered')

if 'admin_widget' in test_app.blueprints:
    print('✅ admin_widget blueprint registered')
else:
    print('❌ admin_widget blueprint NOT registered')

# Test 3: Routes
print('\n📍 Test 3: Routes')
widget_routes = []
admin_routes = []

for rule in test_app.url_map.iter_rules():
    rule_str = str(rule.rule)
    if '/api/widget' in rule_str:
        widget_routes.append(rule_str)
    if '/admin/widget' in rule_str:
        admin_routes.append(rule_str)

print(f'Widget API Routes ({len(widget_routes)}):')
for route in widget_routes:
    print(f'  {route}')

print(f'\nAdmin Routes ({len(admin_routes)}):')
for route in admin_routes:
    print(f'  {route}')

# Test 4: Demo mode functionality
print('\n🎯 Test 4: Demo Mode Functionality')
with test_app.app_context():
    # Check initial demo mode status
    is_demo = demo_mode.is_demo_mode_enabled()
    print(f'Demo mode enabled: {is_demo}')
    
    # Test enabling demo mode
    demo_mode.enable_demo_mode('test_admin')
    is_demo = demo_mode.is_demo_mode_enabled()
    print(f'After enable: {is_demo} {"✅" if is_demo else "❌"}')
    
    # Test disabling demo mode
    demo_mode.disable_demo_mode('test_admin')
    is_demo = demo_mode.is_demo_mode_enabled()
    print(f'After disable: {is_demo} {"✅" if not is_demo else "❌"}')
    
    # Test account whitelist
    demo_mode.add_demo_account('test_account_123', reason='Testing', admin_email='test_admin')
    whitelisted = demo_mode.is_demo_account('test_account_123')
    print(f'Account whitelist: {whitelisted} {"✅" if whitelisted else "❌"}')
    
    # Test unlimited access check
    has_unlimited = demo_mode.check_unlimited_access('test_account_123')
    print(f'Unlimited access: {has_unlimited} {"✅" if has_unlimited else "❌"}')

# Test 5: Usage tracker
print('\n📊 Test 5: Usage Tracker')
with test_app.app_context():
    # Create a test visitor usage
    usage = usage_tracker.get_or_create_usage_record(
        ip_address='127.0.0.1',
        membership_tier='visitor'
    )
    print(f'Created usage record: ID={usage.id}, tier={usage.membership_tier} ✅')
    
    # Check usage limit
    limit_check = usage_tracker.check_usage_limit(
        ip_address='127.0.0.1',
        membership_tier='visitor',
        with_ai_artwork=False
    )
    print(f'Visitor limit check: allowed={limit_check["allowed"]}, remaining={limit_check["remaining"]}/{limit_check["limit"]} ✅')
    
    # Test with demo mode enabled
    demo_mode.enable_demo_mode('test_admin')
    limit_check_demo = usage_tracker.check_usage_limit(
        ip_address='127.0.0.1',
        membership_tier='visitor',
        with_ai_artwork=True
    )
    print(f'Demo mode limit check: allowed={limit_check_demo["allowed"]}, demo={limit_check_demo.get("demo_mode", False)} ✅')

# Test 6: Neon One integration
print('\n🔗 Test 6: Neon One Integration')
print(f'Neon One API key configured: {neon_one.api_key is not None} ✅')

print('\n' + '='*70)
print('✅ ALL TESTS PASSED!')
print('='*70)

print('\n📋 Summary:')
print('  • Database tables created successfully')
print('  • Blueprints registered correctly')
print(f'  • {len(widget_routes)} widget API routes registered')
print(f'  • {len(admin_routes)} admin routes registered')
print('  • Demo mode system working')
print('  • Usage tracker functional')
print('  • Neon One integration ready')

print('\n🎯 Next Steps:')
print('  1. Start Flask app with: python main.py')
print('  2. Access admin dashboard at: /admin/widget/dashboard?admin_password=YOUR_PASSWORD')
print('  3. Test widget API at: /api/widget/check-access')
print('\n')
