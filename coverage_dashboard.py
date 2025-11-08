#!/usr/bin/env python3
"""
Species Coverage Dashboard - Orchid Continuum
Real-time progress toward 100% AI-ready coverage
"""
import os
import psycopg2
from datetime import datetime, timedelta

class CoverageDashboard:
    def __init__(self):
        self.conn = psycopg2.connect(os.environ['DATABASE_URL'])
        self.cur = self.conn.cursor()
    
    def display_dashboard(self):
        """Display comprehensive coverage dashboard"""
        print("\n" + "=" * 80)
        print("🌺 ORCHID CONTINUUM - AI-READY SPECIES COVERAGE DASHBOARD")
        print(f"📅 Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        print("=" * 80)
        
        # Overall stats
        self.cur.execute("SELECT COUNT(*) FROM orchid_taxonomy")
        total_species = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(DISTINCT taxonomy_id) FROM orchid_images WHERE taxonomy_id IS NOT NULL")
        species_with_images = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM orchid_images")
        total_images = self.cur.fetchone()[0]
        
        print(f"\n📊 OVERALL PROGRESS:")
        print(f"   Total Orchid Species: {total_species:,}")
        print(f"   Species with Images: {species_with_images:,}")
        print(f"   Species Missing: {total_species - species_with_images:,}")
        print(f"   Total Images: {total_images:,}")
        print(f"   Basic Coverage: {(species_with_images/total_species)*100:.2f}%")
        
        # AI Readiness breakdown
        self.cur.execute("""
            SELECT 
                COUNT(CASE WHEN img_count = 0 THEN 1 END) as no_images,
                COUNT(CASE WHEN img_count BETWEEN 1 AND 9 THEN 1 END) as insufficient,
                COUNT(CASE WHEN img_count BETWEEN 10 AND 29 THEN 1 END) as minimum,
                COUNT(CASE WHEN img_count BETWEEN 30 AND 49 THEN 1 END) as ideal,
                COUNT(CASE WHEN img_count >= 50 THEN 1 END) as excellent
            FROM (
                SELECT ot.id, COUNT(oi.id) as img_count
                FROM orchid_taxonomy ot
                LEFT JOIN orchid_images oi ON ot.id = oi.taxonomy_id
                GROUP BY ot.id
            ) counts
        """)
        
        breakdown = self.cur.fetchone()
        no_imgs, insufficient, minimum, ideal, excellent = breakdown
        ai_ready = ideal + excellent
        
        print(f"\n🤖 AI READINESS BREAKDOWN:")
        print(f"   🔴 No Images (0):        {no_imgs:,} species ({no_imgs/total_species*100:.1f}%)")
        print(f"   🟠 Insufficient (1-9):   {insufficient:,} species ({insufficient/total_species*100:.1f}%)")
        print(f"   🟡 Minimum (10-29):      {minimum:,} species ({minimum/total_species*100:.1f}%)")
        print(f"   🟢 Ideal (30-49):        {ideal:,} species ({ideal/total_species*100:.1f}%)")
        print(f"   ✅ Excellent (50+):      {excellent:,} species ({excellent/total_species*100:.1f}%)")
        print(f"\n   🎯 AI-READY TOTAL:       {ai_ready:,} species ({ai_ready/total_species*100:.2f}%)")
        
        # Progress bar
        progress = int((ai_ready / total_species) * 50)
        bar = "█" * progress + "░" * (50 - progress)
        print(f"\n   [{bar}] {ai_ready/total_species*100:.2f}%")
        
        # Recent activity
        self.cur.execute("""
            SELECT 
                DATE(created_at) as day,
                COUNT(*) as images,
                COUNT(DISTINCT taxonomy_id) as species
            FROM orchid_images
            WHERE created_at >= NOW() - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        """)
        
        recent = self.cur.fetchall()
        if recent:
            print(f"\n📈 RECENT ACTIVITY (Last 7 Days):")
            total_week = 0
            for row in recent:
                print(f"   {row[0]}: {row[1]:,} images, {row[2]:,} species")
                total_week += row[1]
            print(f"   Total: {total_week:,} images this week")
        
        # Top performing genera
        print(f"\n🏆 TOP 10 GENERA (Most AI-Ready):")
        self.cur.execute("""
            SELECT 
                ot.genus,
                COUNT(DISTINCT ot.id) as total_sp,
                COUNT(DISTINCT CASE WHEN img_count >= 30 THEN ot.id END) as ai_ready_sp,
                SUM(img_count) as total_imgs
            FROM orchid_taxonomy ot
            LEFT JOIN (
                SELECT taxonomy_id, COUNT(*) as img_count
                FROM orchid_images
                GROUP BY taxonomy_id
            ) img_counts ON ot.id = img_counts.taxonomy_id
            WHERE ot.genus IS NOT NULL
            GROUP BY ot.genus
            HAVING COUNT(DISTINCT CASE WHEN img_count >= 30 THEN ot.id END) > 0
            ORDER BY ai_ready_sp DESC, total_sp DESC
            LIMIT 10
        """)
        
        for row in self.cur.fetchall():
            genus, total_sp, ai_ready_sp, total_imgs = row
            pct = (ai_ready_sp / total_sp) * 100 if total_sp > 0 else 0
            print(f"   {genus:20} {ai_ready_sp:3}/{total_sp:4} species ({pct:5.1f}%), {total_imgs:6,} images")
        
        # Genera needing the most help
        print(f"\n⚠️  TOP 10 GENERA NEEDING HELP (Most Species, Least Coverage):")
        self.cur.execute("""
            SELECT 
                ot.genus,
                COUNT(DISTINCT ot.id) as total_sp,
                COUNT(DISTINCT CASE WHEN img_count > 0 THEN ot.id END) as sp_with_imgs,
                COALESCE(SUM(img_count), 0) as total_imgs
            FROM orchid_taxonomy ot
            LEFT JOIN (
                SELECT taxonomy_id, COUNT(*) as img_count
                FROM orchid_images
                GROUP BY taxonomy_id
            ) img_counts ON ot.id = img_counts.taxonomy_id
            WHERE ot.genus IS NOT NULL
            GROUP BY ot.genus
            HAVING COUNT(DISTINCT ot.id) > 20
            ORDER BY 
                (COUNT(DISTINCT CASE WHEN img_count > 0 THEN ot.id END)::float / COUNT(DISTINCT ot.id)) ASC,
                COUNT(DISTINCT ot.id) DESC
            LIMIT 10
        """)
        
        for row in self.cur.fetchall():
            genus, total_sp, sp_with_imgs, total_imgs = row
            pct = (sp_with_imgs / total_sp) * 100 if total_sp > 0 else 0
            print(f"   {genus:20} {sp_with_imgs:4}/{total_sp:4} species ({pct:5.1f}%), {total_imgs:6,} images")
        
        # Projected completion
        if recent and total_week > 0:
            images_needed = (total_species * 30) - total_images
            weeks_to_complete = images_needed / total_week
            completion_date = datetime.now() + timedelta(weeks=weeks_to_complete)
            
            print(f"\n📅 PROJECTIONS (at current rate):")
            print(f"   Weekly rate: {total_week:,} images/week")
            print(f"   Images needed for 100% AI-ready: {images_needed:,}")
            print(f"   Estimated weeks to completion: {weeks_to_complete:.1f} weeks")
            print(f"   Projected completion: {completion_date.strftime('%B %d, %Y')}")
        
        # Next milestones
        print(f"\n🎯 NEXT MILESTONES:")
        milestones = [
            (1000, "1K AI-ready species"),
            (5000, "5K AI-ready species"),
            (10000, "10K AI-ready species (28%)"),
            (17664, "50% AI-ready coverage"),
            (35327, "100% AI-READY COVERAGE! 🎉")
        ]
        
        for target, label in milestones:
            if ai_ready < target:
                remaining = target - ai_ready
                print(f"   {label:40} {remaining:,} species to go")
                if len([m for m, l in milestones if ai_ready < m]) >= 3:
                    break
        
        print("=" * 80 + "\n")
    
    def close(self):
        self.cur.close()
        self.conn.close()

def main():
    dashboard = CoverageDashboard()
    dashboard.display_dashboard()
    dashboard.close()

if __name__ == '__main__':
    main()
