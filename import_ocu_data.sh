#!/bin/bash
# Import OCU curriculum data via Flask shell

python3 << 'EOFPY'
import sys
sys.path.insert(0, '/home/runner/workspace')

# Import via Flask
from app import app
with app.app_context():
    from models import db, OCUCourse, OCULesson, OCUGlossaryTerm, GenusAbbreviation
    import csv
    import re
    from pathlib import Path
    
    print("🌺 ORCHID UNIVERSITY - DATA IMPORT")
    print("="*60)
    
    # Create tables
    print("📊 Creating tables...")
    db.create_all()
    print("✅ Tables created\n")
    
    # Import courses
    print("📚 Importing courses...")
    courses = [
        {'course_code': 'C1', 'title': 'Orchid Taxonomy & Identification', 'description': 'Learn how to read scientific names and understand taxonomic hierarchy.', 'order_num': 1, 'estimated_hours': 10, 'difficulty_level': 'beginner', 'companion_character': 'Sprig the Seedling', 'is_published': True},
        {'course_code': 'C2', 'title': 'Orchid Conservation & CITES', 'description': 'Understanding orchid conservation and international trade regulations.', 'order_num': 2, 'estimated_hours': 8, 'difficulty_level': 'intermediate', 'companion_character': 'FaeDra the Fairy', 'is_published': True}
    ]
    
    for cd in courses:
        if not OCUCourse.query.filter_by(course_code=cd['course_code']).first():
            db.session.add(OCUCourse(**cd))
            print(f"  ✅ {cd['course_code']}: {cd['title']}")
    db.session.commit()
    
    # Get course IDs
    c1 = OCUCourse.query.filter_by(course_code='C1').first()
    c2 = OCUCourse.query.filter_by(course_code='C2').first()
    
    # Import lessons
    print("\n📝 Importing lessons...")
    lessons = [
        {'course_id': c1.id, 'lesson_code': 'C1L1', 'title': 'Introduction to Orchid Names', 'summary': 'Understanding scientific names and binomial nomenclature.', 'order_num': 1, 'estimated_time_minutes': 45, 'is_published': True},
        {'course_id': c1.id, 'lesson_code': 'C1L2', 'title': 'Reading Orchid Name Tags', 'summary': 'Decoding nursery labels and understanding cultivar names.', 'order_num': 2, 'estimated_time_minutes': 50, 'is_published': True},
        {'course_id': c1.id, 'lesson_code': 'C1L3', 'title': 'The Orchidaceae Family Tree', 'summary': 'Overview of orchid subfamilies and evolutionary groups.', 'order_num': 3, 'estimated_time_minutes': 60, 'is_published': True},
        {'course_id': c1.id, 'lesson_code': 'C1L4', 'title': 'Genus vs Species', 'summary': 'Understanding genus and species in orchid classification.', 'order_num': 4, 'estimated_time_minutes': 50, 'is_published': True},
        {'course_id': c1.id, 'lesson_code': 'C1L5', 'title': 'Infraspecific Ranks', 'summary': 'Learning about subspecies, varieties, and forms.', 'order_num': 5, 'estimated_time_minutes': 55, 'is_published': True},
        {'course_id': c1.id, 'lesson_code': 'C1L6', 'title': 'Advanced Label Reading', 'summary': 'Mastering hybrid names and RHS registration.', 'order_num': 6, 'estimated_time_minutes': 60, 'is_published': True},
        {'course_id': c2.id, 'lesson_code': 'C2L2', 'title': 'CITES and International Trade', 'summary': 'Understanding CITES regulations and legal orchid trading.', 'order_num': 2, 'estimated_time_minutes': 70, 'is_published': True}
    ]
    
    for ld in lessons:
        if not OCULesson.query.filter_by(lesson_code=ld['lesson_code']).first():
            db.session.add(OCULesson(**ld))
            print(f"  ✅ {ld['lesson_code']}: {ld['title']}")
    db.session.commit()
    
    # Import glossary
    print("\n📖 Importing glossary terms...")
    glossary_file = Path('attached_assets/ocu_v0_2/attached_assets/glossaries/glossary_taxonomy.md')
    if glossary_file.exists():
        content = glossary_file.read_text()
        pattern = r'- \*\*(.+?)\*\* — (.+?)(?=\n|$)'
        matches = re.findall(pattern, content)
        
        for term, definition in matches:
            if not OCUGlossaryTerm.query.filter_by(term=term).first():
                db.session.add(OCUGlossaryTerm(term=term, definition=definition, category='taxonomy'))
        db.session.commit()
        print(f"  ✅ Imported {len(matches)} terms")
    
    # Import abbreviations
    print("\n🔤 Importing genus abbreviations...")
    csv_file = Path('attached_assets/orchid_genus_abbreviations 2_1761175940072.csv')
    if csv_file.exists():
        count = 0
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not GenusAbbreviation.query.filter_by(abbreviation=row['abbreviation'], full_genus=row['full_genus']).first():
                    db.session.add(GenusAbbreviation(abbreviation=row['abbreviation'], full_genus=row['full_genus'], pattern=row['pattern']))
                    count += 1
                    if count % 500 == 0:
                        db.session.commit()
        db.session.commit()
        print(f"  ✅ Imported {count} abbreviations")
    
    print("\n" + "="*60)
    print("✅ IMPORT COMPLETE!")
    
    # Show summary
    print(f"\n📊 DATABASE SUMMARY:")
    print(f"  Courses: {OCUCourse.query.count()}")
    print(f"  Lessons: {OCULesson.query.count()}")
    print(f"  Glossary Terms: {OCUGlossaryTerm.query.count()}")
    print(f"  Genus Abbreviations: {GenusAbbreviation.query.count()}")
EOFPY
