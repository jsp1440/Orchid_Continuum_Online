#!/usr/bin/env python3
"""
Import all 112 genera from Teoh PDF CSV into genus knowledge cards
Creates indexed entries for Research Library integration
"""

import csv
import os
from app import app, db
from models import GenusKnowledgeCard, ResearchDocument

def import_genera_from_csv():
    """Import all genera from the CSV file"""
    
    csv_path = 'attached_assets/medicinal_orchid_genera_extracted_1760304975945.csv'
    
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        return
    
    with app.app_context():
        # Get the Teoh document
        teoh_doc = ResearchDocument.query.filter_by(title="Medicinal Orchids of Asia").first()
        
        if not teoh_doc:
            print("❌ Error: Teoh document not found in database")
            return
        
        print(f"📚 Found Teoh document (ID: {teoh_doc.id})")
        
        # Read CSV and process genera
        genera_processed = 0
        genera_skipped = 0
        genera_created = 0
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                genus = row['Genus'].strip()
                page_start = row['PageStart'].strip()
                excerpt = row['Medicinal_Uses_Excerpt'].strip()
                
                # Skip invalid entries
                if not genus or not page_start:
                    genera_skipped += 1
                    continue
                
                # Skip non-genus entries (like "Seiden" which is an author name)
                if genus in ['Seiden', 'Anaphora']:  # Filter obvious non-genera
                    genera_skipped += 1
                    continue
                
                # Check if already exists
                existing = GenusKnowledgeCard.query.filter_by(
                    genus=genus,
                    document_id=teoh_doc.id
                ).first()
                
                if existing:
                    print(f"⏭️  {genus}: Already exists, skipping")
                    genera_skipped += 1
                    continue
                
                # Create page reference
                try:
                    page_num = int(page_start)
                    page_refs = [page_num]
                except ValueError:
                    page_refs = []
                
                # Create knowledge card with minimal data
                # We'll enrich these later with specific medicinal data
                card = GenusKnowledgeCard(
                    document_id=teoh_doc.id,
                    genus=genus,
                    indigenous_names=[],
                    traditional_uses=["Referenced in Medicinal Orchids of Asia"],
                    medicinal_uses=[],
                    active_compounds=[],
                    cultural_areas=["Asia"],  # Default since it's "Medicinal Orchids of Asia"
                    page_references=page_refs,
                    key_findings=f"Index entry - See page {page_start} in Teoh (2016) for detailed information."
                )
                
                # Add excerpt if available
                if excerpt:
                    card.key_findings = f"{excerpt}\n\nPage {page_start} in Teoh (2016)"
                
                db.session.add(card)
                genera_created += 1
                genera_processed += 1
                
                print(f"✅ {genus}: Created knowledge card (page {page_start})")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n🎉 Import complete!")
            print(f"   ✅ Created: {genera_created} new knowledge cards")
            print(f"   ⏭️  Skipped: {genera_skipped} existing/invalid entries")
            print(f"   📊 Total processed: {genera_processed}")
            
            # Show summary stats
            total_cards = GenusKnowledgeCard.query.filter_by(document_id=teoh_doc.id).count()
            print(f"\n📚 Total knowledge cards for Teoh document: {total_cards}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during commit: {e}")
            raise

if __name__ == '__main__':
    import_genera_from_csv()
