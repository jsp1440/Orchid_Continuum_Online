import os, sqlite3, json
from flask import jsonify, request

DB_PATH = os.environ.get("BB_DB_PATH", "bb.db")
LICENSE_WHITELIST = {"CC0", "CC-BY", "CC-BY 3.0", "CC-BY 4.0", "CC-BY-SA 3.0", "CC-BY-SA 4.0"}

def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _score_row(row):
    base = float(row["confidence"] or 0)
    return min(1.0, max(0.0, base + 0.1))

def get_pollinators():
    plant_taxon_id = request.args.get("plant_taxon_id", type=int)
    species_name = request.args.get("species_name", type=str)

    if not os.path.exists(DB_PATH):
        # fallback to sample JSON
        sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "pollinators.json")
        with open(sample_path) as f:
            data = json.load(f)
        return jsonify(data)

    if not plant_taxon_id and not species_name:
        return jsonify({"error": "Provide plant_taxon_id or species_name"}), 400

    conn = _connect()
    cur = conn.cursor()

    if species_name and not plant_taxon_id:
        cur.execute("SELECT id FROM taxon WHERE name = ? LIMIT 1", (species_name,))
        row = cur.fetchone()
        if row:
            plant_taxon_id = row["id"]

    q = """
    SELECT i.*, t.name as pollinator_name, t.rank as pollinator_rank,
           m.url as media_url, m.license as media_license, m.attribution as media_attribution,
           m.source as media_source, m.source_id as media_source_id, m.width, m.height
    FROM interaction i
    JOIN taxon t ON t.id = i.pollinator_taxon_id
    LEFT JOIN media m ON m.taxon_id = t.id
    WHERE i.plant_taxon_id = ?
    """
    cur.execute(q, (plant_taxon_id,))
    rows = cur.fetchall()
    conn.close()

    items = []
    for r in rows:
        lic = (r["media_license"] or "").strip()
        if lic and not any(lic.startswith(ok) for ok in LICENSE_WHITELIST):
            continue
        items.append({
            "taxon": {"id": r["pollinator_taxon_id"], "name": r["pollinator_name"], "rank": r["pollinator_rank"]},
            "interaction": {"predicate": r["predicate"], "confidence": float(r["confidence"] or 0), "source": r["source"], "evidence": r["evidence"]},
            "media": {"url": r["media_url"], "license": lic, "attribution": r["media_attribution"], "source": r["media_source"], "source_id": r["media_source_id"], "width": r["width"], "height": r["height"]},
            "score": _score_row(r)
        })

    items.sort(key=lambda x: (x["score"], x["interaction"]["confidence"]), reverse=True)
    return jsonify({"plant_taxon_id": plant_taxon_id, "pollinators": items[:3]})
