"""
Platform Template Routes - Widget Container Pages
NO Famous AI footer - Clean, cloneable templates for multiple widget pages
"""

from flask import Blueprint, render_template, request
from models import db

platform_bp = Blueprint('platform', __name__, url_prefix='/platform')

@platform_bp.route('/')
@platform_bp.route('/home')
def platform_home():
    """
    Main platform homepage - landing page widget
    """
    landing_html = render_template('landing_widget.html')
    
    return render_template('platform_template.html',
                         page_title='The Orchid Continuum',
                         page_subtitle='Your comprehensive digital platform for orchid research and education',
                         widget_hero=landing_html)

@platform_bp.route('/judge')
def platform_judge():
    """
    FCOS Judge widget page
    """
    # Import judge widget content (will integrate actual widget later)
    return render_template('platform_template.html',
                         page_title='FCOS Orchid Judge',
                         page_subtitle='Educational mobile-first orchid judging tool',
                         widget_hero=None,  # Will add actual FCOS Judge widget
                         widget_primary='<h3>FCOS Judge Widget</h3><p>Judge widget will be embedded here</p>')

@platform_bp.route('/gallery')
def platform_gallery():
    """
    Gallery widget page
    """
    return render_template('platform_template.html',
                         page_title='Orchid Gallery',
                         page_subtitle='Browse our collection of orchid images',
                         widget_hero='<h2>Gallery Hub</h2>',
                         widget_primary='<h3>Themed Galleries</h3>')

@platform_bp.route('/games')
def platform_games():
    """
    Games widget page - Mahjong game
    """
    mahjong_html = render_template('mahjong_widget.html')
    
    return render_template('platform_template.html',
                         page_title='Orchid Mahjong',
                         page_subtitle='Match orchid tiles in this relaxing puzzle game',
                         widget_hero=mahjong_html)

@platform_bp.route('/stories')
def platform_stories():
    """
    Lore & Life widget page - stories and community content
    """
    lore_html = render_template('lore_widget.html')
    
    return render_template('platform_template.html',
                         page_title='Orchid Lore & Life',
                         page_subtitle='Discover the fascinating stories, legends, and cultural history of orchids',
                         widget_hero=lore_html)

@platform_bp.route('/trivia')
def platform_trivia():
    """
    Trivia widget page
    """
    # Load trivia widget template
    trivia_html = render_template('trivia_widget.html')
    
    return render_template('platform_template.html',
                         page_title='Orchid Trivia Challenge',
                         page_subtitle='Test your orchid knowledge with fascinating facts!',
                         widget_hero=trivia_html)

@platform_bp.route('/photo-studio')
def platform_photo_studio():
    """
    Photo editing widget page
    """
    photo_studio_html = render_template('photo_studio_widget.html')
    
    return render_template('platform_template.html',
                         page_title='Orchid Photo Studio',
                         page_subtitle='Edit, style, and share your orchid photos',
                         widget_hero=photo_studio_html)

@platform_bp.route('/journal')
def platform_journal():
    """
    My Orchid Collection journal widget page
    """
    journal_html = render_template('journal_widget.html')
    
    return render_template('platform_template.html',
                         page_title='My Orchid Collection',
                         page_subtitle='Track your orchids, log care activities, and celebrate blooms',
                         widget_hero=journal_html)

@platform_bp.route('/custom/<page_name>')
def platform_custom(page_name):
    """
    Custom platform page - allows creating new pages on the fly
    Usage: /platform/custom/my-page-name
    """
    return render_template('platform_template.html',
                         page_title=page_name.replace('-', ' ').title(),
                         page_subtitle='Custom widget page')

# Widget embedding demo route
@platform_bp.route('/demo')
def platform_demo():
    """
    Demo page showing all widget slot options
    """
    demo_widget = '<div style="background: rgba(139, 92, 246, 0.1); padding: 1rem; border-radius: 8px; text-align: center;"><strong>Demo Widget</strong><p>This shows widget slot placement</p></div>'
    
    return render_template('platform_template.html',
                         page_title='Platform Demo',
                         page_subtitle='All widget slots demonstrated',
                         widget_hero=demo_widget.replace('Demo Widget', 'Hero Widget - Full Width'),
                         widget_primary=demo_widget.replace('Demo Widget', 'Primary Widget - 2/3 Width'),
                         widget_sidebar=demo_widget.replace('Demo Widget', 'Sidebar Widget - 1/3 Width'),
                         widget_feature1=demo_widget.replace('Demo Widget', 'Feature 1 - 1/3 Width'),
                         widget_feature2=demo_widget.replace('Demo Widget', 'Feature 2 - 1/3 Width'),
                         widget_feature3=demo_widget.replace('Demo Widget', 'Feature 3 - 1/3 Width'),
                         widget_footer_left=demo_widget.replace('Demo Widget', 'Footer Left - 1/2 Width'),
                         widget_footer_right=demo_widget.replace('Demo Widget', 'Footer Right - 1/2 Width'),
                         widget_bottom=demo_widget.replace('Demo Widget', 'Bottom Widget - Full Width'))
