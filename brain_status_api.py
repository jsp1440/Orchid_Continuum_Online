"""
Brain Status API

Exposes a stable, machine-readable status endpoint for the Orchid Brain / Orchid Continuum
implementation tracker. This is intended to be the first endpoint consulted before proposing
new work, so existing systems can be continued instead of redesigned.
"""

from datetime import datetime
from flask import Blueprint, jsonify

brain_status_bp = Blueprint("brain_status", __name__)


STATUS_WEIGHTS = {
    "complete": 100,
    "working": 100,
    "testing": 75,
    "in_progress": 50,
    "designed": 35,
    "available": 25,
    "pending": 0,
    "unknown": 0,
    "quota_issue": 0,
}


def _feature_score(feature):
    status = str(feature.get("status", "unknown")).lower()
    return STATUS_WEIGHTS.get(status, 0)


def _project_completion(project):
    features = project.get("features") or []
    if features:
        scores = [_feature_score(feature) for feature in features]
        return round(sum(scores) / len(scores)) if scores else 0

    status = str(project.get("status", "unknown")).lower()
    return STATUS_WEIGHTS.get(status, 0)


def _project_phase(project):
    status = str(project.get("status", "unknown")).lower()
    if status in ("complete", "working"):
        return "implemented"
    if status in ("testing", "in_progress"):
        return "partially_integrated"
    if status in ("designed", "available"):
        return "designed_not_implemented"
    if status in ("pending", "unknown", "quota_issue"):
        return "needs_audit"
    return "needs_audit"


def _load_project_status():
    """Load current tracker state without requiring a database migration."""
    try:
        from master_tracker import PROJECT_STATUS
        return PROJECT_STATUS
    except Exception as exc:  # pragma: no cover - defensive endpoint behavior
        return {
            "tracker_unavailable": {
                "name": "Project Tracker unavailable",
                "status": "unknown",
                "owner": "System",
                "notes": f"Could not import master_tracker.PROJECT_STATUS: {exc}",
            }
        }


@brain_status_bp.route("/api/brain/status")
def brain_status():
    """
    Return normalized implementation state for the Orchid Brain.

    This endpoint intentionally summarizes the legacy Master Project Tracker into
    categories that are useful for development triage: implemented, partial,
    designed-but-not-implemented, needs audit, blockers, and next action.
    """
    projects = _load_project_status()
    normalized = []

    for key, project in projects.items():
        completion = _project_completion(project)
        features = project.get("features") or []
        unfinished_features = [
            feature for feature in features
            if str(feature.get("status", "unknown")).lower() not in ("complete", "working")
        ]

        normalized.append({
            "key": key,
            "name": project.get("name", key),
            "status": project.get("status", "unknown"),
            "phase": _project_phase(project),
            "completion_percent": completion,
            "priority": project.get("priority"),
            "owner": project.get("owner"),
            "url": project.get("url"),
            "notes": project.get("notes"),
            "unfinished_features": unfinished_features,
            "next_action": (
                unfinished_features[0].get("name")
                if unfinished_features else
                "Verify deployment and connect to active Brain/Research Station surfaces"
            ),
        })

    normalized.sort(key=lambda item: (item["completion_percent"], item.get("priority") != "CRITICAL"))

    summary = {
        "total_projects": len(normalized),
        "implemented": sum(1 for item in normalized if item["phase"] == "implemented"),
        "partially_integrated": sum(1 for item in normalized if item["phase"] == "partially_integrated"),
        "designed_not_implemented": sum(1 for item in normalized if item["phase"] == "designed_not_implemented"),
        "needs_audit": sum(1 for item in normalized if item["phase"] == "needs_audit"),
        "average_completion_percent": round(
            sum(item["completion_percent"] for item in normalized) / len(normalized)
        ) if normalized else 0,
    }

    return jsonify({
        "success": True,
        "source": "master_tracker.PROJECT_STATUS",
        "timestamp": datetime.now().isoformat(),
        "governance_rule": "Query Brain status before proposing new Orchid Continuum work.",
        "summary": summary,
        "projects": normalized,
    })
