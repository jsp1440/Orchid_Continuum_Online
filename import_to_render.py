#!/usr/bin/env python3
"""
Import all CSV data to Render PostgreSQL database
"""
import psycopg2
import sys
from pathlib import Path

# Render database connection
RENDER_DB_URL = "postgresql://orchid_user:4WVfquT9ZRvuc0PeHxyAvoGYPbdmIbq8@dpg-d390i5mmcj7s738lpqig-a.oregon-postgres.render.com/orchid_contnuum"

# Import order (respects foreign key dependencies)
IMPORT_ORDER = [
    'orchid_taxonomy.csv',
    'orchid_records.csv',
    'svo_extracted_data.csv',
    'scraping_log.csv',
    'knowledge_base.csv',
    'orchid_glossary_terms.csv',
    'orchid_collections.csv',
    'user_orchid_collections.csv',
    'external_database_cache.csv',
]

def import_csv_to_table(conn, csv_file):
    """Import a CSV file to its corresponding table"""
    table_name = csv_file.replace('.csv', '')
    csv_path = Path(csv_file).absolute()
    
    if not csv_path.exists():
        print(f"⚠️  Skipping {csv_file} - file not found")
        return False
    
    try:
        with conn.cursor() as cur:
            # Use COPY command to import CSV
            with open(csv_path, 'r') as f:
                cur.copy_expert(
                    f"COPY {table_name} FROM STDIN WITH CSV HEADER",
                    f
                )
            conn.commit()
            
            # Count imported rows
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"✅ Imported {csv_file} → {table_name} ({count:,} rows)")
            return True
    except Exception as e:
        print(f"❌ Error importing {csv_file}: {e}")
        conn.rollback()
        return False

def main():
    print("🚀 Starting import to Render PostgreSQL...")
    print(f"📊 Database: dpg-d390i5mmcj7s738lpqig-a/orchid_contnuum\n")
    
    try:
        # Connect to Render database
        conn = psycopg2.connect(RENDER_DB_URL)
        print("✅ Connected to Render database\n")
        
        success_count = 0
        total_files = len(IMPORT_ORDER)
        
        # Import in order
        for csv_file in IMPORT_ORDER:
            if import_csv_to_table(conn, csv_file):
                success_count += 1
        
        conn.close()
        
        print(f"\n🎉 Import complete! {success_count}/{total_files} files imported successfully")
        
        if success_count < total_files:
            print(f"⚠️  {total_files - success_count} files had issues - check errors above")
            sys.exit(1)
        else:
            print("✅ All data imported successfully to Render!")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
