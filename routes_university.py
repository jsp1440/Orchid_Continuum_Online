"""
Orchid Continuum University - Routes
Academic botanical research platform for orchid education
"""

from flask import Blueprint, render_template, request, jsonify
from models import (db, OCUCourse, OCULesson, OCUGlossaryTerm, OCUUserProgress,
                   OCUQuizAttempt, OCUCertificate, GenusAbbreviation)
from sqlalchemy import func, or_
import logging

logger = logging.getLogger(__name__)

university_bp = Blueprint('university', __name__, url_prefix='/university')


@university_bp.route('/')
def index():
    """University home page - course catalog"""
    courses = OCUCourse.query.filter_by(is_published=True).order_by(OCUCourse.order_num).all()
    
    # Get lesson counts for each course
    course_data = []
    for course in courses:
        lessons = OCULesson.query.filter_by(course_id=course.id, is_published=True).count()
        course_dict = course.to_dict()
        course_dict['lesson_count'] = lessons
        course_data.append(course_dict)
    
    return render_template('university/index.html', courses=course_data)


@university_bp.route('/course/<course_code>')
def view_course(course_code):
    """View course details and lesson list"""
    course = OCUCourse.query.filter_by(course_code=course_code, is_published=True).first_or_404()
    lessons = OCULesson.query.filter_by(
        course_id=course.id,
        is_published=True
    ).order_by(OCULesson.order_num).all()
    
    return render_template('university/course.html', 
                         course=course,
                         lessons=lessons)


@university_bp.route('/lesson/<lesson_code>')
def view_lesson(lesson_code):
    """View individual lesson"""
    lesson = OCULesson.query.filter_by(lesson_code=lesson_code, is_published=True).first_or_404()
    course = lesson.course
    
    # Get next and previous lessons
    next_lesson = OCULesson.query.filter(
        OCULesson.course_id == course.id,
        OCULesson.order_num > lesson.order_num,
        OCULesson.is_published == True
    ).order_by(OCULesson.order_num).first()
    
    prev_lesson = OCULesson.query.filter(
        OCULesson.course_id == course.id,
        OCULesson.order_num < lesson.order_num,
        OCULesson.is_published == True
    ).order_by(OCULesson.order_num.desc()).first()
    
    return render_template('university/lesson.html',
                         lesson=lesson,
                         course=course,
                         next_lesson=next_lesson,
                         prev_lesson=prev_lesson)


@university_bp.route('/glossary')
def glossary():
    """Searchable glossary of orchid terms"""
    category = request.args.get('category', 'all')
    search = request.args.get('search', '')
    
    query = OCUGlossaryTerm.query
    
    if category != 'all':
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(
            or_(
                OCUGlossaryTerm.term.ilike(f'%{search}%'),
                OCUGlossaryTerm.definition.ilike(f'%{search}%')
            )
        )
    
    terms = query.order_by(OCUGlossaryTerm.term).all()
    
    # Get unique categories
    categories = db.session.query(OCUGlossaryTerm.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('university/glossary.html',
                         terms=terms,
                         categories=categories,
                         current_category=category,
                         search_query=search)


@university_bp.route('/genus-lookup')
def genus_lookup():
    """Genus abbreviation lookup tool"""
    search = request.args.get('search', '')
    
    if search:
        results = GenusAbbreviation.query.filter(
            or_(
                GenusAbbreviation.abbreviation.ilike(f'%{search}%'),
                GenusAbbreviation.full_genus.ilike(f'%{search}%')
            )
        ).limit(50).all()
    else:
        # Show popular examples
        results = GenusAbbreviation.query.filter(
            GenusAbbreviation.abbreviation.in_(['Phal.', 'Paph.', 'Catt.', 'Dend.', 'Onc.', 'Cyp.'])
        ).all()
    
    return render_template('university/genus_lookup.html',
                         results=results,
                         search_query=search)


@university_bp.route('/api/glossary/term/<int:term_id>')
def get_glossary_term(term_id):
    """API endpoint for glossary term popup"""
    term = OCUGlossaryTerm.query.get_or_404(term_id)
    
    # Increment view count
    term.view_count += 1
    db.session.commit()
    
    return jsonify(term.to_dict())


@university_bp.route('/api/abbreviation/<abbreviation>')
def lookup_abbreviation(abbreviation):
    """API endpoint for genus abbreviation lookup"""
    results = GenusAbbreviation.query.filter_by(abbreviation=abbreviation).all()
    return jsonify([r.to_dict() for r in results])


@university_bp.route('/word-playground')
def word_playground():
    """Interactive word-building game for learning botanical Greek/Latin roots"""
    
    # Define word-building challenges with prefixes, roots, and suffixes
    word_parts = {
        'prefixes': [
            {'affix': 'myco-', 'meaning': 'fungus', 'etymology': 'Greek: mykēs (mushroom)'},
            {'affix': 'epi-', 'meaning': 'upon, on', 'etymology': 'Greek: epi (upon)'},
            {'affix': 'endo-', 'meaning': 'within, inside', 'etymology': 'Greek: endon (within)'},
            {'affix': 'hetero-', 'meaning': 'different', 'etymology': 'Greek: heteros (other)'},
            {'affix': 'homo-', 'meaning': 'same', 'etymology': 'Greek: homos (same)'},
            {'affix': 'poly-', 'meaning': 'many', 'etymology': 'Greek: polys (many)'},
            {'affix': 'mono-', 'meaning': 'one, single', 'etymology': 'Greek: monos (alone)'},
            {'affix': 'macro-', 'meaning': 'large', 'etymology': 'Greek: makros (long, large)'},
            {'affix': 'micro-', 'meaning': 'small', 'etymology': 'Greek: mikros (small)'},
        ],
        'roots': [
            {'affix': 'rhiz', 'meaning': 'root', 'etymology': 'Greek: rhiza (root)'},
            {'affix': 'phyte', 'meaning': 'plant', 'etymology': 'Greek: phyton (plant)'},
            {'affix': 'morph', 'meaning': 'form, shape', 'etymology': 'Greek: morphē (form)'},
            {'affix': 'trop', 'meaning': 'turn', 'etymology': 'Greek: tropos (turn, direction)'},
            {'affix': 'phil', 'meaning': 'loving', 'etymology': 'Greek: philos (loving)'},
            {'affix': 'troph', 'meaning': 'nourishment', 'etymology': 'Greek: trophē (food)'},
            {'affix': 'bio', 'meaning': 'life', 'etymology': 'Greek: bios (life)'},
        ],
        'suffixes': [
            {'affix': '-al', 'meaning': 'relating to', 'etymology': 'Latin: -alis (pertaining to)'},
            {'affix': '-ism', 'meaning': 'condition, state', 'etymology': 'Greek: -ismos (action, state)'},
            {'affix': '-ous', 'meaning': 'full of, having', 'etymology': 'Latin: -osus (full of)'},
            {'affix': '-ic', 'meaning': 'pertaining to', 'etymology': 'Greek: -ikos (pertaining to)'},
            {'affix': '-ology', 'meaning': 'study of', 'etymology': 'Greek: -logia (study)'},
        ]
    }
    
    # Valid word combinations with definitions - MUST match validation dictionary
    valid_words = [
        {'word': 'mycorrhizal', 'parts': ['myco-', 'rhiz', '-al'], 'definition': 'Relating to fungus-root symbiotic association'},
        {'word': 'epiphytic', 'parts': ['epi-', 'phyte', '-ic'], 'definition': 'Plant growing upon another plant'},
        {'word': 'endotrophic', 'parts': ['endo-', 'troph', '-ic'], 'definition': 'Nourished from within'},
        {'word': 'heteromorphic', 'parts': ['hetero-', 'morph', '-ic'], 'definition': 'Having different forms'},
        {'word': 'homomorphic', 'parts': ['homo-', 'morph', '-ic'], 'definition': 'Having the same form'},
        {'word': 'polymorphic', 'parts': ['poly-', 'morph', '-ic'], 'definition': 'Having many forms'},
        {'word': 'monomorphic', 'parts': ['mono-', 'morph', '-ic'], 'definition': 'Having one form'},
        {'word': 'macromorphic', 'parts': ['macro-', 'morph', '-ic'], 'definition': 'Having large form'},
        {'word': 'micromorphic', 'parts': ['micro-', 'morph', '-ic'], 'definition': 'Having small form'},
        {'word': 'monobiotic', 'parts': ['mono-', 'bio', '-ic'], 'definition': 'Living in single habitat'},
        {'word': 'polybiotic', 'parts': ['poly-', 'bio', '-ic'], 'definition': 'Living in multiple habitats'},
    ]
    
    return render_template('university/word_playground.html',
                         word_parts=word_parts,
                         valid_words=valid_words)


@university_bp.route('/api/word-playground/validate', methods=['POST'])
def validate_word_combination():
    """API endpoint to validate word combinations"""
    data = request.get_json()
    parts = data.get('parts', [])
    
    # Valid combinations database - maps part sequences to canonical words
    # Format: tuple of parts -> {word, definition, score}
    valid_combinations = {
        ('myco-', 'rhiz', '-al'): {'word': 'mycorrhizal', 'definition': 'Relating to fungus-root symbiotic association', 'score': 100},
        ('epi-', 'phyte', '-ic'): {'word': 'epiphytic', 'definition': 'Plant growing upon another plant (not parasitic)', 'score': 100},
        ('endo-', 'troph', '-ic'): {'word': 'endotrophic', 'definition': 'Nourished from within; internal nutrition', 'score': 100},
        ('hetero-', 'morph', '-ic'): {'word': 'heteromorphic', 'definition': 'Having different forms or shapes', 'score': 100},
        ('homo-', 'morph', '-ic'): {'word': 'homomorphic', 'definition': 'Having the same form or shape', 'score': 100},
        ('poly-', 'morph', '-ic'): {'word': 'polymorphic', 'definition': 'Having many different forms', 'score': 100},
        ('mono-', 'morph', '-ic'): {'word': 'monomorphic', 'definition': 'Having a single uniform form', 'score': 100},
        ('macro-', 'morph', '-ic'): {'word': 'macromorphic', 'definition': 'Having large form or structure', 'score': 90},
        ('micro-', 'morph', '-ic'): {'word': 'micromorphic', 'definition': 'Having small form or structure', 'score': 90},
        ('mono-', 'bio', '-ic'): {'word': 'monobiotic', 'definition': 'Living in a single habitat or association', 'score': 90},
        ('poly-', 'bio', '-ic'): {'word': 'polybiotic', 'definition': 'Living in multiple habitats or associations', 'score': 90},
    }
    
    # Convert parts list to tuple for lookup
    parts_tuple = tuple(parts)
    
    # Check if this exact combination is valid
    if parts_tuple in valid_combinations:
        result = valid_combinations[parts_tuple]
        return jsonify({
            'valid': True,
            'word': result['word'],
            'definition': result['definition'],
            'score': result['score'],
            'message': f'✨ Excellent! You discovered: {result["word"].capitalize()}'
        })
    else:
        return jsonify({
            'valid': False,
            'word': ''.join(parts),
            'message': 'Not a valid botanical term. Try a different combination!',
            'score': 0
        })


@university_bp.route('/etymology-tree')
def etymology_tree():
    """Interactive etymology tree showing word relationships"""
    
    # Define root families and their derivatives
    etymology_tree_data = {
        'roots': [
            {
                'root': 'morph',
                'meaning': 'form, shape',
                'origin': 'Greek: morphē',
                'derivatives': [
                    {'word': 'polymorphic', 'prefix': 'poly-', 'meaning': 'many forms'},
                    {'word': 'monomorphic', 'prefix': 'mono-', 'meaning': 'one form'},
                    {'word': 'heteromorphic', 'prefix': 'hetero-', 'meaning': 'different forms'},
                    {'word': 'homomorphic', 'prefix': 'homo-', 'meaning': 'same form'},
                    {'word': 'macromorphic', 'prefix': 'macro-', 'meaning': 'large form'},
                    {'word': 'micromorphic', 'prefix': 'micro-', 'meaning': 'small form'},
                ]
            },
            {
                'root': 'phyte',
                'meaning': 'plant',
                'origin': 'Greek: phyton',
                'derivatives': [
                    {'word': 'epiphyte', 'prefix': 'epi-', 'meaning': 'plant growing upon'},
                    {'word': 'epiphytic', 'prefix': 'epi-', 'meaning': 'relating to plants growing upon'},
                ]
            },
            {
                'root': 'rhiz',
                'meaning': 'root',
                'origin': 'Greek: rhiza',
                'derivatives': [
                    {'word': 'mycorrhiza', 'prefix': 'myco-', 'meaning': 'fungus-root'},
                    {'word': 'mycorrhizal', 'prefix': 'myco-', 'meaning': 'relating to fungus-root'},
                ]
            },
            {
                'root': 'troph',
                'meaning': 'nourishment',
                'origin': 'Greek: trophē',
                'derivatives': [
                    {'word': 'endotrophic', 'prefix': 'endo-', 'meaning': 'nourished from within'},
                ]
            },
            {
                'root': 'bio',
                'meaning': 'life',
                'origin': 'Greek: bios',
                'derivatives': [
                    {'word': 'monobiotic', 'prefix': 'mono-', 'meaning': 'single life/habitat'},
                    {'word': 'polybiotic', 'prefix': 'poly-', 'meaning': 'multiple lives/habitats'},
                ]
            },
        ],
        'prefixes': [
            {
                'prefix': 'epi-',
                'meaning': 'upon, on',
                'origin': 'Greek: epi',
                'example_words': ['epiphyte', 'epiphytic', 'epidermis']
            },
            {
                'prefix': 'myco-',
                'meaning': 'fungus',
                'origin': 'Greek: mykēs',
                'example_words': ['mycorrhiza', 'mycology', 'mycobiont']
            },
            {
                'prefix': 'endo-',
                'meaning': 'within, inside',
                'origin': 'Greek: endon',
                'example_words': ['endotrophic', 'endosperm', 'endodermis']
            },
            {
                'prefix': 'poly-',
                'meaning': 'many',
                'origin': 'Greek: polys',
                'example_words': ['polymorphic', 'polybiotic', 'polycarpic']
            },
            {
                'prefix': 'mono-',
                'meaning': 'one, single',
                'origin': 'Greek: monos',
                'example_words': ['monomorphic', 'monobiotic', 'monopodial']
            },
        ]
    }
    
    return render_template('university/etymology_tree.html', tree_data=etymology_tree_data)


@university_bp.route('/companions')
def companions():
    """Meet the companion characters"""
    companions_data = [
        {
            'name': 'Sprig the Seedling',
            'role': 'Taxonomy Guide',
            'personality': 'Curious and detail-oriented',
            'course': 'C1',
            'bio': 'Sprig loves learning scientific names and can spot tiny details on orchid labels. Perfect companion for taxonomy students!'
        },
        {
            'name': 'Buzz the Bee',
            'role': 'Pollinator Expert',
            'personality': 'Energetic and social',
            'course': 'Pollination',
            'bio': 'Buzz knows everything about orchid-pollinator relationships and loves sharing stories from the field.'
        },
        {
            'name': 'Mica Myco',
            'role': 'Mycorrhizal Specialist',
            'personality': 'Scientific and thoughtful',
            'course': 'Ecology',
            'bio': 'Mica studies the hidden world of orchid-fungus partnerships beneath the soil.'
        },
        {
            'name': 'FaeDra the Fairy',
            'role': 'Conservation Advocate',
            'personality': 'Passionate and protective',
            'course': 'C2',
            'bio': 'FaeDra champions endangered orchids and helps students understand CITES and conservation.'
        },
        {
            'name': 'Finny the Hummingbird',
            'role': 'Explorer',
            'personality': 'Adventurous and quick',
            'course': 'Geography',
            'bio': 'Finny has visited orchid habitats worldwide and shares amazing travel stories.'
        }
    ]
    
    return render_template('university/companions.html', companions=companions_data)


@university_bp.route('/key-navigator')
def key_navigator():
    """Interactive dichotomous key navigator for species identification"""
    # Get all genera with keys from database
    query = """
        SELECT DISTINCT genus, 
               key_metadata->>'tags' as tags,
               key_metadata->>'geo_tags' as geography,
               COUNT(*) as key_count
        FROM orchid_taxonomic_keys
        WHERE genus IS NOT NULL
        GROUP BY genus, key_metadata->>'tags', key_metadata->>'geo_tags'
        ORDER BY genus
    """
    
    result = db.session.execute(db.text(query))
    genera = []
    for row in result:
        genera.append({
            'genus': row[0],
            'tags': row[1] or '',
            'geography': row[2] or '',
            'key_count': row[3]
        })
    
    return render_template('university/key_navigator.html', genera=genera)


@university_bp.route('/api/key-navigator/genus/<genus>')
def get_genus_keys(genus):
    """API endpoint to get all keys for a specific genus"""
    query = """
        SELECT id, genus, source_organization, source_url, 
               key_type, key_text, key_metadata
        FROM orchid_taxonomic_keys
        WHERE genus = :genus
        ORDER BY source_organization
    """
    
    result = db.session.execute(db.text(query), {'genus': genus})
    keys = []
    for row in result:
        metadata = row[6] if row[6] else {}
        keys.append({
            'id': row[0],
            'genus': row[1],
            'source': row[2],
            'url': row[3],
            'type': row[4],
            'description': row[5],
            'metadata': metadata
        })
    
    return jsonify(keys)


@university_bp.route('/api/glossary/search')
def search_glossary_terms():
    """API endpoint for glossary term search - used for key tooltips"""
    search_term = request.args.get('term', '').strip().lower()
    
    if not search_term:
        return jsonify([])
    
    terms = OCUGlossaryTerm.query.filter(
        OCUGlossaryTerm.term.ilike(f'%{search_term}%')
    ).limit(5).all()
    
    return jsonify([{
        'id': t.id,
        'term': t.term,
        'definition': t.definition,
        'etymology': t.etymology,
        'pronunciation': t.pronunciation
    } for t in terms])
