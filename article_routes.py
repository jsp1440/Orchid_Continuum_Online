"""
Featured Articles System - API Routes
"""

from flask import Blueprint, request, jsonify, render_template, send_file, session
from werkzeug.utils import secure_filename
from app import db
from models import (
    Author, Asset, Article, ArticleAsset, Submission,
    ArticleStatus, AssetKind, AssetPlacement, SubmissionStatus
)
from article_utils import render_markdown_to_html, generate_excerpt_from_markdown
from datetime import datetime
import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# Create blueprint
articles_bp = Blueprint('articles', __name__)

# Admin check decorator (uses existing session-based auth)
def require_admin(f):
    """Decorator to require admin access via session authentication"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated via admin session
        if not session.get('admin_authenticated'):
            return jsonify({
                'error': 'Admin authentication required',
                'message': 'Please log in at /admin/login first'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# ASSET UPLOAD
# ============================================================================

@articles_bp.route('/api/assets', methods=['POST'])
@require_admin
def upload_asset():
    """Upload an image or file asset"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate MIME type
    allowed_mimes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_mimes:
        return jsonify({'error': 'Invalid file type. Only images allowed.'}), 400
    
    # Validate file size (10MB max)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    if file_size > 10 * 1024 * 1024:  # 10MB
        return jsonify({'error': 'File too large. Max 10MB.'}), 400
    
    # Secure filename
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    
    # Save to static/uploads/articles
    upload_dir = os.path.join('static', 'uploads', 'articles')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    # Get image dimensions
    width, height = None, None
    try:
        with Image.open(filepath) as img:
            width, height = img.size
    except:
        pass
    
    # Create asset record
    asset = Asset(
        kind=AssetKind.IMAGE,
        filename=filename,
        mime_type=file.content_type,
        width=width,
        height=height,
        alt_text=request.form.get('alt_text'),
        credit=request.form.get('credit'),
        storage_url=f'/{filepath}'
    )
    
    db.session.add(asset)
    db.session.commit()
    
    logger.info(f"Asset uploaded: {filename} (ID: {asset.id})")
    return jsonify(asset.to_dict()), 201

# ============================================================================
# AUTHORS
# ============================================================================

@articles_bp.route('/api/authors', methods=['GET'])
def list_authors():
    """List all authors for dropdowns"""
    authors = Author.query.order_by(Author.display_name).all()
    return jsonify([author.to_dict() for author in authors])

@articles_bp.route('/api/authors', methods=['POST'])
@require_admin
def create_author():
    """Create a new author"""
    data = request.json
    
    if not data.get('display_name'):
        return jsonify({'error': 'display_name is required'}), 400
    
    author = Author(
        display_name=data['display_name'],
        email=data.get('email'),
        bio=data.get('bio'),
        website_url=data.get('website_url')
    )
    
    db.session.add(author)
    db.session.commit()
    
    logger.info(f"Author created: {author.display_name} (ID: {author.id})")
    return jsonify(author.to_dict()), 201

# ============================================================================
# ARTICLES
# ============================================================================

@articles_bp.route('/api/articles', methods=['POST'])
@require_admin
def create_article():
    """Create a new article"""
    data = request.json
    
    # Validate required fields
    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400
    if not data.get('author_id'):
        return jsonify({'error': 'author_id is required'}), 400
    if not data.get('content_markdown'):
        return jsonify({'error': 'content_markdown is required'}), 400
    
    # Generate slug
    slug = Article.generate_slug(data['title'])
    
    # Render markdown to HTML
    content_html = render_markdown_to_html(data['content_markdown'])
    
    # Generate excerpt if not provided
    excerpt = data.get('excerpt') or generate_excerpt_from_markdown(data['content_markdown'])
    
    # Create article
    article = Article(
        slug=slug,
        title=data['title'],
        subtitle=data.get('subtitle'),
        excerpt=excerpt,
        content_markdown=data['content_markdown'],
        content_html=content_html,
        status=ArticleStatus.DRAFT,
        featured=data.get('featured', False),
        hero_image_id=data.get('hero_image_id'),
        author_id=data['author_id'],
        tags=data.get('tags', [])
    )
    
    db.session.add(article)
    db.session.commit()
    
    logger.info(f"Article created: {article.title} (ID: {article.id}, slug: {article.slug})")
    return jsonify(article.to_dict(include_content=True)), 201

@articles_bp.route('/api/articles/<int:article_id>', methods=['PUT'])
@require_admin
def update_article(article_id):
    """Update an existing article"""
    article = Article.query.get_or_404(article_id)
    data = request.json
    
    # Update fields
    if 'title' in data:
        article.title = data['title']
        # Regenerate slug if title changed
        if data.get('regenerate_slug', False):
            article.slug = Article.generate_slug(data['title'], article.id)
    
    if 'subtitle' in data:
        article.subtitle = data['subtitle']
    if 'excerpt' in data:
        article.excerpt = data['excerpt']
    if 'featured' in data:
        article.featured = data['featured']
    if 'hero_image_id' in data:
        article.hero_image_id = data['hero_image_id']
    if 'tags' in data:
        article.tags = data['tags']
    
    # Update content and re-render if changed
    if 'content_markdown' in data:
        article.content_markdown = data['content_markdown']
        article.content_html = render_markdown_to_html(data['content_markdown'])
        
        # Regenerate excerpt if not explicitly provided
        if 'excerpt' not in data:
            article.excerpt = generate_excerpt_from_markdown(data['content_markdown'])
    
    article.updated_at = datetime.utcnow()
    db.session.commit()
    
    logger.info(f"Article updated: {article.title} (ID: {article.id})")
    return jsonify(article.to_dict(include_content=True))

@articles_bp.route('/api/articles/<int:article_id>/submit', methods=['POST'])
@require_admin
def submit_article_for_review(article_id):
    """Submit article for review"""
    article = Article.query.get_or_404(article_id)
    article.status = ArticleStatus.PENDING_REVIEW
    article.updated_at = datetime.utcnow()
    db.session.commit()
    
    logger.info(f"Article submitted for review: {article.title} (ID: {article.id})")
    return jsonify(article.to_dict())

@articles_bp.route('/api/articles/<int:article_id>/publish', methods=['POST'])
@require_admin
def publish_article(article_id):
    """Publish an article"""
    article = Article.query.get_or_404(article_id)
    article.status = ArticleStatus.PUBLISHED
    article.published_at = datetime.utcnow()
    article.updated_at = datetime.utcnow()
    db.session.commit()
    
    logger.info(f"Article published: {article.title} (ID: {article.id})")
    return jsonify(article.to_dict())

@articles_bp.route('/api/articles/<int:article_id>/assets', methods=['POST'])
@require_admin
def attach_asset_to_article(article_id):
    """Attach an asset to an article"""
    article = Article.query.get_or_404(article_id)
    data = request.json
    
    if not data.get('asset_id'):
        return jsonify({'error': 'asset_id is required'}), 400
    
    # Check if asset exists
    asset = Asset.query.get(data['asset_id'])
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Create article-asset link
    article_asset = ArticleAsset(
        article_id=article_id,
        asset_id=data['asset_id'],
        placement=AssetPlacement[data.get('placement', 'INLINE').upper()],
        block_anchor=data.get('block_anchor'),
        caption=data.get('caption'),
        order_index=data.get('order_index', 0)
    )
    
    db.session.add(article_asset)
    db.session.commit()
    
    logger.info(f"Asset {data['asset_id']} attached to article {article_id}")
    return jsonify(article_asset.to_dict()), 201

# ============================================================================
# FEATURED FEED (PUBLIC)
# ============================================================================

@articles_bp.route('/api/articles/featured', methods=['GET'])
def get_featured_articles():
    """Get featured articles for widget (public endpoint)"""
    limit = int(request.args.get('limit', 8))
    
    # Only return published, featured articles
    articles = Article.query.filter_by(
        status=ArticleStatus.PUBLISHED,
        featured=True
    ).order_by(Article.published_at.desc()).limit(limit).all()
    
    result = []
    for article in articles:
        card_data = {
            'id': article.id,
            'slug': article.slug,
            'title': article.title,
            'excerpt': article.excerpt,
            'author': {'name': article.author.display_name} if article.author else None,
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'tags': article.tags or []
        }
        
        if article.hero_image:
            card_data['hero_image'] = {
                'url': article.hero_image.storage_url,
                'alt': article.hero_image.alt_text or article.title
            }
        
        if article.youtube_url:
            card_data['youtube_url'] = article.youtube_url
        
        result.append(card_data)
    
    return jsonify(result)

# ============================================================================
# SUBMISSIONS (PUBLIC)
# ============================================================================

@articles_bp.route('/api/submissions', methods=['POST'])
def create_submission():
    """Public submission endpoint"""
    data = request.json
    
    # Validate required fields
    if not data.get('submitter_name'):
        return jsonify({'error': 'submitter_name is required'}), 400
    if not data.get('submitter_email'):
        return jsonify({'error': 'submitter_email is required'}), 400
    if not data.get('proposed_title'):
        return jsonify({'error': 'proposed_title is required'}), 400
    if not data.get('proposed_markdown'):
        return jsonify({'error': 'proposed_markdown is required'}), 400
    
    # Create submission
    submission = Submission(
        submitter_name=data['submitter_name'],
        submitter_email=data['submitter_email'],
        proposed_title=data['proposed_title'],
        proposed_excerpt=data.get('proposed_excerpt'),
        proposed_markdown=data['proposed_markdown'],
        linked_asset_ids=data.get('linked_asset_ids', []),
        status=SubmissionStatus.RECEIVED
    )
    
    db.session.add(submission)
    db.session.commit()
    
    logger.info(f"Submission received: {submission.proposed_title} from {submission.submitter_email}")
    return jsonify(submission.to_dict()), 201

@articles_bp.route('/api/submissions/<int:submission_id>/approve', methods=['POST'])
@require_admin
def approve_submission(submission_id):
    """Approve a submission and convert to article"""
    submission = Submission.query.get_or_404(submission_id)
    data = request.json
    
    # Get or create default author for submissions
    author_id = data.get('author_id')
    if not author_id:
        # Use submitter as author
        author = Author.query.filter_by(email=submission.submitter_email).first()
        if not author:
            author = Author(
                display_name=submission.submitter_name,
                email=submission.submitter_email
            )
            db.session.add(author)
            db.session.flush()
        author_id = author.id
    
    # Create article from submission
    slug = Article.generate_slug(submission.proposed_title)
    content_html = render_markdown_to_html(submission.proposed_markdown)
    excerpt = submission.proposed_excerpt or generate_excerpt_from_markdown(submission.proposed_markdown)
    
    article = Article(
        slug=slug,
        title=submission.proposed_title,
        excerpt=excerpt,
        content_markdown=submission.proposed_markdown,
        content_html=content_html,
        status=ArticleStatus.PENDING_REVIEW,
        author_id=author_id
    )
    
    db.session.add(article)
    submission.status = SubmissionStatus.APPROVED
    submission.updated_at = datetime.utcnow()
    db.session.commit()
    
    logger.info(f"Submission {submission_id} approved, created article {article.id}")
    return jsonify({'article': article.to_dict(), 'submission': submission.to_dict()})

# ============================================================================
# ARTICLE PAGES
# ============================================================================

@articles_bp.route('/articles/<slug>')
def view_article(slug):
    """View a published article"""
    article = Article.query.filter_by(slug=slug, status=ArticleStatus.PUBLISHED).first_or_404()
    
    # Check for print mode
    print_mode = request.args.get('print') == '1'
    
    return render_template(
        'articles/article_detail.html',
        article=article,
        print_mode=print_mode
    )

@articles_bp.route('/widgets/featured-articles')
def featured_articles_widget():
    """Standalone widget page for embedding"""
    return render_template('widgets/featured_articles_widget.html')

@articles_bp.route('/admin/articles')
@require_admin
def admin_articles():
    """Admin interface for managing articles"""
    return render_template('articles/admin_articles.html')

@articles_bp.route('/api/articles/all', methods=['GET'])
@require_admin
def list_all_articles():
    """List all articles for admin (includes drafts)"""
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return jsonify([article.to_dict() for article in articles])
