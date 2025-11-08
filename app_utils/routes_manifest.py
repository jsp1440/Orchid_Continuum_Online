from flask import Blueprint, jsonify, render_template
from .manifest import get_manifest

bp_manifest = Blueprint("manifest", __name__)

@bp_manifest.get("/api/manifest")
def api_manifest():
    """
    JSON manifest Neon One can read. Includes pages, widgets_flat, errors.
    """
    return jsonify(get_manifest())

@bp_manifest.get("/manifest")
def manifest_dashboard():
    """
    Lightweight human dashboard. Safe to expose publicly if you wish,
    or you can protect later. No secrets displayed.
    """
    data = get_manifest()
    # If templates not available in this project, return JSON-as-HTML fallback
    try:
        return render_template("manifest_dashboard.html", data=data)
    except Exception:
        html = ["<h1>Widget Deployment Manifest</h1>"]
        if data.get("errors"):
            html.append("<p><strong>Errors:</strong> " + ", ".join(data["errors"]) + "</p>")
        for page in data.get("pages", []):
            html.append(f"<h2>{page.get('page','(no page)')}</h2><ul>")
            for w in page.get("widgets", []):
                badge = "🟢" if w.get("status") in ("active","restricted") else "⚪️"
                html.append(f"<li>{badge} <strong>{w.get('name')}</strong> "
                            f"({w.get('type','?')}, {w.get('delivery','cdn')}) — {w.get('notes','')}</li>")
            html.append("</ul>")
        return ("".join(html), 200, {"Content-Type": "text/html; charset=utf-8"})
