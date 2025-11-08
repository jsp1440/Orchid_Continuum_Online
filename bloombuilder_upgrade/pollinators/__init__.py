from flask import Blueprint
from .routes import get_pollinators

pollinators_bp = Blueprint("pollinators", __name__)

@pollinators_bp.route("/pollinators")
def pollinators_route():
    return get_pollinators()
