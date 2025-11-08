import json, os
from flask import jsonify
BASE = os.path.dirname(os.path.dirname(__file__))

def get_traits(plant_taxon_id: int):
    path = os.path.join(BASE, "sample_data", "traits.json")
    data = json.loads(open(path).read())
    items = data.get(str(plant_taxon_id), [])
    return jsonify({"plant_taxon_id": plant_taxon_id, "traits": items})
