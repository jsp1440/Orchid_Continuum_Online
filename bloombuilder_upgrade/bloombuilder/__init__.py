from flask import Blueprint, render_template, request

bb_bp = Blueprint("bloombuilder", __name__, template_folder="templates", static_folder="static")

@bb_bp.route("/widget")
def widget():
    # For demo purposes we pass a single species; wire your species list as needed
    species_name = request.args.get("species_name", "Phragmipedium kovachii")
    plant_taxon_id = 12345
    return render_template("widget.html", species_name=species_name, plant_taxon_id=plant_taxon_id)
