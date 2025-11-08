"""
Botanical Knowledge Loader
Loads glossary terms and dichotomous keys from Julius API for Vision AI
"""

import os
import requests
import logging
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
import json

logger = logging.getLogger(__name__)

class BotanicalKnowledgeLoader:
    """Loads botanical knowledge from internal database for Vision AI enrichment"""
    
    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL")
        self.engine = create_engine(self.database_url) if self.database_url else None
        
        # Knowledge cache
        self.glossary_terms = []
        self.dichotomous_keys = {}
        self.latin_terminology = {}
        
    def load_glossary_terms(self, limit: int = 1763) -> List[Dict]:
        """Load botanical glossary terms from database"""
        logger.info(f"📚 Loading botanical glossary ({limit} terms)...")
        
        if not self.engine:
            logger.error("Database engine not initialized")
            return []
        
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT 
                        term, 
                        definition, 
                        etymology, 
                        pronunciation,
                        category
                    FROM ocu_glossary_terms
                    WHERE category IN ('morphology', 'anatomy', 'taxonomy', 'growth_habit')
                    LIMIT :limit
                """)
                
                result = conn.execute(query, {'limit': limit})
                
                terms = []
                latin_terms = {}
                
                for row in result:
                    term_data = {
                        'term': row[0],
                        'definition': row[1],
                        'etymology': row[2],
                        'pronunciation': row[3],
                        'category': row[4]
                    }
                    terms.append(term_data)
                    
                    # Extract Latin roots for AI knowledge
                    if row[2]:  # etymology field
                        latin_terms[row[0]] = {
                            'etymology': row[2],
                            'definition': row[1]
                        }
                
                self.glossary_terms = terms
                self.latin_terminology = latin_terms
                
                logger.info(f"✅ Loaded {len(terms)} botanical terms")
                logger.info(f"✅ Extracted {len(latin_terms)} Latin terminology entries")
                
                return terms
                
        except Exception as e:
            logger.error(f"❌ Failed to load glossary: {e}")
            return []
    
    def load_dichotomous_keys(self, genera: Optional[List[str]] = None) -> Dict:
        """Load dichotomous keys for specific genera"""
        logger.info("🔑 Loading dichotomous keys...")
        
        if not self.engine:
            logger.error("Database engine not initialized")
            return {}
        
        try:
            with self.engine.connect() as conn:
                # Build query
                if genera:
                    placeholders = ','.join([f':genus{i}' for i in range(len(genera))])
                    query = text(f"""
                        SELECT 
                            genus,
                            species,
                            source_organization,
                            key_type,
                            morphological_characters,
                            key_text,
                            key_metadata
                        FROM orchid_taxonomic_keys
                        WHERE genus IN ({placeholders})
                        ORDER BY genus, source_organization
                    """)
                    
                    params = {f'genus{i}': g for i, g in enumerate(genera)}
                    result = conn.execute(query, params)
                else:
                    # Load all keys
                    query = text("""
                        SELECT 
                            genus,
                            species,
                            source_organization,
                            key_type,
                            morphological_characters,
                            key_text,
                            key_metadata
                        FROM orchid_taxonomic_keys
                        ORDER BY genus, source_organization
                        LIMIT 100
                    """)
                    result = conn.execute(query)
                
                keys_by_genus = {}
                
                for row in result:
                    genus = row[0]
                    
                    if genus not in keys_by_genus:
                        keys_by_genus[genus] = []
                    
                    key_data = {
                        'genus': genus,
                        'species': row[1],
                        'source': row[2],
                        'type': row[3],
                        'characters': row[4],  # Morphological characters used in key
                        'key_text': row[5],    # Actual dichotomous key text
                        'metadata': row[6] if row[6] else {}
                    }
                    
                    keys_by_genus[genus].append(key_data)
                
                self.dichotomous_keys = keys_by_genus
                
                logger.info(f"✅ Loaded keys for {len(keys_by_genus)} genera")
                for genus, keys in keys_by_genus.items():
                    logger.info(f"  - {genus}: {len(keys)} key sources")
                
                return keys_by_genus
                
        except Exception as e:
            logger.error(f"❌ Failed to load dichotomous keys: {e}")
            return {}
    
    def build_botanical_context(self, genus: Optional[str] = None) -> str:
        """Build botanical context string for AI Vision prompt"""
        
        context_parts = []
        
        # Add key botanical terms
        if self.latin_terminology:
            context_parts.append("## BOTANICAL TERMINOLOGY (Latin)")
            
            # Select most relevant morphological terms
            morphology_terms = [
                term for term, data in self.latin_terminology.items() 
                if any(keyword in data['definition'].lower() 
                       for keyword in ['flower', 'petal', 'sepal', 'lip', 'labellum', 'column', 'spur', 'leaf'])
            ][:50]  # Top 50 most relevant
            
            for term in morphology_terms:
                data = self.latin_terminology[term]
                context_parts.append(f"- **{term}**: {data['definition']} ({data['etymology']})")
        
        # Add genus-specific dichotomous key characters
        if genus and genus in self.dichotomous_keys:
            context_parts.append(f"\n## DICHOTOMOUS KEY CHARACTERS FOR {genus.upper()}")
            
            for key in self.dichotomous_keys[genus]:
                if key['characters']:
                    context_parts.append(f"\n**{key['source']}** diagnostic characters:")
                    
                    # Parse morphological characters if available
                    if isinstance(key['characters'], str):
                        context_parts.append(f"{key['characters']}")
                    elif isinstance(key['characters'], list):
                        for char in key['characters'][:10]:  # Top 10 characters
                            context_parts.append(f"  - {char}")
        
        return "\n".join(context_parts)
    
    def get_taxonomic_characters_template(self) -> Dict:
        """Get template for extracting taxonomic characters from images"""
        return {
            "flower_morphology": {
                "sepal_count": None,
                "sepal_color": None,
                "sepal_shape": None,
                "petal_count": None,
                "petal_color": None,
                "petal_shape": None,
                "labellum_shape": None,
                "labellum_color": None,
                "labellum_markings": None,
                "column_visible": None,
                "column_position": None,
                "spur_present": None,
                "spur_length": None,
                "inflorescence_type": None,
                "flower_count": None,
                "flower_size": None,
                "flower_orientation": None
            },
            "vegetative_morphology": {
                "growth_habit": None,
                "leaf_arrangement": None,
                "leaf_shape": None,
                "leaf_texture": None,
                "pseudobulb_present": None,
                "roots_visible": None,
                "root_type": None
            },
            "diagnostic_features": {
                "distinctive_features": [],
                "unique_markings": [],
                "unusual_structures": []
            }
        }
    
    def load_all_knowledge(self):
        """Load all botanical knowledge at once"""
        logger.info("🌺 Loading complete botanical knowledge base...")
        
        self.load_glossary_terms()
        self.load_dichotomous_keys()
        
        logger.info(f"✅ Knowledge base loaded:")
        logger.info(f"  📚 {len(self.glossary_terms)} glossary terms")
        logger.info(f"  🔑 {len(self.dichotomous_keys)} genera with keys")
        logger.info(f"  🏛️ {len(self.latin_terminology)} Latin terms")
        
        return {
            'glossary_count': len(self.glossary_terms),
            'genera_with_keys': len(self.dichotomous_keys),
            'latin_terms': len(self.latin_terminology)
        }


if __name__ == "__main__":
    # Test the loader
    loader = BotanicalKnowledgeLoader()
    stats = loader.load_all_knowledge()
    
    print("\n📊 Botanical Knowledge Base Statistics:")
    print(f"  - Glossary terms: {stats['glossary_count']}")
    print(f"  - Genera with keys: {stats['genera_with_keys']}")
    print(f"  - Latin terminology: {stats['latin_terms']}")
    
    # Test context building
    if stats['genera_with_keys'] > 0:
        test_genus = list(loader.dichotomous_keys.keys())[0]
        context = loader.build_botanical_context(test_genus)
        print(f"\n📖 Sample context for {test_genus}:")
        print(context[:500] + "..." if len(context) > 500 else context)
