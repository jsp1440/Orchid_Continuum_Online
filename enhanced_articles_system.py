from flask import render_template_string, request, jsonify, flash, redirect, url_for
from app import app, db
from models import OrchidRecord
import os
from datetime import datetime

# Available articles with metadata
ARTICLES = {
    'greek-mythology': {
        'title': 'Orchids and Greek Mythology: A Floral Odyssey',
        'file': 'static/articles/greek_mythology_orchids.txt',
        'category': 'Mythology & Culture',
        'description': 'Explore orchids named after Greek gods and heroes',
        'date': 'September 11, 2024',
        'read_time': '15 min'
    },
    'jewel-orchids': {
        'title': 'The Fascinating World of Jewel Orchids',
        'file': 'static/articles/jewel_orchids.txt',
        'category': 'Botanical Science',
        'description': 'Discover orchids valued for their stunning foliage',
        'date': 'September 11, 2024',
        'read_time': '12 min'
    },
    'literary-orchids': {
        'title': 'Famous Literary Works Featuring Orchids',
        'file': 'static/articles/literary_orchids.txt',
        'category': 'Literature & Culture',
        'description': 'Orchids in famous books and literature',
        'date': 'September 11, 2024',
        'read_time': '10 min'
    },
    'vanilla-story': {
        'title': 'The Boy Who Saved Vanilla',
        'file': 'static/articles/vanilla_boy_story.txt',
        'category': 'History & Innovation',
        'description': 'Story of Edmond Albius and vanilla pollination',
        'date': 'September 11, 2024',
        'read_time': '8 min'
    },
    'mythic-orchids': {
        'title': 'The Mythic Times and Orchids',
        'file': 'static/articles/mythic_orchids.txt',
        'category': 'Mythology & Culture',
        'description': 'Journey through mythical orchid connections',
        'date': 'September 11, 2024',
        'read_time': '18 min'
    },
    'august-care': {
        'title': 'Orchid Care Tips for August',
        'file': 'static/articles/august_orchid_care.txt',
        'category': 'Practical Guides',
        'description': 'Essential August care tips',
        'date': 'September 11, 2024',
        'read_time': '10 min'
    },
    'halloween-story': {
        'title': 'The Night of the Black Rot',
        'file': 'static/articles/halloween_black_rot.txt',
        'category': 'Seasonal Stories',
        'description': 'A spooky Halloween orchid tale',
        'date': 'September 11, 2024',
        'read_time': '12 min'
    },
    'mars-terraforming': {
        'title': 'Mars Orchids: Terraforming Dreams',
        'file': 'static/articles/mars_orchids_terraforming.txt',
        'category': 'Science Fiction',
        'description': 'Orchids in space colonization',
        'date': 'September 11, 2024',
        'read_time': '15 min'
    }
}

@app.route('/articles-hub')
def articles_hub():
    """Main articles hub with all articles"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orchid Articles - Orchid Continuum</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Georgia', serif;
                background: #f9f9f9;
                padding: 40px 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { 
                color: #2c5f2d; 
                margin-bottom: 10px;
                font-size: 42px;
            }
            .subtitle { 
                color: #666; 
                margin-bottom: 40px;
                font-size: 18px;
            }
            
            .articles-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 30px;
            }
            
            .article-card {
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 15px rgba(0,0,0,0.1);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .article-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 6px 25px rgba(0,0,0,0.15);
            }
            
            .article-header {
                padding: 25px;
                border-bottom: 1px solid #eee;
            }
            
            .article-category {
                display: inline-block;
                padding: 5px 12px;
                background: #2c5f2d;
                color: white;
                font-size: 12px;
                border-radius: 15px;
                margin-bottom: 15px;
            }
            
            .article-title {
                font-size: 22px;
                color: #2c5f2d;
                margin-bottom: 10px;
                line-height: 1.3;
            }
            
            .article-description {
                color: #666;
                line-height: 1.6;
                margin-bottom: 15px;
            }
            
            .article-meta {
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                color: #999;
            }
            
            .article-actions {
                padding: 20px 25px;
                background: #f9f9f9;
                display: flex;
                gap: 10px;
            }
            
            .btn {
                padding: 10px 20px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: 500;
                transition: opacity 0.2s;
            }
            
            .btn-primary {
                background: #2c5f2d;
                color: white;
            }
            
            .btn-secondary {
                background: #e0e0e0;
                color: #333;
            }
            
            .btn:hover { opacity: 0.9; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Orchid Articles</h1>
            <p class="subtitle">Stories, science, and culture from the world of orchids</p>
            
            <div class="articles-grid">
                {% for key, article in articles.items() %}
                <div class="article-card">
                    <div class="article-header">
                        <div class="article-category">{{ article.category }}</div>
                        <div class="article-title">{{ article.title }}</div>
                        <div class="article-description">{{ article.description }}</div>
                        <div class="article-meta">
                            <span>{{ article.date }}</span>
                            <span>{{ article.read_time }}</span>
                        </div>
                    </div>
                    <div class="article-actions">
                        <a href="/article/{{ key }}" class="btn btn-primary">Read Article</a>
                        <a href="/article/{{ key }}/share" class="btn btn-secondary">Share</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, articles=ARTICLES)

@app.route('/article/<article_id>')
def view_article(article_id):
    """View individual article with formatting"""
    # Try to find article by ID first
    if article_id in ARTICLES:
        article = ARTICLES[article_id]
        with open(article['file'], 'r') as f:
            content = f.read()
    else:
        # Try direct filename
        filepath = os.path.join('static/articles', f"{article_id}.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            article = {
                'title': article_id.replace('_', ' ').title(),
                'category': 'Article',
                'date': datetime.now().strftime('%B %d, %Y'),
                'read_time': '10 min'
            }
        else:
            flash('Article not found', 'error')
            return redirect(url_for('articles_hub'))
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ article.title }} - Orchid Continuum</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Georgia', serif;
                background: #fff;
                color: #333;
                line-height: 1.8;
            }
            
            .article-header {
                background: linear-gradient(135deg, #2c5f2d, #4a8b4f);
                color: white;
                padding: 60px 20px;
                text-align: center;
            }
            
            .article-category {
                display: inline-block;
                padding: 5px 15px;
                background: rgba(255,255,255,0.2);
                border-radius: 20px;
                font-size: 14px;
                margin-bottom: 15px;
            }
            
            .article-title {
                font-size: 48px;
                margin-bottom: 15px;
            }
            
            .article-meta {
                font-size: 16px;
                opacity: 0.9;
            }
            
            .article-content {
                max-width: 800px;
                margin: 60px auto;
                padding: 0 20px;
                font-size: 18px;
            }
            
            .article-content p {
                margin-bottom: 20px;
            }
            
            .share-buttons {
                margin: 40px 0;
                padding: 30px;
                background: #f9f9f9;
                border-radius: 12px;
                text-align: center;
            }
            
            .share-btn {
                display: inline-block;
                margin: 0 10px;
                padding: 12px 24px;
                background: #2c5f2d;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 16px;
            }
            
            .back-link {
                display: inline-block;
                margin: 20px 0;
                color: #2c5f2d;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="article-header">
            <div class="article-category">{{ article.category }}</div>
            <h1 class="article-title">{{ article.title }}</h1>
            <div class="article-meta">{{ article.date }} · {{ article.read_time }} read</div>
        </div>
        
        <div class="article-content">
            <a href="/articles-hub" class="back-link">← Back to Articles</a>
            
            <div style="white-space: pre-wrap;">{{ content }}</div>
            
            <div class="share-buttons">
                <h3 style="margin-bottom: 20px;">Share This Article</h3>
                <a href="mailto:?subject={{ article.title }}&body=Check out this article: {{ url }}" class="share-btn">📧 Email</a>
                <a href="#" onclick="copyLink()" class="share-btn">🔗 Copy Link</a>
                <a href="/article/{{ article_id }}/download" class="share-btn">⬇️ Download PDF</a>
            </div>
        </div>
        
        <script>
        function copyLink() {
            navigator.clipboard.writeText(window.location.href);
            alert('Link copied to clipboard!');
        }
        </script>
    </body>
    </html>
    '''
    
    url = request.url
    return render_template_string(html, article=article, content=content, article_id=article_id, url=url)

@app.route('/article/<article_id>/share')
def share_article(article_id):
    """Share article - generates shareable link"""
    if article_id not in ARTICLES:
        return jsonify({'error': 'Article not found'}), 404
    
    article = ARTICLES[article_id]
    share_url = url_for('view_article', article_id=article_id, _external=True)
    
    return jsonify({
        'title': article['title'],
        'url': share_url,
        'description': article['description'],
        'email_subject': f"Check out: {article['title']}",
        'email_body': f"I thought you'd enjoy this article:\\n\\n{article['title']}\\n{article['description']}\\n\\n{share_url}"
    })
