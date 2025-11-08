from flask import Blueprint
from .routes import get_traits

traits_bp = Blueprint("traits", __name__)

@traits_bp.route("/traits/<int:plant_taxon_id>")
def traits_route(plant_taxon_id):
    return get_traits(plant_taxon_id)
