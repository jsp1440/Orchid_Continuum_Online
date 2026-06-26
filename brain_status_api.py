"""
Brain Status API

Stable, machine-readable status endpoint for the Orchid Brain / Orchid Continuum.
This endpoint now reads persistent database-backed tracker state instead of the legacy
in-memory dictionary.
"""

from datetime import datetime
from flask import Blueprint, jsonify, request

brain_status_bp = Blueprint("brain_status", __name__)


@brain_status_bp.route("/api/brain/status")
def brain_status():
    """Return normalized persistent implementation state for the Orchid Brain."""
    try:
        from tracker_db_service import list_projects, summary
        projects = list_projects()
        return jsonify({
            "success": True,
            "source": "database.brain_projects",
            "timestamp": datetime.now().isoformat(),
            "governance_rule": "Query Brain status before proposing new Orchid Continuum work.",
            "summary": summary(projects),
            "projects": [project.to_dict() for project in projects],
        })
    except Exception as exc:
        return jsonify({
            "success": False,
            "source": "database.brain_projects",
            "timestamp": datetime.now().isoformat(),
            "error": str(exc),
            "message": "Brain status database endpoint failed. Check tracker model import, table creation, and DATABASE_URL.",
        }), 500


@brain_status_bp.route("/api/brain/tracker/seed", methods=["POST"])
def seed_brain_tracker():
    """Seed or refresh persistent tracker rows from legacy master_tracker.PROJECT_STATUS."""
    from tracker_db_service import seed_from_legacy
    data = request.json or {}
    result = seed_from_legacy(force=bool(data.get("force", False)))
    return jsonify({"success": True, "result": result})


@brain_status_bp.route("/api/brain/tracker/project", methods=["POST"])
def create_or_update_brain_project():
    """Create or update a persistent project tracker item."""
    from tracker_db_service import upsert_project
    try:
        project = upsert_project(request.json or {})
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    return jsonify({"success": True, "project": project.to_dict()})


@brain_status_bp.route("/api/brain/tracker/project/<project_key>", methods=["PATCH", "POST"])
def update_brain_project(project_key):
    """Update an existing persistent tracker item."""
    from tracker_db_service import update_project
    project = update_project(project_key, request.json or {})
    if not project:
        return jsonify({"success": False, "error": f"Project {project_key} not found"}), 404
    return jsonify({"success": True, "project": project.to_dict()})
