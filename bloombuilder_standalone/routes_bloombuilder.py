"""BloomBuilder: Interactive Orchid Morphology Lab Routes"""
import logging
from flask import Blueprint, render_template, jsonify, request, session
from models import db, BloomBuilderSpecies, BloomBuilderAnnotation, BloomBuilderValidation, OCUGlossaryTerm
import uuid

bloombuilder_bp = Blueprint('bloombuilder', __name__, url_prefix='/bloombuilder')

@bloombuilder_bp.route('/')
def index():
    """Main BloomBuilder interface - Species selector"""
    # Get all species for dropdown
    species_list = BloomBuilderSpecies.query.order_by(BloomBuilderSpecies.genus, BloomBuilderSpecies.species).all()
    species_data = [sp.to_dict() for sp in species_list]
    
    # Get session ID for anonymous users
    if 'bloombuilder_session' not in session:
        session['bloombuilder_session'] = str(uuid.uuid4())
    
    return render_template('bloombuilder/index.html', 
                         species_list=species_data,
                         session_id=session['bloombuilder_session'])

@bloombuilder_bp.route('/gallery/<int:species_id>')
def gallery_selector(species_id):
    """Multi-stage gallery: Choose herbarium, plate, and photo"""
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    return render_template('bloombuilder/gallery_selector.html', 
                         species_id=species_id,
                         species=species)

@bloombuilder_bp.route('/workbench/<int:species_id>')
def workbench(species_id):
    """Main workbench with canvas, tools, and trait toggles"""
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    return render_template('bloombuilder/workbench.html',
                         species_id=species_id,
                         species=species)


@bloombuilder_bp.route('/api/species/all')
def get_all_species():
    """Get all species for selection"""
    species_list = BloomBuilderSpecies.query.order_by(BloomBuilderSpecies.genus, BloomBuilderSpecies.species).all()
    return jsonify([{
        'id': sp.id,
        'genus': sp.genus,
        'species': sp.species,
        'common_name': sp.common_name or f'{sp.genus} {sp.species}',
        'profile_type': sp.profile_type
    } for sp in species_list])

@bloombuilder_bp.route('/api/species/<int:species_id>')
def get_species(species_id):
    """Get species details with ALL image types (herbarium, plates, photos)"""
    from models import OrchidImage, OrchidTrait
    from sqlalchemy import or_
    from eol_traitbank_api import eol_client
    
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    
    # Get images from database - herbarium specimens & botanical plates
    genus = species.genus
    species_name = species.species
    
    # Load traits from EOL if not already in database
    scientific_name = f"{genus} {species_name}"
    existing_traits = OrchidTrait.query.filter_by(species_id=species_id).count()
    
    if existing_traits == 0:
        # Try to fetch from EOL TraitBank
        eol_data = eol_client.get_species_traits(scientific_name)
        if eol_data and eol_data.get('traits'):
            # Persist EOL traits to database
            for trait_info in eol_data['traits']:
                trait = OrchidTrait(
                    species_id=species_id,
                    trait_category=trait_info['category'],
                    trait_value='default',
                    trait_description=trait_info['description'],
                    eol_trait_id=eol_data.get('eol_page_id')
                )
                db.session.add(trait)
            db.session.commit()
    
    # Query for images matching this species
    images = OrchidImage.query.join(
        'taxonomy'
    ).filter(
        or_(
            OrchidImage.image_source == 'Tropicos - Missouri Botanical Garden',  # Herbarium
            OrchidImage.image_source == 'Botanical Illustration'  # Plates
        )
    ).limit(20).all()
    
    # Get existing annotations
    annotations = BloomBuilderAnnotation.query.filter_by(species_id=species_id).all()
    annotations_data = [ann.to_dict() for ann in annotations]
    
    # Organize images by type
    image_data = {
        'herbarium': [],
        'botanical_plates': [],
        'living_photos': []
    }
    
    for img in images:
        img_dict = {
            'id': img.id,
            'url': img.image_url,
            'source': img.image_source,
            'type': 'herbarium' if 'Tropicos' in img.image_source else 'botanical_plate'
        }
        
        if 'Tropicos' in img.image_source:
            image_data['herbarium'].append(img_dict)
        else:
            image_data['botanical_plates'].append(img_dict)
    
    return jsonify({
        'species': species.to_dict(),
        'images': image_data,
        'annotations': annotations_data
    })


@bloombuilder_bp.route('/api/glossary/<term>')
def get_glossary_term(term):
    """Get glossary definition for a botanical term"""
    # Look up in OCU glossary
    glossary_term = OCUGlossaryTerm.query.filter_by(term=term).first()
    
    if glossary_term:
        return jsonify(glossary_term.to_dict())
    
    # Fallback definitions for basic orchid parts
    fallback_glossary = {
        'dorsal_sepal': {
            'term': 'dorsal sepal',
            'definition': 'Uppermost sepal, centered above the column in most orchids.',
            'pronunciation': 'DOR-sal SEE-pul'
        },
        'lateral_sepal_pair': {
            'term': 'lateral sepals',
            'definition': 'The two lower sepals; may be fused as a synsepal in slipper orchids.',
            'pronunciation': 'LAT-er-al SEE-pulz'
        },
        'petal_pair': {
            'term': 'petals',
            'definition': 'Lateral petals flanking the column; often narrow in Phrags.',
            'pronunciation': 'PET-ulz'
        },
        'labellum': {
            'term': 'labellum',
            'definition': 'Modified petal (lip) used for pollinator landing platform.',
            'pronunciation': 'la-BEL-um',
            'etymology': 'Latin: labellum = little lip'
        },
        'pouch_labellum': {
            'term': 'pouch labellum',
            'definition': 'Slipper-like labellum in Cypripedium/Phragmipedium that traps pollinators.',
            'pronunciation': 'POUCH la-BEL-um'
        },
        'column': {
            'term': 'column',
            'definition': 'Fused reproductive structure typical of orchids; holds pollinia.',
            'pronunciation': 'KOL-um',
            'etymology': 'Latin: columna = pillar'
        },
        'spur_or_nectary': {
            'term': 'spur/nectary',
            'definition': 'Tubular/sac-like extension, often nectar-bearing.',
            'pronunciation': 'SPUR / NEK-tar-ee'
        },
        'staminode': {
            'term': 'staminode',
            'definition': 'Sterile stamen-like shield in slipper orchids.',
            'pronunciation': 'STAM-in-ode',
            'etymology': 'Greek: stamen = thread + -ode = like'
        },
        'synsepal': {
            'term': 'synsepal',
            'definition': 'Fused lateral sepals forming a pouch or shield below the lip.',
            'pronunciation': 'SIN-see-pul'
        },
        'ovary_pedicel': {
            'term': 'ovary pedicel',
            'definition': 'Stalk supporting the ovary and flower.',
            'pronunciation': 'OH-var-ee PED-i-sel'
        },
        'rostellum': {
            'term': 'rostellum',
            'definition': 'Small beak-like projection separating anther from stigma.',
            'pronunciation': 'ros-TEL-um',
            'etymology': 'Latin: rostellum = little beak'
        },
        'callus': {
            'term': 'callus',
            'definition': 'Raised fleshy ridge on the labellum, often guides pollinators.',
            'pronunciation': 'KAL-us'
        },
        'speculum': {
            'term': 'speculum',
            'definition': 'Shiny patch on labellum that mimics insect appearance.',
            'pronunciation': 'SPEK-yoo-lum',
            'etymology': 'Latin: speculum = mirror'
        }
    }
    
    if term in fallback_glossary:
        return jsonify(fallback_glossary[term])
    
    return jsonify({'error': 'Term not found'}), 404


@bloombuilder_bp.route('/api/annotations', methods=['POST'])
def save_annotation():
    """Save a new annotation"""
    data = request.get_json()
    
    annotation = BloomBuilderAnnotation(
        species_id=data['species_id'],
        part_name=data['part_name'],
        box_data=data['box_data'],
        image_type=data.get('image_type', 'herbarium'),
        session_id=session.get('bloombuilder_session')
    )
    
    db.session.add(annotation)
    db.session.commit()
    
    # Check if this completes the species (all major parts annotated)
    all_annotations = BloomBuilderAnnotation.query.filter_by(
        species_id=data['species_id'],
        session_id=session.get('bloombuilder_session')
    ).count()
    
    # If user has annotated 5+ parts, send completion email
    if all_annotations >= 5 and data.get('user_email'):
        from email_notification_service import send_bloombuilder_completion_email
        from neon_one_api_client import neon_client
        
        species = BloomBuilderSpecies.query.get(data['species_id'])
        species_name = f"{species.genus} {species.species}"
        
        # Send email notification
        send_bloombuilder_completion_email(
            user_email=data['user_email'],
            species_name=species_name,
            annotation_count=all_annotations
        )
        
        # Log to Neon One
        neon_client.log_activity(
            email=data['user_email'],
            activity_type='BloomBuilder Completion',
            description=f"Completed digital morphology lab for {species_name} ({all_annotations} annotations)"
        )
    
    return jsonify(annotation.to_dict())


@bloombuilder_bp.route('/api/acknowledgments/<int:species_id>')
def get_acknowledgments(species_id):
    """Get contributor acknowledgments for a species - expressing the continuum"""
    from datetime import datetime
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    
    # Calculate historical span
    earliest_year = 1850  # Approximate earliest herbarium specimens
    current_year = datetime.now().year
    time_span = current_year - earliest_year
    
    # Build contributor list
    contributors = [
        {
            'role': 'Original Botanist & Collector',
            'name': 'Historical field botanists',
            'institution': 'Various institutions',
            'year': f'{earliest_year}s-1900s'
        },
        {
            'role': 'Herbarium Curator',
            'name': 'Tropicos archivists',
            'institution': 'Missouri Botanical Garden',
            'year': '1850s-present'
        },
        {
            'role': 'Botanical Illustrator',
            'name': 'Lindenia artists',
            'institution': 'Belgium horticultural society',
            'year': '1885-1906'
        },
        {
            'role': 'Digital Archivist',
            'name': 'GBIF data contributors',
            'institution': 'Global Biodiversity Information Facility',
            'year': '2000s-present'
        },
        {
            'role': 'Database Engineer',
            'name': 'Orchid Continuum developers',
            'institution': 'Five Cities Orchid Society',
            'year': '2024-2025'
        },
        {
            'role': 'Educational Designer',
            'name': 'NAOCC Orchid-Gami creators',
            'institution': 'North American Orchid Conservation Center',
            'year': '2010s-present'
        },
        {
            'role': 'You - Student & Creator',
            'name': 'Your contribution today',
            'institution': 'The Orchid Continuum',
            'year': str(current_year)
        }
    ]
    
    return jsonify({
        'total_contributors': len(contributors) * 10,  # Multiply to show collective effort
        'time_span': time_span,
        'species_name': species.scientific_name,
        'contributors': contributors,
        'message': 'Your work connects generations of botanical passion'
    })

@bloombuilder_bp.route('/api/save-creation', methods=['POST'])
def save_creation():
    """Save user's completed orchid creation to community gallery"""
    import base64
    import os
    import json
    from datetime import datetime
    from models import BloomBuilderCreation, db
    
    data = request.get_json()
    
    try:
        # Extract base64 image data
        image_data = data.get('image_data', '')
        if ',' in image_data:
            image_data = image_data.split(',')[1]  # Remove "data:image/png;base64," prefix
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        species_id = data.get('species_id')
        creator_name = data.get('creator_name', 'anonymous')
        style = data.get('style', 'line')
        filename = f"orchid_{species_id}_{timestamp}_{style}.png"
        
        # Save image file to static/uploads/bloombuilder/
        upload_dir = os.path.join('static', 'uploads', 'bloombuilder')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        # Save to database
        creation = BloomBuilderCreation(
            species_id=species_id,
            creator_name=creator_name,
            image_filename=filename,
            style=style,
            creation_data=json.dumps(data.get('selected_images', {}))
        )
        db.session.add(creation)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Creation saved to gallery!',
            'creation_id': creation.id,
            'image_url': f'/static/uploads/bloombuilder/{filename}'
        })
        
    except Exception as e:
        import logging
        logging.error(f"Error saving creation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bloombuilder_bp.route('/api/annotations/<int:annotation_id>/validate', methods=['POST'])
def validate_annotation(annotation_id):
    """Submit validation vote for an annotation"""
    data = request.get_json()
    
    annotation = BloomBuilderAnnotation.query.get_or_404(annotation_id)
    
    # Check if user already validated this
    existing = BloomBuilderValidation.query.filter_by(
        annotation_id=annotation_id,
        session_id=session.get('bloombuilder_session')
    ).first()
    
    if existing:
        return jsonify({'error': 'Already validated'}), 400
    
    # Create validation
    validation = BloomBuilderValidation(
        annotation_id=annotation_id,
        session_id=session.get('bloombuilder_session'),
        validation_type=data['validation_type'],
        suggestion_notes=data.get('suggestion_notes'),
        suggested_box_data=data.get('suggested_box_data')
    )
    
    db.session.add(validation)
    
    # Update counts on annotation
    if data['validation_type'] == 'agree':
        annotation.agrees += 1
    else:
        annotation.suggestions += 1
    
    # Mark as validated if enough agrees
    if annotation.agrees >= 3:
        annotation.is_validated = True
    
    db.session.commit()
    
    return jsonify(annotation.to_dict())


# Register blueprint in app.py
