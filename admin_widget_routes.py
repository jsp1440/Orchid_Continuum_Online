"""
Admin Routes for Culture Sheet Widget Management
Allows admin to control demo mode, view usage statistics, manage whitelist
"""
import logging
from flask import Blueprint, request, jsonify, render_template_string
from datetime import datetime
from app import db
from admin_demo_mode import demo_mode, AdminSettings
from usage_tracking import usage_tracker, CultureSheetUsage

logger = logging.getLogger(__name__)

# Create blueprint for admin routes
admin_widget_bp = Blueprint('admin_widget', __name__, url_prefix='/admin/widget')


# Secure admin authentication check (requires ADMIN_PASSWORD environment variable)
def check_admin_auth():
    """Secure admin authentication check - requires ADMIN_PASSWORD in environment"""
    import os
    
    # SECURITY: No fallback value - admin password MUST be set
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if not admin_password:
        logger.error('🚨 SECURITY ERROR: ADMIN_PASSWORD environment variable not set!')
        return False, jsonify({
            'error': 'Server misconfiguration - Admin password not configured',
            'details': 'Contact system administrator to set ADMIN_PASSWORD environment variable'
        }), 500
    
    provided_password = request.headers.get('X-Admin-Password') or request.args.get('admin_password')
    
    if not provided_password:
        return False, jsonify({'error': 'Unauthorized - Missing admin password'}), 401
    
    if provided_password != admin_password:
        logger.warning(f'🚨 SECURITY: Failed admin login attempt from {request.remote_addr}')
        return False, jsonify({'error': 'Unauthorized - Invalid admin password'}), 401
    
    return True, None, None


@admin_widget_bp.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """Simple admin dashboard to control demo mode"""
    
    # Check admin auth
    is_admin, error_response, status_code = check_admin_auth()
    if not is_admin:
        return error_response, status_code
    
    # Get current status
    status = demo_mode.get_status()
    
    # Get usage statistics
    total_usage = CultureSheetUsage.query.count()
    visitor_usage = CultureSheetUsage.query.filter_by(membership_tier='visitor').count()
    member_usage = CultureSheetUsage.query.filter_by(membership_tier='member').count()
    life_member_usage = CultureSheetUsage.query.filter_by(membership_tier='life_member').count()
    
    total_sheets = db.session.query(db.func.sum(CultureSheetUsage.sheets_generated)).scalar() or 0
    total_ai_sheets = db.session.query(db.func.sum(CultureSheetUsage.sheets_with_ai_artwork)).scalar() or 0
    
    # Simple HTML dashboard
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Widget Admin Dashboard</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #9d4edd;
            }}
            .status {{
                font-size: 24px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .enabled {{
                color: #00c853;
            }}
            .disabled {{
                color: #d32f2f;
            }}
            button {{
                padding: 12px 24px;
                font-size: 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-right: 10px;
            }}
            .btn-enable {{
                background: #00c853;
                color: white;
            }}
            .btn-disable {{
                background: #d32f2f;
                color: white;
            }}
            .btn-action {{
                background: #2196f3;
                color: white;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background: #f5f5f5;
                font-weight: bold;
            }}
            input {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin-right: 10px;
            }}
        </style>
    </head>
    <body>
        <h1>🌺 Culture Sheet Widget - Admin Dashboard</h1>
        
        <div class="card">
            <h2>Demo Mode Control</h2>
            <div class="status {'enabled' if status['demo_mode_enabled'] else 'disabled'}">
                Status: {'✅ ENABLED (Unlimited for Everyone!)' if status['demo_mode_enabled'] else '🛑 DISABLED (Normal Limits)'}
            </div>
            <p>
                <strong>What is Demo Mode?</strong><br>
                When enabled, ALL users get unlimited culture sheets with AI artwork.
                Perfect for testing, debugging, or showcasing the widget to potential partners.
            </p>
            <button class="btn-enable" onclick="toggleDemoMode(true)">Enable Demo Mode</button>
            <button class="btn-disable" onclick="toggleDemoMode(false)">Disable Demo Mode</button>
        </div>
        
        <div class="card">
            <h2>Demo Account Whitelist</h2>
            <p>
                <strong>Add specific accounts</strong> for unlimited access (works even when demo mode is off).<br>
                Use this for: beta testers, debugging helpers, VIP members.
            </p>
            <p>Currently {status['demo_account_count']} whitelisted accounts</p>
            
            <div style="margin: 20px 0;">
                <input type="text" id="account_id" placeholder="Neon One Account ID" style="width: 300px;">
                <input type="text" id="reason" placeholder="Reason (e.g. beta tester)" style="width: 200px;">
                <button class="btn-action" onclick="addDemoAccount()">Add to Whitelist</button>
            </div>
            
            <h3>Current Whitelist:</h3>
            <ul id="whitelist">
                {''.join(f'<li>{acc} <button onclick="removeDemoAccount(\\'{acc}\\')">Remove</button></li>' for acc in status['demo_accounts']) if status['demo_accounts'] else '<li>No accounts whitelisted</li>'}
            </ul>
        </div>
        
        <div class="card">
            <h2>Usage Statistics</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Total Users</td>
                    <td>{total_usage}</td>
                </tr>
                <tr>
                    <td>Visitors</td>
                    <td>{visitor_usage}</td>
                </tr>
                <tr>
                    <td>Members</td>
                    <td>{member_usage}</td>
                </tr>
                <tr>
                    <td>Life Members</td>
                    <td>{life_member_usage}</td>
                </tr>
                <tr>
                    <td>Total Sheets Generated</td>
                    <td><strong>{total_sheets}</strong></td>
                </tr>
                <tr>
                    <td>Sheets with AI Artwork</td>
                    <td><strong>{total_ai_sheets}</strong></td>
                </tr>
            </table>
        </div>
        
        <script>
            const password = new URLSearchParams(window.location.search).get('admin_password');
            
            function toggleDemoMode(enable) {{
                fetch('/admin/widget/demo-mode/' + (enable ? 'enable' : 'disable'), {{
                    method: 'POST',
                    headers: {{ 'X-Admin-Password': password }}
                }})
                .then(r => r.json())
                .then(data => {{
                    alert(data.message || 'Demo mode ' + (enable ? 'enabled' : 'disabled'));
                    location.reload();
                }});
            }}
            
            function addDemoAccount() {{
                const accountId = document.getElementById('account_id').value;
                const reason = document.getElementById('reason').value;
                
                if (!accountId) {{
                    alert('Please enter account ID');
                    return;
                }}
                
                fetch('/admin/widget/demo-accounts/add', {{
                    method: 'POST',
                    headers: {{ 
                        'Content-Type': 'application/json',
                        'X-Admin-Password': password
                    }},
                    body: JSON.stringify({{ account_id: accountId, reason: reason }})
                }})
                .then(r => r.json())
                .then(data => {{
                    alert(data.message || 'Account added');
                    location.reload();
                }});
            }}
            
            function removeDemoAccount(accountId) {{
                if (!confirm('Remove ' + accountId + ' from whitelist?')) return;
                
                fetch('/admin/widget/demo-accounts/remove', {{
                    method: 'POST',
                    headers: {{ 
                        'Content-Type': 'application/json',
                        'X-Admin-Password': password
                    }},
                    body: JSON.stringify({{ account_id: accountId }})
                }})
                .then(r => r.json())
                .then(data => {{
                    alert(data.message || 'Account removed');
                    location.reload();
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    return render_template_string(html)


@admin_widget_bp.route('/demo-mode/enable', methods=['POST'])
def enable_demo_mode():
    """Enable demo mode"""
    is_admin, error_response, status_code = check_admin_auth()
    if not is_admin:
        return error_response, status_code
    
    demo_mode.enable_demo_mode(admin_email='admin')
    
    return jsonify({
        'success': True,
        'message': '✅ Demo mode enabled - All users now have unlimited access!'
    })


@admin_widget_bp.route('/demo-mode/disable', methods=['POST'])
def disable_demo_mode():
    """Disable demo mode"""
    is_admin, error_response, status_code = check_admin_auth()
    if not is_admin:
        return error_response, status_code
    
    demo_mode.disable_demo_mode(admin_email='admin')
    
    return jsonify({
        'success': True,
        'message': '🛑 Demo mode disabled - Normal usage limits restored'
    })


@admin_widget_bp.route('/demo-accounts/add', methods=['POST'])
def add_demo_account():
    """Add account to demo whitelist"""
    is_admin, error_response, status_code = check_admin_auth()
    if not is_admin:
        return error_response, status_code
    
    data = request.get_json()
    account_id = data.get('account_id')
    reason = data.get('reason', 'No reason provided')
    
    if not account_id:
        return jsonify({'error': 'account_id required'}), 400
    
    added = demo_mode.add_demo_account(account_id, reason=reason, admin_email='admin')
    
    if added:
        return jsonify({
            'success': True,
            'message': f'✅ Added {account_id} to unlimited access whitelist'
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Account {account_id} already on whitelist'
        })


@admin_widget_bp.route('/demo-accounts/remove', methods=['POST'])
def remove_demo_account():
    """Remove account from demo whitelist"""
    is_admin, error_response, status_code = check_admin_auth()
    if not is_admin:
        return error_response, status_code
    
    data = request.get_json()
    account_id = data.get('account_id')
    
    if not account_id:
        return jsonify({'error': 'account_id required'}), 400
    
    removed = demo_mode.remove_demo_account(account_id, admin_email='admin')
    
    if removed:
        return jsonify({
            'success': True,
            'message': f'🛑 Removed {account_id} from whitelist'
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Account {account_id} not found on whitelist'
        })


@admin_widget_bp.route('/status', methods=['GET'])
def get_status():
    """Get current admin status (requires auth)"""
    is_admin, error_response, status_code = check_admin_auth()
    if not is_admin:
        return error_response, status_code
    
    status = demo_mode.get_status()
    
    # Get usage stats
    total_usage = CultureSheetUsage.query.count()
    total_sheets = db.session.query(db.func.sum(CultureSheetUsage.sheets_generated)).scalar() or 0
    
    return jsonify({
        'demo_mode': status,
        'usage_stats': {
            'total_users': total_usage,
            'total_sheets': total_sheets
        }
    })
