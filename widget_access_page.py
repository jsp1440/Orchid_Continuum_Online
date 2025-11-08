"""
Simple access page for all widgets and features
"""

from flask import render_template_string
from app import app

@app.route('/widget-hub')
def widget_hub():
    """Central hub for accessing all widgets and features"""
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Widget Hub - The Orchid Continuum</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://unpkg.com/feather-icons"></script>
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            .hub-container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .hub-header {
                text-align: center;
                color: white;
                margin-bottom: 50px;
            }
            
            .hub-header h1 {
                font-size: 48px;
                margin-bottom: 10px;
            }
            
            .category {
                background: white;
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            }
            
            .category h2 {
                color: #667eea;
                margin-bottom: 20px;
                font-size: 28px;
            }
            
            .widget-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            
            .widget-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-decoration: none;
                transition: transform 0.2s, box-shadow 0.2s;
                display: block;
            }
            
            .widget-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(0,0,0,0.3);
                color: white;
            }
            
            .widget-card h3 {
                font-size: 20px;
                margin-bottom: 10px;
            }
            
            .widget-card p {
                font-size: 14px;
                opacity: 0.9;
                margin: 0;
            }
            
            .new-badge {
                background: #ff6b6b;
                color: white;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="hub-container">
            <div class="hub-header">
                <h1>🌸 Widget Hub</h1>
                <p>Access all Orchid Continuum features in one place</p>
            </div>
            
            <!-- NEW & INNOVATIVE -->
            <div class="category">
                <h2>🔥 New & Innovative</h2>
                <div class="widget-grid">
                    <a href="/widgets/orchid-match" class="widget-card">
                        <h3>Orchid Match <span class="new-badge">NEW!</span></h3>
                        <p>Tinder-style swipe to discover your perfect orchids</p>
                    </a>
                </div>
            </div>
            
            <!-- POPULAR WIDGETS -->
            <div class="category">
                <h2>⭐ Most Popular</h2>
                <div class="widget-grid">
                    <a href="/widget/orchid-of-the-day" class="widget-card">
                        <h3>Orchid of the Day</h3>
                        <p>Daily featured orchid with full details</p>
                    </a>
                    
                    <a href="/widgets/philosophy-quiz" class="widget-card">
                        <h3>Philosophy Quiz</h3>
                        <p>Test your orchid philosophy knowledge</p>
                    </a>
                    
                    <a href="/widgets/ai-orchid-health-diagnostic" class="widget-card">
                        <h3>AI Health Diagnostic</h3>
                        <p>Diagnose orchid health issues with AI</p>
                    </a>
                    
                    <a href="/widgets/gallery" class="widget-card">
                        <h3>Gallery Widget</h3>
                        <p>Browse 1,332 orchid images</p>
                    </a>
                </div>
            </div>
            
            <!-- ADMIN & CONTENT -->
            <div class="category">
                <h2>📝 Content Management</h2>
                <div class="widget-grid">
                    <a href="/admin/login" class="widget-card">
                        <h3>Admin Login</h3>
                        <p>Access admin dashboard and article editor</p>
                    </a>
                    
                    <a href="/articles-hub" class="widget-card">
                        <h3>Articles Hub</h3>
                        <p>Read featured orchid articles</p>
                    </a>
                    
                    <a href="/widgets/" class="widget-card">
                        <h3>Full Widget Dashboard</h3>
                        <p>See all 34+ widgets organized by category</p>
                    </a>
                </div>
            </div>
            
            <!-- ANALYSIS TOOLS -->
            <div class="category">
                <h2>🔬 Analysis & Research</h2>
                <div class="widget-grid">
                    <a href="/widgets/ai-breeder-pro" class="widget-card">
                        <h3>AI Breeder Pro</h3>
                        <p>Predict hybrid outcomes with AI</p>
                    </a>
                    
                    <a href="/widgets/climate" class="widget-card">
                        <h3>Climate Comparator</h3>
                        <p>Compare orchid habitat conditions</p>
                    </a>
                    
                    <a href="/widgets/growing-condition-matcher" class="widget-card">
                        <h3>Growing Matcher</h3>
                        <p>Find orchids for your conditions</p>
                    </a>
                </div>
            </div>
            
            <!-- GALLERIES -->
            <div class="category">
                <h2>🖼️ Themed Galleries</h2>
                <div class="widget-grid">
                    <a href="/widgets/thailand-gallery" class="widget-card">
                        <h3>Thailand Gallery</h3>
                        <p>Thai orchid collection</p>
                    </a>
                    
                    <a href="/widgets/madagascar-gallery" class="widget-card">
                        <h3>Madagascar Gallery</h3>
                        <p>Madagascar orchid collection</p>
                    </a>
                    
                    <a href="/widgets/central-america-gallery" class="widget-card">
                        <h3>Central America Gallery</h3>
                        <p>Central American orchids</p>
                    </a>
                </div>
            </div>
            
            <div class="text-center mt-5">
                <a href="/" class="btn btn-light btn-lg">← Back to Home</a>
            </div>
        </div>
        
        <script>
            feather.replace();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)
