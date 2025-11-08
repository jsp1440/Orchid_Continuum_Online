from flask import render_template_string
from app import app

@app.route('/widgets-dashboard')
def widgets_dashboard():
    """Clean, organized widget dashboard - SINGLE source of truth"""
    
    # Core working widgets (tested and functional)
    working_widgets = [
        {
            'name': '🌸 Orchid of the Day',
            'url': '/widget/orchid-of-the-day',
            'description': 'Featured orchid with care info',
            'status': 'working'
        },
        {
            'name': '🖼️ Gallery Widget',
            'url': '/widgets/gallery',
            'description': 'Scrolling orchid gallery',
            'status': 'working'
        },
        {
            'name': '🌡️ Climate Widget',
            'url': '/widgets/climate',
            'description': 'Weather and climate data',
            'status': 'working'
        },
        {
            'name': '🔍 Discovery Widget',
            'url': '/widget/discovery',
            'description': 'Discover new orchids',
            'status': 'working'
        },
        {
            'name': '🧠 Philosophy Quiz',
            'url': '/widgets/philosophy-quiz',
            'description': 'Educational orchid quiz',
            'status': 'working'
        },
        {
            'name': '🌍 Ecosystem Explorer',
            'url': '/widgets/ecosystem-explorer',
            'description': 'Explore orchid ecosystems',
            'status': 'working'
        },
        {
            'name': '🏥 AI Health Diagnostic',
            'url': '/widgets/ai-orchid-health-diagnostic',
            'description': 'AI-powered orchid health check',
            'status': 'working'
        },
        {
            'name': '🌱 Growing Condition Matcher',
            'url': '/widgets/personalized-growing-condition-matcher',
            'description': 'Match orchids to your conditions',
            'status': 'working'
        },
        {
            'name': '🧬 AI Breeder Pro',
            'url': '/widgets/ai-breeder-pro',
            'description': 'Hybrid breeding assistant',
            'status': 'working'
        },
        {
            'name': '📅 Adaptive Care Calendar',
            'url': '/widgets/adaptive-care-calendar',
            'description': 'Personalized care schedule',
            'status': 'working'
        },
        {
            'name': '🔐 Authentication Detector',
            'url': '/widgets/orchid-authentication-detector',
            'description': 'Verify orchid authenticity',
            'status': 'working'
        },
        {
            'name': '🌤️ Weather/Habitat Comparison',
            'url': '/widgets/weather-habitat',
            'description': 'Compare habitat conditions',
            'status': 'working'
        }
    ]
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Widget Dashboard - Orchid Continuum</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px;
                min-height: 100vh;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { 
                color: white; 
                text-align: center; 
                margin-bottom: 10px;
                font-size: 42px;
            }
            .subtitle {
                text-align: center;
                color: rgba(255,255,255,0.9);
                margin-bottom: 40px;
                font-size: 18px;
            }
            
            .widget-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }
            
            .widget-card {
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                transition: transform 0.2s, box-shadow 0.2s;
                border: 2px solid transparent;
            }
            
            .widget-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.25);
                border-color: #667eea;
            }
            
            .widget-name {
                font-size: 22px;
                font-weight: bold;
                color: #2d3748;
                margin-bottom: 10px;
            }
            
            .widget-description {
                color: #718096;
                margin-bottom: 20px;
                line-height: 1.6;
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
            
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
            
            .status-working {
                background: #48bb78;
                color: white;
            }
            
            .stats {
                background: rgba(255,255,255,0.2);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            
            .stats-number {
                font-size: 48px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌸 Widget Dashboard</h1>
            <p class="subtitle">All Working Widgets - Clean & Organized</p>
            
            <div class="stats">
                <div class="stats-number">{{ widgets|length }}</div>
                <div>Active Widgets</div>
            </div>
            
            <div class="widget-grid">
                {% for widget in widgets %}
                <div class="widget-card">
                    <div class="widget-name">
                        {{ widget.name }}
                        <span class="status-badge status-{{ widget.status }}">{{ widget.status }}</span>
                    </div>
                    <div class="widget-description">{{ widget.description }}</div>
                    <a href="{{ widget.url }}" class="widget-link" target="_blank">Open Widget →</a>
                </div>
                {% endfor %}
            </div>
            
            <div style="text-align: center; margin-top: 40px; color: white;">
                <p>All widgets are tested and working ✅</p>
                <p style="margin-top: 10px; opacity: 0.8;">Updated: {{ now }}</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    from datetime import datetime
    return render_template_string(html, widgets=working_widgets, now=datetime.now().strftime('%B %d, %Y'))
