"""BloomBuilder Database Models - Standalone"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class BloomBuilderSpecies(db.Model):
    __tablename__ = 'bloombuilder_species'
    
    id = db.Column(db.Integer, primary_key=True)
    genus = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(100), nullable=False)
    common_name = db.Column(db.String(200))
    profile_type = db.Column(db.String(50))  # pouch_orchid, spurred_orchid, default_orchid
    habitat = db.Column(db.Text)
    distribution = db.Column(db.Text)
    pollinators = db.Column(db.Text)
    conservation_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'genus': self.genus,
            'species': self.species,
            'common_name': self.common_name,
            'profile_type': self.profile_type,
            'habitat': self.habitat,
            'distribution': self.distribution,
            'pollinators': self.pollinators,
            'conservation_status': self.conservation_status
        }

class BloomBuilderAnnotation(db.Model):
    __tablename__ = 'bloombuilder_annotations'
    
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('bloombuilder_species.id'))
    part_name = db.Column(db.String(100), nullable=False)
    box_data = db.Column(db.Text, nullable=False)  # JSON string
    image_type = db.Column(db.String(50))  # herbarium, botanical_plate, photo
    session_id = db.Column(db.String(100))
    is_validated = db.Column(db.Boolean, default=False)
    agrees = db.Column(db.Integer, default=0)
    suggestions = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'species_id': self.species_id,
            'part_name': self.part_name,
            'box_data': self.box_data,
            'image_type': self.image_type,
            'is_validated': self.is_validated,
            'agrees': self.agrees,
            'suggestions': self.suggestions
        }

class BloomBuilderValidation(db.Model):
    __tablename__ = 'bloombuilder_validations'
    
    id = db.Column(db.Integer, primary_key=True)
    annotation_id = db.Column(db.Integer, db.ForeignKey('bloombuilder_annotations.id'))
    session_id = db.Column(db.String(100))
    validation_type = db.Column(db.String(20))  # 'agree' or 'suggest'
    suggestion_notes = db.Column(db.Text)
    suggested_box_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OCUGlossaryTerm(db.Model):
    __tablename__ = 'ocu_glossary_terms'
    
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(200), unique=True)
    definition = db.Column(db.Text)
    pronunciation = db.Column(db.String(200))
    etymology = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'term': self.term,
            'definition': self.definition,
            'pronunciation': self.pronunciation,
            'etymology': self.etymology
        }

class OrchidImage(db.Model):
    __tablename__ = 'orchid_images'
    
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(500))
    image_source = db.Column(db.String(200))
    local_path = db.Column(db.String(500))
    image_license = db.Column(db.String(200))
    download_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BloomBuilderCreation(db.Model):
    """User-created orchid illustrations - the final puzzle pieces!"""
    __tablename__ = 'bloombuilder_creations'
    
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('bloombuilder_species.id'))
    creator_name = db.Column(db.String(200), nullable=False)
    image_filename = db.Column(db.String(500), nullable=False)  # Stored in static/uploads/bloombuilder/
    style = db.Column(db.String(50))  # line, watercolor, oil, coloring, origami, wallpaper
    herbarium_image_id = db.Column(db.Integer)  # Track which images they chose
    plate_image_id = db.Column(db.Integer)
    photo_image_id = db.Column(db.Integer)
    creation_data = db.Column(db.Text)  # JSON with full selections and metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'species_id': self.species_id,
            'creator_name': self.creator_name,
            'image_url': f'/static/uploads/bloombuilder/{self.image_filename}',
            'style': self.style,
            'created_at': self.created_at.isoformat()
        }

class OrchidTrait(db.Model):
    """Morphological traits for evolutionary trait variation"""
    __tablename__ = 'orchid_traits'
    
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('bloombuilder_species.id'))
    trait_category = db.Column(db.String(100))  # spur_length, labellum_shape, petal_color
    trait_value = db.Column(db.String(100))  # long, pouch, purple
    trait_description = db.Column(db.Text)
    image_url = db.Column(db.String(500))  # Image showing THIS phenotype
    herbarium_specimen_id = db.Column(db.Integer, db.ForeignKey('orchid_images.id'))
    pollinator_association = db.Column(db.String(200))  # "Attracts sphinx moths"
    evolutionary_significance = db.Column(db.Text)
    eol_trait_id = db.Column(db.String(100))  # EOL TraitBank reference
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'species_id': self.species_id,
            'trait_category': self.trait_category,
            'trait_value': self.trait_value,
            'trait_description': self.trait_description,
            'image_url': self.image_url,
            'pollinator_association': self.pollinator_association,
            'evolutionary_significance': self.evolutionary_significance
        }

class TraitVariation(db.Model):
    """Comparison of trait variations across populations/species"""
    __tablename__ = 'trait_variations'
    
    id = db.Column(db.Integer, primary_key=True)
    base_trait_id = db.Column(db.Integer, db.ForeignKey('orchid_traits.id'))
    variant_name = db.Column(db.String(200))  # "Short vs Long Spur"
    variant_type = db.Column(db.String(100))  # morphology, color, size
    comparison_data = db.Column(db.Text)  # JSON with comparative measurements
    geographic_distribution = db.Column(db.Text)
    selective_pressure = db.Column(db.Text)  # "Longer spurs in moth-pollinated populations"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
