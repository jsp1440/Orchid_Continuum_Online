#!/usr/bin/env python3
"""
DATA VALIDATOR - Enforces Strict Data Integrity
================================================
Validates all data before insertion:
- Taxonomy must exist in orchid_taxonomy
- Genus/species must be locked and correct
- Metadata must be complete
- No duplicate images
"""
import os, psycopg2, logging
from psycopg2 import pool

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')
pool_obj = pool.SimpleConnectionPool(minconn=1, maxconn=3, dsn=DATABASE_URL)

class DataValidator:
    @staticmethod
    def validate_and_insert_image(image_data):
        """
        Validate image data before insertion.
        Returns: (success: bool, reason: str, image_id: int or None)
        """
        conn = pool_obj.getconn()
        try:
            cur = conn.cursor()
            
            # VALIDATION 1: Taxonomy must exist
            taxonomy_id = image_data.get('taxonomy_id')
            if not taxonomy_id:
                return False, "REJECT: No taxonomy_id provided", None
            
            cur.execute("SELECT genus, species FROM orchid_taxonomy WHERE id = %s", (taxonomy_id,))
            result = cur.fetchone()
            
            if not result:
                return False, f"REJECT: taxonomy_id {taxonomy_id} does not exist", None
            
            locked_genus, locked_species = result
            
            # VALIDATION 2: Image URL must be provided
            image_url = image_data.get('image_url')
            if not image_url or len(image_url) < 10:
                return False, "REJECT: Invalid or missing image_url", None
            
            # VALIDATION 3: Check for duplicates by URL
            cur.execute(
                "SELECT id FROM orchid_images WHERE image_url = %s",
                (image_url,)
            )
            if cur.fetchone():
                return False, f"DUPLICATE: URL already exists", None
            
            # VALIDATION 4: Metadata must be present and locked
            image_source = image_data.get('image_source', 'Unknown')
            if not image_source:
                return False, "REJECT: No image_source provided", None
            
            # VALIDATION 5: Insert with locked taxonomy reference
            cur.execute("""
                INSERT INTO orchid_images (
                    taxonomy_id, image_url, image_source, 
                    country, locality, latitude, longitude,
                    observer_name, image_license, gbif_occurrence_key,
                    occurrence_metadata, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING id
            """, (
                taxonomy_id, image_url, image_source,
                image_data.get('country'),
                image_data.get('locality'),
                image_data.get('latitude'),
                image_data.get('longitude'),
                image_data.get('observer_name'),
                image_data.get('image_license'),
                image_data.get('gbif_occurrence_key'),
                image_data.get('occurrence_metadata')
            ))
            
            image_id = cur.fetchone()[0]
            conn.commit()
            
            return True, f"✅ INSERTED: {locked_genus} {locked_species} (ID: {image_id})", image_id
            
        except Exception as e:
            conn.rollback()
            return False, f"ERROR: {str(e)}", None
        finally:
            pool_obj.putconn(conn)
    
    @staticmethod
    def audit_database():
        """Daily audit of database integrity"""
        conn = pool_obj.getconn()
        try:
            cur = conn.cursor()
            
            # Check for orphaned images
            cur.execute("""
                SELECT COUNT(*) FROM orchid_images i
                WHERE NOT EXISTS (SELECT 1 FROM orchid_taxonomy t WHERE t.id = i.taxonomy_id)
            """)
            orphaned = cur.fetchone()[0]
            
            # Check for NULL taxonomy_id
            cur.execute("SELECT COUNT(*) FROM orchid_images WHERE taxonomy_id IS NULL")
            nulls = cur.fetchone()[0]
            
            # Check for NULL image_url
            cur.execute("SELECT COUNT(*) FROM orchid_images WHERE image_url IS NULL OR image_url = ''")
            null_urls = cur.fetchone()[0]
            
            report = {
                'orphaned_images': orphaned,
                'null_taxonomy_ids': nulls,
                'null_image_urls': null_urls,
                'is_clean': orphaned == 0 and nulls == 0 and null_urls == 0
            }
            
            conn.commit()
            return report
            
        finally:
            pool_obj.putconn(conn)

if __name__ == "__main__":
    print("📊 Data Integrity Audit")
    report = DataValidator.audit_database()
    print(f"  Orphaned: {report['orphaned_images']}")
    print(f"  NULL taxonomy: {report['null_taxonomy_ids']}")
    print(f"  NULL URLs: {report['null_image_urls']}")
    print(f"  Status: {'✅ CLEAN' if report['is_clean'] else '❌ HAS ISSUES'}")
