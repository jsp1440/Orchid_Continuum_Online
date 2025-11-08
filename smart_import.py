#!/usr/bin/env python3
"""
Smart import that handles column mapping between CSV and Render tables
"""
import psycopg2
import csv
import sys
from pathlib import Path

RENDER_DB_URL = "postgresql://orchid_user:4WVfquT9ZRvuc0PeHxyAvoGYPbdmIbq8@dpg-d390i5mmcj7s738lpqig-a.oregon-postgres.render.com/orchid_contnuum"

# Map CSV files to table names
TABLE_MAPPING = {
    'orchid_records.csv': 'orchid_record',  # singular!
    'orchid_taxonomy.csv': 'orchid_taxonomy',
}

def get_table_columns(conn, table_name):
    """Get ordered list of columns for a table"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """, (table_name,))
        return [row[0] for row in cur.fetchall()]

def import_csv_smart(conn, csv_file, table_name):
    """Import CSV with column matching"""
    csv_path = Path(csv_file)
    
    if not csv_path.exists():
        print(f"⚠️  Skipping {csv_file} - file not found")
        return False
    
    try:
        # Get table columns
        table_cols = get_table_columns(conn, table_name)
        
        # Read CSV and match columns
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_cols = reader.fieldnames
            
            # Find matching columns (exclude 'id' to let PostgreSQL auto-generate)
            matched_cols = [col for col in csv_cols if col in table_cols and col != 'id']
            
            if not matched_cols:
                print(f"❌ No matching columns between CSV and table {table_name}")
                return False
            
            print(f"📊 Importing {len(matched_cols)}/{len(csv_cols)} columns to {table_name}")
            
            # Clear existing data and reset sequence
            with conn.cursor() as cur:
                cur.execute(f"DELETE FROM {table_name}")
                # Reset ID sequence to start from 1
                cur.execute(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1")
                conn.commit()
                print(f"  Cleared {table_name} and reset ID sequence")
            
            # Import row by row
            imported = 0
            with conn.cursor() as cur:
                for row in reader:
                    # Build INSERT statement with matched columns
                    # Convert empty strings to None for proper NULL handling
                    values = [row.get(col) if row.get(col) != '' else None for col in matched_cols]
                    placeholders = ','.join(['%s'] * len(matched_cols))
                    col_names = ','.join(matched_cols)
                    
                    cur.execute(
                        f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})",
                        values
                    )
                    imported += 1
                    
                    if imported % 1000 == 0:
                        print(f"  ... {imported:,} rows")
                        conn.commit()
            
            conn.commit()
            print(f"✅ Imported {imported:,} rows to {table_name}")
            return True
            
    except Exception as e:
        print(f"❌ Error importing {csv_file}: {e}")
        conn.rollback()
        return False

def main():
    print("🚀 Smart Import to Render PostgreSQL...")
    print(f"📊 Database: orchid_contnuum @ oregon-postgres.render.com\n")
    
    try:
        conn = psycopg2.connect(RENDER_DB_URL)
        print("✅ Connected to Render database\n")
        
        # Import main tables
        for csv_file, table_name in TABLE_MAPPING.items():
            import_csv_smart(conn, csv_file, table_name)
        
        # Show final counts
        print("\n📊 Final Record Counts:")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
            tax_count = cur.fetchone()[0]
            print(f"  Taxonomy: {tax_count:,} records")
            
            cur.execute("SELECT COUNT(*) FROM orchid_record")
            rec_count = cur.fetchone()[0]
            print(f"  Orchids: {rec_count:,} records")
        
        conn.close()
        print("\n✅ Import complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
