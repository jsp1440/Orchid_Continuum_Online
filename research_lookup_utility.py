"""
Research Lookup Utility for AI Widgets
Provides quick access to ethnobotanical and medicinal knowledge from the Research Library
"""

from app import db
from models import GenusKnowledgeCard, ResearchDocument
from sqlalchemy import func, or_
import logging

logger = logging.getLogger(__name__)


def get_genus_research_data(genus_name: str) -> dict:
    """
    Quick lookup of research data for a given genus
    
    Args:
        genus_name: The genus name to look up (case-insensitive)
    
    Returns:
        Dictionary with research data or None if not found
    """
    if not genus_name:
        return None
    
    try:
        # Case-insensitive genus lookup
        knowledge_card = db.session.query(GenusKnowledgeCard).filter(
            func.lower(GenusKnowledgeCard.genus) == func.lower(genus_name.strip())
        ).first()
        
        if not knowledge_card:
            return None
        
        return {
            'genus': knowledge_card.genus,
            'has_research': True,
            'traditional_uses': knowledge_card.traditional_uses or [],
            'medicinal_uses': knowledge_card.medicinal_uses or [],
            'active_compounds': knowledge_card.active_compounds or [],
            'cultural_areas': knowledge_card.cultural_areas or [],
            'indigenous_names': knowledge_card.indigenous_names or [],
            'source': knowledge_card.source or 'Research Library',
            'page_reference': knowledge_card.page_reference,
            'view_count': knowledge_card.view_count or 0
        }
    
    except Exception as e:
        logger.error(f"Error looking up research data for genus {genus_name}: {e}")
        return None


def format_research_summary(research_data: dict, include_disclaimer: bool = True) -> str:
    """
    Format research data into a readable summary for AI widgets
    
    Args:
        research_data: Dictionary from get_genus_research_data()
        include_disclaimer: Whether to include medical disclaimer
    
    Returns:
        Formatted string summary
    """
    if not research_data or not research_data.get('has_research'):
        return ""
    
    summary_parts = []
    
    # Header
    summary_parts.append(f"📚 Research Data for {research_data['genus']}:")
    summary_parts.append("")
    
    # Traditional uses
    if research_data.get('traditional_uses'):
        summary_parts.append("📿 Traditional Uses:")
        for use in research_data['traditional_uses'][:3]:  # Limit to top 3
            summary_parts.append(f"  • {use}")
        if len(research_data['traditional_uses']) > 3:
            summary_parts.append(f"  ... and {len(research_data['traditional_uses']) - 3} more")
        summary_parts.append("")
    
    # Medicinal uses
    if research_data.get('medicinal_uses'):
        summary_parts.append("💊 Medicinal Uses:")
        for use in research_data['medicinal_uses'][:3]:  # Limit to top 3
            summary_parts.append(f"  • {use}")
        if len(research_data['medicinal_uses']) > 3:
            summary_parts.append(f"  ... and {len(research_data['medicinal_uses']) - 3} more")
        summary_parts.append("")
    
    # Active compounds
    if research_data.get('active_compounds'):
        compounds = ', '.join(research_data['active_compounds'][:5])
        summary_parts.append(f"🧪 Active Compounds: {compounds}")
        summary_parts.append("")
    
    # Cultural areas
    if research_data.get('cultural_areas'):
        areas = ', '.join(research_data['cultural_areas'][:5])
        summary_parts.append(f"🌏 Cultural Areas: {areas}")
        summary_parts.append("")
    
    # Source
    source = research_data.get('source', 'Research Library')
    page_ref = research_data.get('page_reference', '')
    if page_ref:
        summary_parts.append(f"📖 Source: {source} (Page {page_ref})")
    else:
        summary_parts.append(f"📖 Source: {source}")
    
    # Disclaimer
    if include_disclaimer:
        summary_parts.append("")
        summary_parts.append("⚠️ IMPORTANT: This information is for educational purposes only. NOT medical advice.")
    
    return "\n".join(summary_parts)


def get_research_context_for_ai(genus_name: str) -> str:
    """
    Get concise research context suitable for AI model context injection
    
    Args:
        genus_name: The genus name
    
    Returns:
        Concise research context string for AI models
    """
    research_data = get_genus_research_data(genus_name)
    
    if not research_data:
        return ""
    
    context_parts = [f"Research Context for {research_data['genus']}:"]
    
    if research_data.get('traditional_uses'):
        uses = '; '.join(research_data['traditional_uses'][:3])
        context_parts.append(f"Traditional uses: {uses}")
    
    if research_data.get('medicinal_uses'):
        uses = '; '.join(research_data['medicinal_uses'][:3])
        context_parts.append(f"Medicinal uses: {uses}")
    
    if research_data.get('active_compounds'):
        compounds = ', '.join(research_data['active_compounds'][:3])
        context_parts.append(f"Known compounds: {compounds}")
    
    if research_data.get('cultural_areas'):
        areas = ', '.join(research_data['cultural_areas'][:3])
        context_parts.append(f"Cultural significance in: {areas}")
    
    return " | ".join(context_parts)


def check_genus_has_research(genus_name: str) -> bool:
    """
    Quick check if a genus has research data available
    
    Args:
        genus_name: The genus name to check
    
    Returns:
        True if research data exists, False otherwise
    """
    if not genus_name:
        return False
    
    try:
        exists = db.session.query(GenusKnowledgeCard).filter(
            func.lower(GenusKnowledgeCard.genus) == func.lower(genus_name.strip())
        ).first() is not None
        
        return exists
    
    except Exception as e:
        logger.error(f"Error checking research for genus {genus_name}: {e}")
        return False


def get_all_researched_genera() -> list:
    """
    Get list of all genera with research data
    
    Returns:
        List of genus names with research data
    """
    try:
        genera = db.session.query(GenusKnowledgeCard.genus).distinct().all()
        return [g[0] for g in genera]
    
    except Exception as e:
        logger.error(f"Error getting researched genera: {e}")
        return []


def increment_research_view_count(genus_name: str):
    """
    Increment view count when research data is accessed
    
    Args:
        genus_name: The genus name
    """
    if not genus_name:
        return
    
    try:
        knowledge_card = db.session.query(GenusKnowledgeCard).filter(
            func.lower(GenusKnowledgeCard.genus) == func.lower(genus_name.strip())
        ).first()
        
        if knowledge_card:
            knowledge_card.view_count = (knowledge_card.view_count or 0) + 1
            db.session.commit()
            logger.debug(f"Incremented view count for {genus_name}")
    
    except Exception as e:
        logger.error(f"Error incrementing view count for {genus_name}: {e}")
        db.session.rollback()


logger.info("📚 Research Lookup Utility initialized")
