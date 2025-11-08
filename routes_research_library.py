"""
Research Library Routes - Browse and search catalogued research documents
"""
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import or_, and_
import logging

research_library_bp = Blueprint('research_library', __name__)
logger = logging.getLogger(__name__)

@research_library_bp.route('/research-library')
def research_library():
    """Main research library page with document catalog"""
    from models import ResearchDocument
    
    # Get search parameters
    search_query = request.args.get('q', '').strip()
    genus_filter = request.args.get('genus', '').strip()
    theme_filter = request.args.get('theme', '').strip()
    year_filter = request.args.get('year', type=int)
    
    # Base query
    query = ResearchDocument.query
    
    # Apply filters
    if search_query:
        query = query.filter(
            or_(
                ResearchDocument.title.ilike(f'%{search_query}%'),
                ResearchDocument.author.ilike(f'%{search_query}%'),
                ResearchDocument.abstract.ilike(f'%{search_query}%')
            )
        )
    
    if genus_filter:
        query = query.filter(
            ResearchDocument.genera_covered.contains([genus_filter])
        )
    
    if theme_filter:
        query = query.filter(
            ResearchDocument.themes.contains([theme_filter])
        )
    
    if year_filter:
        query = query.filter(ResearchDocument.year == year_filter)
    
    # Execute query
    documents = query.order_by(ResearchDocument.year.desc()).all()
    
    # Get all unique genera and themes for filters
    all_docs = ResearchDocument.query.all()
    all_genera = set()
    all_themes = set()
    
    for doc in all_docs:
        if doc.genera_covered:
            all_genera.update(doc.genera_covered)
        if doc.themes:
            all_themes.update(doc.themes)
    
    return render_template(
        'research_library.html',
        documents=documents,
        search_query=search_query,
        genus_filter=genus_filter,
        theme_filter=theme_filter,
        year_filter=year_filter,
        all_genera=sorted(all_genera),
        all_themes=sorted(all_themes),
        total_documents=ResearchDocument.query.count()
    )

@research_library_bp.route('/research-document/<int:doc_id>')
def view_document(doc_id):
    """View detailed information about a research document"""
    from models import ResearchDocument, DocumentTopic, GenusKnowledgeCard
    
    document = ResearchDocument.query.get_or_404(doc_id)
    
    # Get all topics for this document
    topics = DocumentTopic.query.filter_by(document_id=doc_id).all()
    
    # Get all knowledge cards for this document
    knowledge_cards = GenusKnowledgeCard.query.filter_by(document_id=doc_id).all()
    
    # Organize topics by type
    topics_by_type = {}
    for topic in topics:
        if topic.topic_type not in topics_by_type:
            topics_by_type[topic.topic_type] = []
        topics_by_type[topic.topic_type].append(topic)
    
    # Increment view count
    document.view_count += 1
    from app import db
    db.session.commit()
    
    return render_template(
        'research_document_detail.html',
        document=document,
        topics_by_type=topics_by_type,
        knowledge_cards=knowledge_cards
    )

@research_library_bp.route('/genus-knowledge/<genus>')
def genus_knowledge(genus):
    """View all knowledge cards for a specific genus across all documents"""
    from models import GenusKnowledgeCard, ResearchDocument, OrchidRecord
    
    knowledge_cards = GenusKnowledgeCard.query.filter_by(genus=genus).all()
    
    if not knowledge_cards:
        # Check if we have orchids of this genus in the database
        orchid_count = OrchidRecord.query.filter_by(genus=genus).count()
        return render_template(
            'genus_knowledge.html',
            genus=genus,
            knowledge_cards=[],
            orchid_count=orchid_count,
            has_orchids=orchid_count > 0
        )
    
    # Get all documents referenced
    doc_ids = [card.document_id for card in knowledge_cards]
    documents = {doc.id: doc for doc in ResearchDocument.query.filter(
        ResearchDocument.id.in_(doc_ids)
    ).all()}
    
    # Count orchids of this genus
    orchid_count = OrchidRecord.query.filter_by(genus=genus).count()
    
    return render_template(
        'genus_knowledge.html',
        genus=genus,
        knowledge_cards=knowledge_cards,
        documents=documents,
        orchid_count=orchid_count,
        has_orchids=orchid_count > 0
    )

@research_library_bp.route('/api/search-topics')
def search_topics():
    """API endpoint to search document topics"""
    from models import DocumentTopic
    
    query = request.args.get('q', '').strip()
    topic_type = request.args.get('type', '').strip()
    genus = request.args.get('genus', '').strip()
    
    if not query and not topic_type and not genus:
        return jsonify({'error': 'No search criteria provided'}), 400
    
    # Build query
    topic_query = DocumentTopic.query
    
    if query:
        topic_query = topic_query.filter(
            or_(
                DocumentTopic.topic_name.ilike(f'%{query}%'),
                DocumentTopic.description.ilike(f'%{query}%')
            )
        )
    
    if topic_type:
        topic_query = topic_query.filter(DocumentTopic.topic_type == topic_type)
    
    if genus:
        topic_query = topic_query.filter(DocumentTopic.genus == genus)
    
    topics = topic_query.order_by(DocumentTopic.relevance_score.desc()).limit(50).all()
    
    return jsonify({
        'count': len(topics),
        'topics': [topic.to_dict() for topic in topics]
    })

@research_library_bp.route('/api/genus-search')
def genus_search():
    """API endpoint for genus autocomplete search"""
    from models import GenusKnowledgeCard
    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'genera': []})
    
    # Get genera from knowledge cards
    knowledge_genera = GenusKnowledgeCard.query.filter(
        GenusKnowledgeCard.genus.ilike(f'{query}%')
    ).with_entities(GenusKnowledgeCard.genus).distinct().limit(10).all()
    
    genera_list = [g[0] for g in knowledge_genera]
    
    return jsonify({'genera': genera_list})

# Register the blueprint
def init_research_library(app):
    """Initialize research library routes"""
    app.register_blueprint(research_library_bp)
    logger.info("📚 Research Library routes registered successfully")

logger.info("📚 Research Library module loaded")
