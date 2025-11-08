#!/usr/bin/env python3
"""
Import Orchid Continuum University curriculum from Julius's v0.2 package
"""

from app import app, db
from models import (OCUCourse, OCULesson, OCUGlossaryTerm, GenusAbbreviation)
import json
import csv
from pathlib import Path
import re

def create_tables():
    """Create OCU database tables"""
    with app.app_context():
        print("📊 Creating Orchid University tables...")
        db.create_all()
        print("✅ Tables created successfully")

def import_courses():
    """Import course definitions"""
    with app.app_context():
        print("\n📚 Importing courses...")
        
        courses_data = [
            {
                'course_code': 'C1',
                'title': 'Orchid Taxonomy & Identification',
                'description': 'Learn how to read scientific names, understand taxonomic hierarchy, and identify orchids using proper botanical nomenclature.',
                'order_num': 1,
                'estimated_hours': 10,
                'difficulty_level': 'beginner',
                'companion_character': 'Sprig the Seedling',
                'is_published': True
            },
            {
                'course_code': 'C2',
                'title': 'Orchid Conservation & CITES',
                'description': 'Understanding orchid conservation, endangered species, and international trade regulations.',
                'order_num': 2,
                'estimated_hours': 8,
                'difficulty_level': 'intermediate',
                'companion_character': 'FaeDra the Fairy',
                'is_published': True
            }
        ]
        
        for course_data in courses_data:
            existing = OCUCourse.query.filter_by(course_code=course_data['course_code']).first()
            if not existing:
                course = OCUCourse(**course_data)
                db.session.add(course)
                print(f"  ✅ Added {course_data['course_code']}: {course_data['title']}")
            else:
                print(f"  ⏭️  Course {course_data['course_code']} already exists")
        
        db.session.commit()
        print("✅ Courses imported")

def import_lessons():
    """Import lesson content from OCU v0.2"""
    with app.app_context():
        print("\n📝 Importing lessons...")
        
        # Get course IDs
        c1 = OCUCourse.query.filter_by(course_code='C1').first()
        c2 = OCUCourse.query.filter_by(course_code='C2').first()
        
        if not c1 or not c2:
            print("❌ Courses not found. Run import_courses() first.")
            return
        
        lessons_data = [
            {
                'course_id': c1.id,
                'lesson_code': 'C1L1',
                'title': 'Introduction to Orchid Names',
                'summary': 'Understanding scientific names, binomial nomenclature, and why botanical names matter.',
                'order_num': 1,
                'estimated_time_minutes': 45,
                'is_published': True
            },
            {
                'course_id': c1.id,
                'lesson_code': 'C1L2',
                'title': 'Reading Orchid Name Tags',
                'summary': 'Decoding nursery labels, understanding authors, varieties, and cultivar names.',
                'order_num': 2,
                'estimated_time_minutes': 50,
                'is_published': True
            },
            {
                'course_id': c1.id,
                'lesson_code': 'C1L3',
                'title': 'The Orchidaceae Family Tree',
                'summary': 'Overview of orchid subfamilies, tribes, and major evolutionary groups.',
                'order_num': 3,
                'estimated_time_minutes': 60,
                'is_published': True
            },
            {
                'course_id': c1.id,
                'lesson_code': 'C1L4',
                'title': 'Genus vs Species',
                'summary': 'Understanding the relationship between genus and species names in orchid classification.',
                'order_num': 4,
                'estimated_time_minutes': 50,
                'is_published': True
            },
            {
                'course_id': c1.id,
                'lesson_code': 'C1L5',
                'title': 'Infraspecific Ranks',
                'summary': 'Learning about subspecies, varieties, and forms in orchid taxonomy.',
                'order_num': 5,
                'estimated_time_minutes': 55,
                'is_published': True
            },
            {
                'course_id': c1.id,
                'lesson_code': 'C1L6',
                'title': 'Advanced Label Reading',
                'summary': 'Mastering complex hybrid names, grex names, and RHS registration.',
                'order_num': 6,
                'estimated_time_minutes': 60,
                'is_published': True
            },
            {
                'course_id': c2.id,
                'lesson_code': 'C2L2',
                'title': 'CITES and International Trade',
                'summary': 'Understanding CITES regulations, permits, and legal orchid trading.',
                'order_num': 2,
                'estimated_time_minutes': 70,
                'is_published': True
            }
        ]
        
        for lesson_data in lessons_data:
            existing = OCULesson.query.filter_by(lesson_code=lesson_data['lesson_code']).first()
            if not existing:
                lesson = OCULesson(**lesson_data)
                db.session.add(lesson)
                print(f"  ✅ Added {lesson_data['lesson_code']}: {lesson_data['title']}")
            else:
                print(f"  ⏭️  Lesson {lesson_data['lesson_code']} already exists")
        
        db.session.commit()
        print("✅ Lessons imported")

def import_glossary():
    """Import glossary terms from Julius's taxonomy glossary"""
    with app.app_context():
        print("\n📖 Importing glossary terms...")
        
        glossary_file = Path('attached_assets/ocu_v0_2/attached_assets/glossaries/glossary_taxonomy.md')
        
        if not glossary_file.exists():
            print(f"❌ Glossary file not found: {glossary_file}")
            return
        
        content = glossary_file.read_text()
        
        # Parse markdown glossary (- **Term** — Definition)
        pattern = r'- \*\*(.+?)\*\* — (.+?)(?=\n|$)'
        matches = re.findall(pattern, content)
        
        for term, definition in matches:
            existing = OCUGlossaryTerm.query.filter_by(term=term).first()
            if not existing:
                glossary_term = OCUGlossaryTerm(
                    term=term,
                    definition=definition,
                    category='taxonomy'
                )
                db.session.add(glossary_term)
                print(f"  ✅ Added term: {term}")
            else:
                print(f"  ⏭️  Term '{term}' already exists")
        
        db.session.commit()
        print(f"✅ Imported {len(matches)} glossary terms")

def import_genus_abbreviations():
    """Import genus abbreviations from Julius's CSV"""
    with app.app_context():
        print("\n🔤 Importing genus abbreviations...")
        
        csv_file = Path('attached_assets/orchid_genus_abbreviations 2_1761175940072.csv')
        
        if not csv_file.exists():
            print(f"❌ CSV file not found: {csv_file}")
            return
        
        count = 0
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing = GenusAbbreviation.query.filter_by(
                    abbreviation=row['abbreviation'],
                    full_genus=row['full_genus']
                ).first()
                
                if not existing:
                    abbrev = GenusAbbreviation(
                        abbreviation=row['abbreviation'],
                        full_genus=row['full_genus'],
                        pattern=row['pattern']
                    )
                    db.session.add(abbrev)
                    count += 1
                    
                    if count % 500 == 0:
                        db.session.commit()
                        print(f"  ... {count} abbreviations imported")
        
        db.session.commit()
        print(f"✅ Imported {count} genus abbreviations")

def main():
    """Run all imports"""
    print("🌺 ORCHID CONTINUUM UNIVERSITY - CURRICULUM IMPORT")
    print("="*60)
    
    create_tables()
    import_courses()
    import_lessons()
    import_glossary()
    import_genus_abbreviations()
    
    print("\n" + "="*60)
    print("✅ IMPORT COMPLETE!")
    print("\nNext steps:")
    print("1. Create frontend routes at /university/")
    print("2. Build lesson viewer templates")
    print("3. Add glossary search interface")
    print("4. Test the complete system")

if __name__ == '__main__':
    main()
