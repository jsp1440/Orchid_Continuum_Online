#!/usr/bin/env python3
"""
Missing Species Identifier - Orchid Continuum
Identifies species needing images for AI-ready coverage (10-50 images per species)
"""
import os
import psycopg2
import csv
from datetime import datetime

# AI-ready coverage thresholds
MIN_IMAGES_PER_SPECIES = 10  # Minimum for basic AI identification
IDEAL_IMAGES_PER_SPECIES = 30  # Ideal for robust AI analysis
TARGET_IMAGES_PER_SPECIES = 50  # Target for comprehensive coverage

class MissingSpeciesIdentifier:
    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.cur = self.conn.cursor()
    
    def analyze_coverage(self):
        """Analyze current species coverage for AI readiness"""
        print("\n🔬 AI-READY SPECIES COVERAGE ANALYSIS")
        print("=" * 80)
        
        # Get species with image counts
        self.cur.execute("""
            SELECT 
                ot.id,
                ot.scientific_name,
                ot.genus,
                ot.species,
                COUNT(oi.id) as image_count
            FROM orchid_taxonomy ot
            LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
            WHERE ot.scientific_name IS NOT NULL
            GROUP BY ot.id, ot.scientific_name, ot.genus, ot.species
            ORDER BY image_count ASC, ot.scientific_name
        """)
        
        all_species = self.cur.fetchall()
        
        # Categorize by coverage level
        no_images = []
        insufficient = []  # 1-9 images
        minimum = []  # 10-29 images
        ideal = []  # 30-49 images
        excellent = []  # 50+ images
        
        for species in all_species:
            tax_id, sci_name, genus, sp, img_count = species
            
            if img_count == 0:
                no_images.append(species)
            elif img_count < MIN_IMAGES_PER_SPECIES:
                insufficient.append(species)
            elif img_count < IDEAL_IMAGES_PER_SPECIES:
                minimum.append(species)
            elif img_count < TARGET_IMAGES_PER_SPECIES:
                ideal.append(species)
            else:
                excellent.append(species)
        
        total_species = len(all_species)
        
        print(f"\n📊 SPECIES COVERAGE FOR AI ANALYSIS:")
        print(f"   Total orchid species: {total_species:,}")
        print(f"\n   🔴 NO IMAGES (0):        {len(no_images):,} species ({len(no_images)/total_species*100:.1f}%)")
        print(f"   🟠 INSUFFICIENT (1-9):   {len(insufficient):,} species ({len(insufficient)/total_species*100:.1f}%)")
        print(f"   🟡 MINIMUM (10-29):      {len(minimum):,} species ({len(minimum)/total_species*100:.1f}%)")
        print(f"   🟢 IDEAL (30-49):        {len(ideal):,} species ({len(ideal)/total_species*100:.1f}%)")
        print(f"   ✅ EXCELLENT (50+):      {len(excellent):,} species ({len(excellent)/total_species*100:.1f}%)")
        
        # AI-ready calculation
        ai_ready = len(ideal) + len(excellent)
        needs_work = len(no_images) + len(insufficient) + len(minimum)
        
        print(f"\n🤖 AI READINESS:")
        print(f"   AI-Ready (30+ images): {ai_ready:,} species ({ai_ready/total_species*100:.1f}%)")
        print(f"   Needs More Images: {needs_work:,} species ({needs_work/total_species*100:.1f}%)")
        
        return {
            'no_images': no_images,
            'insufficient': insufficient,
            'minimum': minimum,
            'ideal': ideal,
            'excellent': excellent,
            'total': total_species
        }
    
    def export_priority_list(self, coverage_data, output_file='MISSING_SPECIES_PRIORITY.csv'):
        """Export prioritized list of species needing images"""
        print(f"\n📝 Exporting priority list to {output_file}...")
        
        # Combine categories in priority order
        priority_species = (
            coverage_data['no_images'] +  # Highest priority
            coverage_data['insufficient'] +  # Second priority
            coverage_data['minimum']  # Third priority
        )
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'taxonomy_id', 'scientific_name', 'genus', 'species',
                'current_images', 'images_needed_min', 'images_needed_ideal',
                'priority_level'
            ])
            
            for species in priority_species:
                tax_id, sci_name, genus, sp, img_count = species
                
                # Calculate images needed
                images_needed_min = max(0, MIN_IMAGES_PER_SPECIES - img_count)
                images_needed_ideal = max(0, IDEAL_IMAGES_PER_SPECIES - img_count)
                
                # Priority level
                if img_count == 0:
                    priority = 'CRITICAL'
                elif img_count < MIN_IMAGES_PER_SPECIES:
                    priority = 'HIGH'
                else:
                    priority = 'MEDIUM'
                
                writer.writerow([
                    tax_id, sci_name, genus, sp,
                    img_count, images_needed_min, images_needed_ideal,
                    priority
                ])
        
        print(f"✅ Exported {len(priority_species):,} species to {output_file}")
        return output_file
    
    def export_genus_summary(self, output_file='GENUS_COVERAGE_SUMMARY.csv'):
        """Export genus-level coverage summary"""
        print(f"\n📊 Generating genus summary...")
        
        self.cur.execute("""
            SELECT 
                ot.genus,
                COUNT(DISTINCT ot.id) as total_species,
                COUNT(DISTINCT CASE WHEN oi.id IS NOT NULL THEN ot.id END) as species_with_images,
                COUNT(oi.id) as total_images,
                ROUND(AVG(CASE WHEN oi.id IS NOT NULL THEN 1 ELSE 0 END)::numeric * 100, 2) as coverage_pct
            FROM orchid_taxonomy ot
            LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
            WHERE ot.genus IS NOT NULL
            GROUP BY ot.genus
            HAVING COUNT(DISTINCT ot.id) > 0
            ORDER BY total_species DESC
        """)
        
        genera = self.cur.fetchall()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'genus', 'total_species', 'species_with_images',
                'species_missing', 'total_images', 'avg_images_per_species',
                'coverage_pct', 'ai_ready_status'
            ])
            
            for row in genera:
                genus, total_sp, sp_with_imgs, total_imgs, coverage = row
                sp_missing = total_sp - sp_with_imgs
                avg_imgs = round(total_imgs / total_sp, 1) if total_sp > 0 else 0
                
                # AI ready status
                if avg_imgs >= IDEAL_IMAGES_PER_SPECIES:
                    status = 'AI_READY'
                elif avg_imgs >= MIN_IMAGES_PER_SPECIES:
                    status = 'MINIMUM'
                else:
                    status = 'INSUFFICIENT'
                
                writer.writerow([
                    genus, total_sp, sp_with_imgs, sp_missing,
                    total_imgs, avg_imgs, coverage, status
                ])
        
        print(f"✅ Exported {len(genera):,} genera to {output_file}")
        return output_file
    
    def print_top_priorities(self, coverage_data, n=20):
        """Print top N priority species"""
        print(f"\n🎯 TOP {n} PRIORITY SPECIES (No Images):")
        print("-" * 80)
        
        for i, species in enumerate(coverage_data['no_images'][:n], 1):
            tax_id, sci_name, genus, sp, img_count = species
            print(f"   {i:2}. {sci_name:50} (genus: {genus})")
        
        if len(coverage_data['no_images']) > n:
            print(f"   ... and {len(coverage_data['no_images']) - n:,} more species with no images")
    
    def close(self):
        self.cur.close()
        self.conn.close()

def main():
    print("\n🌺 ORCHID CONTINUUM - Missing Species Identifier")
    print("🎯 Goal: AI-Ready Coverage (30+ images per species)")
    print("=" * 80)
    
    identifier = MissingSpeciesIdentifier()
    
    # Analyze coverage
    coverage_data = identifier.analyze_coverage()
    
    # Export priority lists
    identifier.export_priority_list(coverage_data)
    identifier.export_genus_summary()
    
    # Show top priorities
    identifier.print_top_priorities(coverage_data)
    
    # Calculate image needs
    total_species = coverage_data['total']
    no_imgs = len(coverage_data['no_images'])
    insufficient = len(coverage_data['insufficient'])
    minimum = len(coverage_data['minimum'])
    
    print(f"\n📈 IMAGE REQUIREMENTS FOR AI-READY COVERAGE:")
    print("-" * 80)
    print(f"   Minimum goal (10 images/species):")
    print(f"      Species needing images: {no_imgs + insufficient:,}")
    print(f"      Estimated images needed: ~{(no_imgs * 10 + insufficient * 5):,}")
    print(f"\n   Ideal goal (30 images/species):")
    print(f"      Species needing images: {no_imgs + insufficient + minimum:,}")
    print(f"      Estimated images needed: ~{(no_imgs * 30 + insufficient * 20 + minimum * 15):,}")
    print(f"\n   Excellent goal (50 images/species):")
    print(f"      All species: {total_species:,}")
    print(f"      Estimated total images: ~{total_species * 50:,}")
    print("=" * 80 + "\n")
    
    identifier.close()

if __name__ == '__main__':
    main()
