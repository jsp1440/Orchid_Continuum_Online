import os, json, sqlite3, pathlib
DB_PATH = os.environ.get("BB_DB_PATH", "bb.db")
BASE = pathlib.Path(__file__).resolve().parent.parent

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open(BASE / "migrations" / "schema.sql") as f:
        cur.executescript(f.read())

    data = json.loads(open(BASE / "sample_data" / "pollinators.json").read())

    def upsert_taxon(name, rank, source="local", source_id=None):
        cur.execute("SELECT id FROM taxon WHERE name = ? LIMIT 1", (name,))
        row = cur.fetchone()
        if row: return row[0]
        cur.execute("INSERT INTO taxon (name, rank, source, source_id) VALUES (?,?,?,?)", (name, rank, source, source_id))
        return cur.lastrowid

    plant_id = upsert_taxon(data["plant_taxon"]["name"], data["plant_taxon"].get("rank","species"), "local", str(data["plant_taxon"]["id"]))

    for p in data["pollinators"]:
        pol_id = upsert_taxon(p["taxon"]["name"], p["taxon"].get("rank","species"), "local", str(p["taxon"]["id"]))
        it = p["interaction"]
        cur.execute("INSERT INTO interaction (plant_taxon_id, pollinator_taxon_id, predicate, source, evidence, confidence) VALUES (?,?,?,?,?,?)",
                    (plant_id, pol_id, it.get("predicate"), it.get("source"), None, float(it.get("confidence",0))))
        m = p.get("media")
        if m:
            cur.execute("INSERT INTO media (taxon_id, url, license, attribution, source, source_id, width, height) VALUES (?,?,?,?,?,?,?,?)",
                        (pol_id, m.get("url"), m.get("license"), m.get("attribution"), m.get("source"), m.get("source_id"), m.get("width"), m.get("height")))

    conn.commit()
    conn.close()
    print("Seed complete. Try: /api/pollinators?species_name=Phragmipedium kovachii")

if __name__ == "__main__":
    main()
