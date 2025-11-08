import os, random
from urllib.parse import urlparse
from flask import Blueprint, jsonify, request, render_template
import psycopg2, psycopg2.extras

verify_bp = Blueprint("verify", __name__, url_prefix="/verify")
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set.")
    return psycopg2.connect(DATABASE_URL, sslmode=urlparse(DATABASE_URL).query or "require")

def safe_url(obj):
    try: return obj.get("url")
    except Exception: return None

def to_payload(row):
    return {
        "result_id": row["id"],
        "orchid_id": row["orchid_id"],
        "image_path": row["image_path"],
        "ai_guess": {
            "genus": row["final_genus"],
            "species": row["final_species"],
            "confidence": float(row["final_confidence"]) if row["final_confidence"] is not None else None,
            "status": row["status"],
        },
        "links": {
            "powo": safe_url(row["powo_match"]) if row["powo_match"] else None,
            "gbif": safe_url(row["gbif_match"]) if row["gbif_match"] else None,
            "eol":  safe_url(row["eol_match"])  if row["eol_match"]  else None,
        },
    }

@verify_bp.route("/play")
def play():
    return render_template("verify_play.html")

@verify_bp.route("/api/next")
def api_next():
    member_id = request.headers.get("X-Member-ID")
    status = request.args.get("status", "pending")
    exclude_voted = request.args.get("exclude_voted", "true").lower()=="true"

    join_clause, where_status, where_exclude, params = "", "", "", []
    if status in ("pending","flagged","accepted","corrected"):
        where_status = "AND r.status = %s"; params.append(status)
    if exclude_voted and member_id and member_id.isdigit():
        join_clause = "LEFT JOIN image_validation_feedback v ON v.result_id=r.id AND v.member_id=%s"
        params = [int(member_id)] + params
        where_exclude = "AND v.result_id IS NULL"

    sql = f"""
      SELECT r.id, r.orchid_id, r.image_path, r.final_genus, r.final_species, r.final_confidence,
             r.status, r.powo_match, r.gbif_match, r.eol_match
      FROM image_validation_results r
      {join_clause}
      WHERE 1=1
        {where_status}
        {where_exclude}
      ORDER BY r.created_at DESC
      LIMIT 50;
    """
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    if not rows:
        with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""SELECT r.id, r.orchid_id, r.image_path, r.final_genus, r.final_species, r.final_confidence,
                                  r.status, r.powo_match, r.gbif_match, r.eol_match
                           FROM image_validation_results r
                           ORDER BY r.created_at DESC LIMIT 50;""")
            rows = cur.fetchall()
    if not rows:
        return jsonify({"item": None})
    return jsonify({"item": to_payload(random.choice(rows))})

@verify_bp.route("/api/vote", methods=["POST"])
def api_vote():
    data = request.get_json(force=True, silent=True) or {}
    result_id = data.get("result_id")
    decision = (data.get("decision") or "").lower().strip()
    sug_g = (data.get("suggested_genus") or "").strip() or None
    sug_s = (data.get("suggested_species") or "").strip() or None
    notes  = (data.get("notes") or "").strip() or None

    if not result_id or decision not in ("agree","disagree","corrected"):
        return jsonify({"ok": False, "error": "Invalid payload"}), 400

    member_param = request.args.get("member_id") or request.headers.get("X-Member-ID")
    member_id = int(member_param) if (member_param and str(member_param).isdigit()) else None

    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        if member_id is not None:
            cur.execute("""
              INSERT INTO image_validation_feedback (result_id, member_id, reviewer, decision, correct_genus, correct_species, notes)
              VALUES (%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT (result_id, member_id) DO UPDATE
                 SET decision=EXCLUDED.decision,
                     correct_genus=EXCLUDED.correct_genus,
                     correct_species=EXCLUDED.correct_species,
                     notes=EXCLUDED.notes
              RETURNING feedback_id, created_at;
            """, (result_id, member_id, str(member_id), decision, sug_g, sug_s, notes))
        else:
            cur.execute("""
              INSERT INTO image_validation_feedback (result_id, reviewer, decision, correct_genus, correct_species, notes)
              VALUES (%s,%s,%s,%s,%s,%s) RETURNING feedback_id, created_at;
            """, (result_id, "anonymous", decision, sug_g, sug_s, notes))
        fb = cur.fetchone()

        cur.execute("""
          WITH votes AS (
            SELECT f.decision, f.correct_genus, f.correct_species,
                   COALESCE(m.expertise_score,1.0) AS w
            FROM image_validation_feedback f
            LEFT JOIN member_reputation m ON m.member_id=f.member_id
            WHERE f.result_id=%s
          ),
          agg AS (
            SELECT
              SUM(CASE WHEN decision='agree'     THEN w ELSE 0 END) AS w_agree,
              SUM(CASE WHEN decision='corrected' THEN w ELSE 0 END) AS w_corrected
            FROM votes
          ),
          corrections AS (
            SELECT correct_genus, correct_species, SUM(w) AS w_cnt
            FROM votes WHERE decision='corrected' AND correct_genus IS NOT NULL
            GROUP BY correct_genus, correct_species
            ORDER BY w_cnt DESC, correct_genus ASC LIMIT 1
          )
          SELECT (SELECT w_agree FROM agg) w_agree,
                 (SELECT w_corrected FROM agg) w_corrected,
                 (SELECT correct_genus FROM corrections) top_genus,
                 (SELECT correct_species FROM corrections) top_species,
                 (SELECT w_cnt FROM corrections) top_cnt;
        """, (result_id,))
        c = cur.fetchone()
        w_agree = float(c["w_agree"] or 0)
        w_corr  = float(c["w_corrected"] or 0)
        top_g, top_s, top_cnt = c["top_genus"], c["top_species"], float(c["top_cnt"] or 0)

        new_status, adopted = None, False
        if (w_corr >= 3.0) and (w_corr >= w_agree) and top_g:
            cur.execute("""
              UPDATE image_validation_results
              SET final_genus=%s, final_species=%s, status='corrected'
              WHERE id=%s RETURNING status;
            """, (top_g, top_s, result_id))
            new_status = cur.fetchone()["status"]; adopted = True
        elif (w_agree >= 3.0) and (w_corr < 3.0):
            cur.execute("""UPDATE image_validation_results SET status='accepted' WHERE id=%s RETURNING status;""", (result_id,))
            new_status = cur.fetchone()["status"]
        else:
            cur.execute("""SELECT status FROM image_validation_results WHERE id=%s;""", (result_id,))
            new_status = cur.fetchone()["status"]

    return jsonify({"ok": True, "feedback_id": fb["feedback_id"],
                    "result_status": new_status,
                    "weighted": {"agree": w_agree, "corrected": w_corr},
                    "adopted_correction": adopted,
                    "correction": {"genus": top_g, "species": top_s} if adopted else None})

@verify_bp.route("/leaderboard")
def leaderboard():
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT * FROM view_member_leaderboard LIMIT 100;")
        rows = cur.fetchall()
    return render_template("verify_leaderboard.html", rows=rows)

@verify_bp.route("/admin/set_reputation", methods=["POST"])
def admin_set_reputation():
    data = request.get_json(force=True, silent=True) or {}
    member_id = data.get("member_id"); score = data.get("expertise_score")
    name = (data.get("display_name") or "").strip() or None
    if not member_id or score is None:
        return jsonify({"ok": False, "error":"member_id and expertise_score required"}), 400
    with get_conn() as conn, conn.cursor() as cur:
        if name:
            cur.execute("""INSERT INTO members(member_id,display_name) VALUES (%s,%s)
                           ON CONFLICT (member_id) DO UPDATE SET display_name=EXCLUDED.display_name;""",
                           (member_id, name))
        cur.execute("""INSERT INTO member_reputation(member_id,expertise_score)
                       VALUES (%s,%s)
                       ON CONFLICT (member_id) DO UPDATE SET expertise_score=EXCLUDED.expertise_score, updated_at=NOW();""",
                       (member_id, score))
    return jsonify({"ok": True})
