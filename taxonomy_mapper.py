#!/usr/bin/env python3
"""
TAXONOMY MAPPER - O(1) Direct Database Lookup
==============================================
High-performance taxonomy matching using indexed database queries.
NO linear scanning. NO alphabetical iteration. Direct lookups only.
"""

import os
import re
import logging
from typing import Dict, Optional, Tuple, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaxonomyMapper:
    """
    O(1) taxonomy lookup using direct database queries and in-memory cache.
    Replaces all sequential scanning with index-based lookups.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        db_url = database_url or os.environ.get('DATABASE_URL', '')
        if not db_url:
            raise ValueError("DATABASE_URL not provided")
        self.database_url = db_url
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )
        
        self._cache_scientific_name: Dict[str, Dict] = {}
        self._cache_genus: Dict[str, Dict] = {}
        self._cache_species: Dict[str, Dict] = {}
        self._cache_by_id: Dict[int, Dict] = {}
        self._cache_gbif_key: Dict[int, Dict] = {}
        
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _normalize_name(self, name: str) -> str:
        """Normalize taxon name for consistent lookup"""
        if not name:
            return ""
        normalized = name.strip().lower()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'[×x]\s*', '', normalized)
        normalized = re.sub(r'\s*(var\.|f\.|subsp\.)\s*\S+', '', normalized)
        normalized = re.sub(r'"[^"]*"', '', normalized)
        normalized = re.sub(r"'[^']*'", '', normalized)
        return normalized.strip()
    
    def _parse_genus_species(self, name: str) -> Tuple[str, Optional[str]]:
        """Extract genus and species from scientific name"""
        normalized = self._normalize_name(name)
        parts = normalized.split()
        if not parts:
            return ("", None)
        genus = parts[0].capitalize()
        species = parts[1].lower() if len(parts) > 1 else None
        return (genus, species)
    
    def _build_cache_entry(self, row: Any, columns: List[str]) -> Dict:
        """Build cache entry from database row"""
        entry = {'matched': True}
        for i, col in enumerate(columns):
            entry[col] = row[i]
        return entry
    
    def _add_to_cache(self, entry: Dict) -> None:
        """Add entry to all applicable caches"""
        if entry.get('scientific_name'):
            key = self._normalize_name(entry['scientific_name'])
            self._cache_scientific_name[key] = entry
        
        if entry.get('genus'):
            genus_key = entry['genus'].lower()
            if genus_key not in self._cache_genus:
                self._cache_genus[genus_key] = entry
        
        if entry.get('genus') and entry.get('species'):
            species_key = f"{entry['genus'].lower()}_{entry['species'].lower()}"
            self._cache_species[species_key] = entry
        
        if entry.get('id'):
            self._cache_by_id[entry['id']] = entry
        
        if entry.get('gbif_taxon_key'):
            self._cache_gbif_key[entry['gbif_taxon_key']] = entry
    
    def _check_cache(self, name: str) -> Optional[Dict]:
        """Check all caches for a match"""
        normalized = self._normalize_name(name)
        
        if normalized in self._cache_scientific_name:
            self._cache_hits += 1
            return self._cache_scientific_name[normalized]
        
        genus, species = self._parse_genus_species(name)
        
        if species:
            species_key = f"{genus.lower()}_{species.lower()}"
            if species_key in self._cache_species:
                self._cache_hits += 1
                return self._cache_species[species_key]
        
        if genus:
            genus_key = genus.lower()
            if genus_key in self._cache_genus:
                self._cache_hits += 1
                return self._cache_genus[genus_key]
        
        self._cache_misses += 1
        return None
    
    def lookup(self, name: str) -> Dict:
        """
        O(1) taxonomy lookup by name.
        Returns exact taxon node or unmatched_taxon result.
        """
        if not name or not name.strip():
            return {'matched': False, 'reason': 'empty_input'}
        
        cached = self._check_cache(name)
        if cached:
            return cached
        
        normalized = self._normalize_name(name)
        genus, species = self._parse_genus_species(name)
        
        columns = ['id', 'scientific_name', 'genus', 'species', 'author',
                   'family', 'taxonomic_status', 'gbif_taxon_key']
        col_str = ', '.join(columns)
        
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT {col_str}
                FROM orchid_taxonomy 
                WHERE LOWER(scientific_name) = LOWER(:name)
                LIMIT 1
            """), {'name': normalized})
            
            row = result.fetchone()
            if row:
                entry = self._build_cache_entry(row, columns)
                self._add_to_cache(entry)
                return entry
            
            if genus and species:
                result = conn.execute(text(f"""
                    SELECT {col_str}
                    FROM orchid_taxonomy 
                    WHERE LOWER(genus) = LOWER(:genus) 
                      AND LOWER(species) = LOWER(:species)
                    LIMIT 1
                """), {'genus': genus, 'species': species})
                
                row = result.fetchone()
                if row:
                    entry = self._build_cache_entry(row, columns)
                    self._add_to_cache(entry)
                    return entry
            
            if genus:
                result = conn.execute(text(f"""
                    SELECT {col_str}
                    FROM orchid_taxonomy 
                    WHERE LOWER(genus) = LOWER(:genus)
                      AND species IS NULL
                    LIMIT 1
                """), {'genus': genus})
                
                row = result.fetchone()
                if row:
                    entry = self._build_cache_entry(row, columns)
                    self._add_to_cache(entry)
                    return entry
                
                result = conn.execute(text(f"""
                    SELECT {col_str}
                    FROM orchid_taxonomy 
                    WHERE LOWER(genus) = LOWER(:genus)
                    LIMIT 1
                """), {'genus': genus})
                
                row = result.fetchone()
                if row:
                    entry = self._build_cache_entry(row, columns)
                    self._add_to_cache(entry)
                    return entry
        
        return {
            'matched': False,
            'reason': 'unmatched_taxon',
            'input_name': name,
            'normalized_name': normalized,
            'parsed_genus': genus,
            'parsed_species': species
        }
    
    def lookup_by_id(self, taxonomy_id: int) -> Dict:
        """O(1) lookup by primary key ID"""
        if taxonomy_id in self._cache_by_id:
            self._cache_hits += 1
            return self._cache_by_id[taxonomy_id]
        
        self._cache_misses += 1
        
        columns = ['id', 'scientific_name', 'genus', 'species', 'author',
                   'family', 'taxonomic_status', 'gbif_taxon_key']
        col_str = ', '.join(columns)
        
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT {col_str}
                FROM orchid_taxonomy 
                WHERE id = :id
                LIMIT 1
            """), {'id': taxonomy_id})
            
            row = result.fetchone()
            if row:
                entry = self._build_cache_entry(row, columns)
                self._add_to_cache(entry)
                return entry
        
        return {'matched': False, 'reason': 'unmatched_taxon', 'input_id': taxonomy_id}
    
    def lookup_by_gbif_key(self, gbif_key: int) -> Dict:
        """O(1) lookup by GBIF taxon key"""
        if gbif_key in self._cache_gbif_key:
            self._cache_hits += 1
            return self._cache_gbif_key[gbif_key]
        
        self._cache_misses += 1
        
        columns = ['id', 'scientific_name', 'genus', 'species', 'author',
                   'family', 'taxonomic_status', 'gbif_taxon_key']
        col_str = ', '.join(columns)
        
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT {col_str}
                FROM orchid_taxonomy 
                WHERE gbif_taxon_key = :gbif_key
                LIMIT 1
            """), {'gbif_key': gbif_key})
            
            row = result.fetchone()
            if row:
                entry = self._build_cache_entry(row, columns)
                self._add_to_cache(entry)
                return entry
        
        return {'matched': False, 'reason': 'unmatched_taxon', 'input_gbif_key': gbif_key}
    
    def attach_to_taxonomy(self, record: Dict, image_url: Optional[str] = None) -> Dict:
        """
        Attach an orchid record to the correct taxonomy node.
        Returns the taxonomy node with attachment status.
        """
        name = record.get('scientific_name') or record.get('name') or ''
        if not name:
            genus = record.get('genus', '')
            species = record.get('species', '')
            name = f"{genus} {species}".strip()
        
        taxon = self.lookup(name)
        
        if not taxon.get('matched'):
            return {
                'attached': False,
                'reason': 'unmatched_taxon',
                'input': record,
                'lookup_result': taxon
            }
        
        taxonomy_id = taxon['id']
        
        if image_url:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO orchid_images (taxonomy_id, image_url, image_source, created_at)
                    VALUES (:taxonomy_id, :url, :source, NOW())
                    ON CONFLICT (image_url) DO NOTHING
                """), {
                    'taxonomy_id': taxonomy_id,
                    'url': image_url,
                    'source': record.get('source', 'unknown')
                })
                conn.commit()
        
        return {
            'attached': True,
            'taxonomy_id': taxonomy_id,
            'matched_taxon': taxon,
            'input': record
        }
    
    def batch_lookup(self, names: list) -> Dict[str, Dict]:
        """Batch lookup multiple names efficiently"""
        results: Dict[str, Dict] = {}
        uncached: List[str] = []
        
        for name in names:
            cached = self._check_cache(name)
            if cached:
                results[name] = cached
            else:
                uncached.append(name)
        
        if uncached:
            normalized_map = {self._normalize_name(n): n for n in uncached}
            normalized_list = list(normalized_map.keys())
            
            columns = ['id', 'scientific_name', 'genus', 'species', 'author',
                       'family', 'taxonomic_status', 'gbif_taxon_key']
            col_str = ', '.join(columns)
            
            with self.engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT {col_str}
                    FROM orchid_taxonomy 
                    WHERE LOWER(scientific_name) = ANY(:names)
                """), {'names': normalized_list})
                
                for row in result:
                    entry = self._build_cache_entry(row, columns)
                    self._add_to_cache(entry)
                    
                    sci_name = entry.get('scientific_name', '')
                    norm_key = self._normalize_name(sci_name or '')
                    if norm_key in normalized_map:
                        original_name = normalized_map[norm_key]
                        results[original_name] = entry
        
        for name in names:
            if name not in results:
                results[name] = {
                    'matched': False,
                    'reason': 'unmatched_taxon',
                    'input_name': name
                }
        
        return results
    
    def preload_cache(self, limit: int = 50000) -> int:
        """Preload frequently accessed taxa into memory cache"""
        columns = ['id', 'scientific_name', 'genus', 'species', 'author',
                   'family', 'taxonomic_status', 'gbif_taxon_key']
        col_str = ', '.join([f't.{c}' for c in columns])
        
        with self.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT {col_str}
                FROM orchid_taxonomy t
                LEFT JOIN orchid_images i ON t.id = i.taxonomy_id
                GROUP BY {col_str}
                ORDER BY COUNT(i.id) DESC
                LIMIT :limit
            """), {'limit': limit})
            
            count = 0
            for row in result:
                entry = self._build_cache_entry(row, columns)
                self._add_to_cache(entry)
                count += 1
        
        logger.info(f"Preloaded {count} taxa into cache")
        return count
    
    def get_cache_stats(self) -> Dict:
        """Return cache statistics"""
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'cached_scientific_names': len(self._cache_scientific_name),
            'cached_genera': len(self._cache_genus),
            'cached_species': len(self._cache_species),
            'cached_by_id': len(self._cache_by_id),
            'cached_by_gbif_key': len(self._cache_gbif_key)
        }
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        self._cache_scientific_name.clear()
        self._cache_genus.clear()
        self._cache_species.clear()
        self._cache_by_id.clear()
        self._cache_gbif_key.clear()
        self._cache_hits = 0
        self._cache_misses = 0


_mapper_instance: Optional[TaxonomyMapper] = None


def get_mapper() -> TaxonomyMapper:
    """Get singleton TaxonomyMapper instance"""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = TaxonomyMapper()
    return _mapper_instance


def lookup_taxon(name: str) -> Dict:
    """Direct O(1) taxon lookup by name"""
    return get_mapper().lookup(name)


def lookup_taxon_by_id(taxonomy_id: int) -> Dict:
    """Direct O(1) taxon lookup by ID"""
    return get_mapper().lookup_by_id(taxonomy_id)


def lookup_taxon_by_gbif_key(gbif_key: int) -> Dict:
    """Direct O(1) taxon lookup by GBIF taxon key"""
    return get_mapper().lookup_by_gbif_key(gbif_key)


def attach_record_to_taxonomy(record: Dict, image_url: Optional[str] = None) -> Dict:
    """Attach orchid record to correct taxonomy node"""
    return get_mapper().attach_to_taxonomy(record, image_url)


def batch_lookup_taxa(names: list) -> Dict[str, Dict]:
    """Batch lookup multiple taxa efficiently"""
    return get_mapper().batch_lookup(names)


if __name__ == "__main__":
    mapper = TaxonomyMapper()
    
    test_names = [
        "Phalaenopsis amabilis",
        "Cattleya labiata",
        "Dendrobium nobile",
        "Paphiopedilum rothschildianum",
        "Nonexistent orchidius",
        "Vanda coerulea"
    ]
    
    print("TAXONOMY MAPPER - O(1) LOOKUP TEST")
    print("=" * 60)
    
    for name in test_names:
        result = mapper.lookup(name)
        if result.get('matched'):
            print(f"✓ {name}")
            print(f"  → ID: {result['id']}, Scientific: {result['scientific_name']}")
        else:
            print(f"✗ {name}")
            print(f"  → {result['reason']}")
    
    print("\nCache Stats:", mapper.get_cache_stats())
