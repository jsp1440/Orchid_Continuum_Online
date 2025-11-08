"""BloomBuilder: Interactive Orchid Morphology Lab Routes"""
import logging
from flask import Blueprint, render_template, jsonify, request, session
from models import (
    BloomBuilderSpecies, BloomBuilderAnnotation, BloomBuilderValidation,
    OCUGlossaryTerm, OrchidImage, OrchidTaxonomy, DichotomousKey
)
from app import db, csrf
from sqlalchemy import func, distinct
import uuid

bloombuilder_bp = Blueprint('bloombuilder', __name__, url_prefix='/bloombuilder')

@bloombuilder_bp.route('/')
def index():
    """Main BloomBuilder interface - Digital Orchid-Gami"""
    # Get all species for dropdown
    species_list = BloomBuilderSpecies.query.order_by(BloomBuilderSpecies.genus, BloomBuilderSpecies.species).all()
    species_data = [sp.to_dict() for sp in species_list]
    
    # Get session ID for anonymous users
    if 'bloombuilder_session' not in session:
        session['bloombuilder_session'] = str(uuid.uuid4())
    
    return render_template('bloombuilder/index.html', 
                         species_list=species_data,
                         session_id=session['bloombuilder_session'])


@bloombuilder_bp.route('/api/species/<int:species_id>')
def get_species(species_id):
    """Get species details with ALL image types (herbarium, plates, photos)"""
    from models import OrchidImage
    from sqlalchemy import or_
    
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    
    # Get taxonomy_id for this species
    scientific_name = f"{species.genus} {species.species}"
    taxonomy = OrchidTaxonomy.query.filter_by(scientific_name=scientific_name).first()
    
    if not taxonomy:
        # No matching taxonomy, return empty
        return jsonify({
            'species': species.to_dict(),
            'images': {'herbarium': [], 'botanical_plates': [], 'living_photos': []},
            'annotations': []
        })
    
    # Get images for this species from database (limit per type)
    # Herbarium sheets (Tropicos)
    herbarium = OrchidImage.query.filter_by(
        taxonomy_id=taxonomy.id,
        image_source='Tropicos - Missouri Botanical Garden'
    ).limit(10).all()
    
    # Botanical plates (EOL - Biodiversity Heritage Library)
    plates = OrchidImage.query.filter(
        OrchidImage.taxonomy_id == taxonomy.id,
        OrchidImage.image_source == 'EOL - Botanical Illustration',
        OrchidImage.image_rights_holder == 'Biodiversity Heritage Library'
    ).limit(10).all()
    
    # Living photos (GBIF + EOL photographers)
    photos = OrchidImage.query.filter(
        OrchidImage.taxonomy_id == taxonomy.id,
        or_(
            OrchidImage.image_source == 'GBIF',
            OrchidImage.image_rights_holder.notin_(['Biodiversity Heritage Library'])
        )
    ).limit(15).all()
    
    # Get existing annotations
    annotations = BloomBuilderAnnotation.query.filter_by(species_id=species_id).all()
    annotations_data = [ann.to_dict() for ann in annotations]
    
    # Format images with provenance metadata
    image_data = {
        'herbarium': [{
            'id': img.id,
            'url': img.image_url,
            'source': img.image_source,
            'collector': img.observer_name,
            'institution': img.institution_code,
            'locality': img.locality,
            'license': img.image_license
        } for img in herbarium],
        
        'botanical_plates': [{
            'id': img.id,
            'url': img.image_url,
            'source': img.image_source,
            'artist': img.image_rights_holder,
            'description': img.image_description,
            'page_id': img.eol_data_object_id,
            'year': img.locality,
            'license': img.image_license
        } for img in plates],
        
        'living_photos': [{
            'id': img.id,
            'url': img.image_url,
            'source': img.image_source,
            'photographer': img.observer_name or img.image_rights_holder,
            'license': img.image_license
        } for img in photos]
    }
    
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
@csrf.exempt
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


@bloombuilder_bp.route('/api/annotations/<int:annotation_id>/validate', methods=['POST'])
@csrf.exempt
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


@bloombuilder_bp.route('/api/contributors/stats')
def get_contributor_stats():
    """Get real contributor statistics from database"""
    # Get stats from orchid_images table
    img_stats = db.session.query(
        func.count(distinct(OrchidImage.observer_name)).label('observers'),
        func.count(distinct(OrchidImage.institution_code)).label('institutions'),
        func.min(OrchidImage.observation_date).label('earliest_date'),
        func.max(OrchidImage.observation_date).label('latest_date')
    ).filter(OrchidImage.observation_date.isnot(None)).first()
    
    # Calculate years span
    if img_stats.earliest_date and img_stats.latest_date:
        years_span = img_stats.latest_date.year - img_stats.earliest_date.year
    else:
        years_span = 0
    
    # Total unique contributors (observers + institutions)
    total_contributors = (img_stats.observers or 0) + (img_stats.institutions or 0)
    
    # Get counts of data sources
    glossary_count = db.session.query(func.count(OCUGlossaryTerm.id)).scalar()
    species_count = db.session.query(func.count(BloomBuilderSpecies.id)).scalar()
    images_count = db.session.query(func.count(OrchidImage.id)).scalar()
    
    return jsonify({
        'total_contributors': total_contributors,
        'years_span': years_span,
        'earliest_year': img_stats.earliest_date.year if img_stats.earliest_date else None,
        'latest_year': img_stats.latest_date.year if img_stats.latest_date else None,
        'observers_count': img_stats.observers or 0,
        'institutions_count': img_stats.institutions or 0,
        'glossary_terms': glossary_count or 0,
        'species_available': species_count or 0,
        'images_available': images_count or 0
    })


@bloombuilder_bp.route('/api/species/all')
def get_all_species():
    """Get all species for species selection"""
    species_list = BloomBuilderSpecies.query.order_by(
        BloomBuilderSpecies.genus, 
        BloomBuilderSpecies.species
    ).all()
    
    return jsonify([{
        'id': sp.id,
        'genus': sp.genus,
        'species': sp.species,
        'common_name': sp.common_name,
        'profile_type': sp.profile_type
    } for sp in species_list])


@bloombuilder_bp.route('/api/species/<int:species_id>/key')
def get_dichotomous_key(species_id):
    """Get dichotomous key for a species with glossary terms extracted from database"""
    from models import DichotomousKey
    import re
    
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    
    # Load ALL glossary terms from database with aliases/variants
    glossary_terms_db = OCUGlossaryTerm.query.all()
    
    # Build comprehensive term matching dictionary
    term_lookup = {}
    for gt in glossary_terms_db:
        # Add main term
        term_lower = gt.term.lower().strip()
        term_lookup[term_lower] = {
            'id': gt.id,
            'term': gt.term,
            'definition': gt.definition
        }
        
        # Add common variants/aliases
        if 'sepal' in term_lower:
            term_lookup[term_lower.replace('sepal', 'sepals')] = term_lookup[term_lower]
        if 'petal' in term_lower:
            term_lookup[term_lower.replace('petal', 'petals')] = term_lookup[term_lower]
        
        # Handle multi-word terms (e.g., "dorsal sepal" → also match "dorsal")
        if ' ' in term_lower:
            for word in term_lower.split():
                if len(word) > 3:  # Only match words longer than 3 chars
                    term_lookup[word] = term_lookup[term_lower]
    
    # Get key entries for this genus/species
    key_entries = DichotomousKey.query.filter(
        DichotomousKey.taxon_name.ilike(f'%{species.genus}%')
    ).order_by(DichotomousKey.key_number).all()
    
    def extract_glossary_terms(description):
        """Extract glossary terms from description using database vocabulary"""
        if not description:
            return []
        
        found_terms = []
        description_lower = description.lower()
        
        # Sort terms by length (longest first) to match "dorsal sepal" before "sepal"
        sorted_terms = sorted(term_lookup.keys(), key=len, reverse=True)
        
        seen_ids = set()
        for term in sorted_terms:
            if term in description_lower:
                term_data = term_lookup[term]
                term_id = term_data['id']
                
                # Avoid duplicates (same glossary entry matched multiple ways)
                if term_id not in seen_ids:
                    found_terms.append({
                        'id': term_id,
                        'term': term_data['term'],
                        'definition': term_data['definition']
                    })
                    seen_ids.add(term_id)
        
        return found_terms
    
    if key_entries:
        return jsonify([{
            'id': entry.id,
            'key_number': entry.key_number,
            'lead_number': entry.lead_number,
            'description': entry.description,
            'taxon_name': entry.taxon_name,
            'source': entry.source_name,
            'glossary_terms': extract_glossary_terms(entry.description)
        } for entry in key_entries])
    
    # Fallback: Generic orchid key structure
    generic_key = [
        {
            'key_number': 1,
            'lead_number': 'a',
            'description': 'Column with distinct staminode; lateral sepals fused into synsepal',
            'taxon_name': 'Slipper orchids (Cypripedioideae)',
            'glossary_terms': ['column', 'staminode', 'synsepal']
        },
        {
            'key_number': 1,
            'lead_number': 'b',
            'description': 'Column without staminode; lateral sepals separate',
            'taxon_name': 'Other orchids',
            'glossary_terms': ['column', 'sepals']
        },
        {
            'key_number': 2,
            'lead_number': 'a',
            'description': 'Labellum pouch-shaped; slipper-like',
            'taxon_name': f'{species.genus}',
            'glossary_terms': ['labellum', 'pouch']
        },
        {
            'key_number': 2,
            'lead_number': 'b',
            'description': 'Labellum flat or cupped; not pouch-shaped',
            'taxon_name': 'Other taxa',
            'glossary_terms': ['labellum']
        }
    ]
    
    return jsonify(generic_key)


@bloombuilder_bp.route('/api/species/<int:species_id>/traits')
def get_species_traits(species_id):
    """Get known trait variations for a species"""
    species = BloomBuilderSpecies.query.get_or_404(species_id)
    
    # Known trait variations - these would come from treatment bank in full system
    traits = {
        'spur_length': ['short (<5mm)', 'medium (5-15mm)', 'long (>15mm)'],
        'petal_orientation': ['spreading', 'reflexed', 'forward-facing'],
        'color_morph': ['typical', 'alba (white)', 'flavum (yellow)', 'rubrum (red)'],
        'labellum_shape': ['typical', 'peloric (all petals lip-like)', 'semi-peloric'],
        'fragrance': ['none', 'light', 'strong']
    }
    
    return jsonify({
        'species': species.to_dict(),
        'available_traits': traits
    })


@bloombuilder_bp.route('/api/images/<int:image_id>/metadata')
def get_image_metadata(image_id):
    """Get full metadata for an image including EXIF and provenance"""
    image = OrchidImage.query.get_or_404(image_id)
    
    # Build provenance caption
    provenance = {
        'collector': image.observer_name or 'Unknown',
        'date': str(image.observation_date) if image.observation_date else 'Date unknown',
        'locality': image.locality or 'Location not recorded',
        'institution': image.institution_code or image.image_source,
        'source_url': image.source_url or image.image_url,
        'license': image.license_info or 'See source for license details'
    }
    
    # EXIF-like data
    metadata = {
        'id': image.id,
        'url': image.image_url,
        'type': 'herbarium' if 'Tropicos' in (image.image_source or '') else 
                'plate' if 'Illustration' in (image.image_source or '') else 'photo',
        'provenance': provenance,
        'location': {
            'latitude': image.latitude,
            'longitude': image.longitude,
            'locality': image.locality
        },
        'taxonomy': {
            'genus': image.genus_name,
            'species': image.species_epithet,
            'infraspecific': image.infraspecific_epithet
        }
    }
    
    return jsonify(metadata)


# Register blueprint in app.py
