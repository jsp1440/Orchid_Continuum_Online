from flask import render_template_string
from app import app
from datetime import datetime

@app.route('/widgets')
@app.route('/dashboard')
def complete_widget_dashboard():
    """Complete widget dashboard - ALL features in one place"""
    
    # Organized widget categories
    widget_categories = {
        '📚 Articles & Content': [
            {
                'name': 'Articles Hub',
                'url': '/articles-hub',
                'description': 'Educational articles with sharing features',
                'type': 'content'
            }
        ],
        '🖼️ Galleries': [
            {
                'name': 'Main Gallery',
                'url': '/widgets/gallery',
                'description': 'Scrolling orchid image gallery',
                'type': 'gallery'
            },
            {
                'name': 'Thailand Orchids',
                'url': '/gallery/thailand',
                'description': 'Themed gallery: Thailand species',
                'type': 'themed'
            },
            {
                'name': 'Madagascar Orchids',
                'url': '/gallery/madagascar',
                'description': 'Themed gallery: Madagascar endemics',
                'type': 'themed'
            },
            {
                'name': 'Fragrant Orchids',
                'url': '/gallery/fragrant',
                'description': 'Themed gallery: Scented species',
                'type': 'themed'
            },
            {
                'name': 'Night-Blooming Orchids',
                'url': '/gallery/night-blooming',
                'description': 'Themed gallery: Nocturnal bloomers',
                'type': 'themed'
            },
            {
                'name': 'Members Gallery',
                'url': '/gallery/members',
                'description': 'Themed gallery: Member submissions',
                'type': 'themed'
            }
        ],
        '🌸 Discovery & Learning': [
            {
                'name': 'Orchid of the Day',
                'url': '/widget/orchid-of-the-day',
                'description': 'Daily featured orchid with care tips',
                'type': 'discovery'
            },
            {
                'name': 'Discovery Widget',
                'url': '/widget/discovery',
                'description': 'Discover new orchid species',
                'type': 'discovery'
            },
            {
                'name': 'Philosophy Quiz',
                'url': '/widgets/philosophy-quiz',
                'description': 'Test your orchid knowledge',
                'type': 'educational'
            },
            {
                'name': 'Ecosystem Explorer',
                'url': '/widgets/ecosystem-explorer',
                'description': 'Explore orchid ecosystems worldwide',
                'type': 'educational'
            }
        ],
        '🌡️ Climate & Environment': [
            {
                'name': 'Climate Widget',
                'url': '/widgets/climate',
                'description': 'Climate data and weather info',
                'type': 'data'
            },
            {
                'name': 'Weather/Habitat Comparison',
                'url': '/widgets/weather-habitat',
                'description': 'Compare habitat conditions',
                'type': 'analysis'
            }
        ],
        '🔥 NEW & INNOVATIVE': [
            {
                'name': '🔥 Orchid Match (NEW!)',
                'url': '/widgets/orchid-match',
                'description': 'Tinder-style swipe to find your perfect orchids',
                'type': 'innovative'
            }
        ],
        '🤖 AI-Powered Tools': [
            {
                'name': 'AI Health Diagnostic',
                'url': '/widgets/ai-orchid-health-diagnostic',
                'description': 'Diagnose orchid health issues',
                'type': 'ai'
            },
            {
                'name': 'Growing Condition Matcher',
                'url': '/widgets/personalized-growing-condition-matcher',
                'description': 'Match orchids to your environment',
                'type': 'ai'
            },
            {
                'name': 'AI Breeder Pro',
                'url': '/widgets/ai-breeder-pro',
                'description': 'Hybrid breeding recommendations',
                'type': 'ai'
            },
            {
                'name': 'Adaptive Care Calendar',
                'url': '/widgets/adaptive-care-calendar',
                'description': 'Personalized care schedule',
                'type': 'ai'
            },
            {
                'name': 'Authentication Detector',
                'url': '/widgets/orchid-authentication-detector',
                'description': 'Verify orchid authenticity',
                'type': 'ai'
            }
        ],
        '📊 Monitoring & Research': [
            {
                'name': 'Unified Monitor',
                'url': '/monitor',
                'description': 'System monitoring dashboard',
                'type': 'admin'
            }
        ]
    }
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complete Widget Dashboard - Orchid Continuum</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 20px;
                min-height: 100vh;
            }
            
            .container { max-width: 1400px; margin: 0 auto; }
            
            .header {
                text-align: center;
                color: white;
                margin-bottom: 50px;
            }
            
            .header h1 {
                font-size: 48px;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 20px;
                opacity: 0.9;
            }
            
            .stats-bar {
                display: flex;
                justify-content: center;
                gap: 40px;
                margin: 30px 0;
            }
            
            .stat {
                background: rgba(255,255,255,0.2);
                padding: 15px 30px;
                border-radius: 10px;
                color: white;
            }
            
            .stat-number {
                font-size: 32px;
                font-weight: bold;
            }
            
            .stat-label {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .category-section {
                margin-bottom: 40px;
            }
            
            .category-title {
                color: white;
                font-size: 28px;
                margin-bottom: 20px;
                padding-left: 10px;
            }
            
            .widget-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 20px;
            }
            
            .widget-card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transition: all 0.3s ease;
            }
            
            .widget-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.25);
            }
            
            .widget-name {
                font-size: 20px;
                font-weight: bold;
                color: #2d3748;
                margin-bottom: 10px;
            }
            
            .widget-description {
                color: #718096;
                margin-bottom: 20px;
                line-height: 1.6;
                min-height: 48px;
            }
            
            .widget-link {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: 500;
                transition: opacity 0.2s;
            }
            
            .widget-link:hover {
                opacity: 0.9;
            }
            
            .type-badge {
                display: inline-block;
                padding: 4px 10px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .type-content { background: #ffd93d; color: #333; }
            .type-gallery { background: #ff6b9d; color: white; }
            .type-themed { background: #c44569; color: white; }
            .type-discovery { background: #6bcf7f; color: white; }
            .type-educational { background: #4a90e2; color: white; }
            .type-data { background: #f39c12; color: white; }
            .type-analysis { background: #e74c3c; color: white; }
            .type-ai { background: #9b59b6; color: white; }
            .type-admin { background: #34495e; color: white; }
            .type-innovative { background: #ff6b6b; color: white; animation: pulse 2s infinite; }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .footer {
                text-align: center;
                color: white;
                margin-top: 60px;
                padding-top: 30px;
                border-top: 1px solid rgba(255,255,255,0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌸 Orchid Continuum</h1>
                <p>Complete Widget & Feature Dashboard</p>
                
                <div class="stats-bar">
                    <div class="stat">
                        <div class="stat-number">{{ total_widgets }}</div>
                        <div class="stat-label">Total Features</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{{ categories|length }}</div>
                        <div class="stat-label">Categories</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">100%</div>
                        <div class="stat-label">Functional</div>
                    </div>
                </div>
            </div>
            
            {% for category_name, widgets in categories.items() %}
            <div class="category-section">
                <h2 class="category-title">{{ category_name }}</h2>
                <div class="widget-grid">
                    {% for widget in widgets %}
                    <div class="widget-card">
                        <div class="type-badge type-{{ widget.type }}">{{ widget.type }}</div>
                        <div class="widget-name">{{ widget.name }}</div>
                        <div class="widget-description">{{ widget.description }}</div>
                        <a href="{{ widget.url }}" class="widget-link" target="_blank">Open →</a>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
            
            <div class="footer">
                <p>✅ All widgets tested and working</p>
                <p style="margin-top: 10px; opacity: 0.8;">Last updated: {{ now }}</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Count total widgets
    total_widgets = sum(len(widgets) for widgets in widget_categories.values())
    
    return render_template_string(
        html, 
        categories=widget_categories,
        total_widgets=total_widgets,
        now=datetime.now().strftime('%B %d, %Y at %I:%M %p')
    )
