"""
Database-backed tracker service for the Orchid Brain.

This service preserves the legacy static tracker as seed data, then makes all future
reads/updates persistent through the database.
"""

from datetime import datetime

from app import db
from tracker_models import BrainDecisionLog, BrainProject, BrainProjectFeature


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


IMPLEMENTED_STATUSES = {"complete", "working"}
PARTIAL_STATUSES = {"testing", "in_progress"}
DESIGNED_STATUSES = {"designed", "available"}
NEEDS_AUDIT_STATUSES = {"pending", "unknown", "quota_issue"}


def normalize_status(status):
    return str(status or "unknown").strip().lower()


def status_score(status):
    return STATUS_WEIGHTS.get(normalize_status(status), 0)


def project_phase(status):
    normalized = normalize_status(status)
    if normalized in IMPLEMENTED_STATUSES:
        return "implemented"
    if normalized in PARTIAL_STATUSES:
        return "partially_integrated"
    if normalized in DESIGNED_STATUSES:
        return "designed_not_implemented"
    if normalized in NEEDS_AUDIT_STATUSES:
        return "needs_audit"
    return "needs_audit"


def calculate_completion(status, features=None):
    features = features or []
    if features:
        return round(sum(status_score(feature.get("status")) for feature in features) / len(features))
    return status_score(status)


def seed_tracker_from_legacy(force=False):
    """Seed DB tracker rows from master_tracker.PROJECT_STATUS if rows do not exist."""
    from master_tracker import PROJECT_STATUS

    seeded = 0
    updated = 0

    for key, legacy in PROJECT_STATUS.items():
        project = BrainProject.query.filter_by(project_key=key).first()
        features = legacy.get("features") or []
        completion = calculate_completion(legacy.get("status"), features)

        if project and not force:
            continue

        if not project:
            project = BrainProject(project_key=key)
            db.session.add(project)
            seeded += 1
        else:
            BrainProjectFeature.query.filter_by(project_id=project.id).delete()
            updated += 1

        project.name = legacy.get("name", key)
        project.status = normalize_status(legacy.get("status"))
        project.phase = project_phase(project.status)
        project.owner = legacy.get("owner")
        project.priority = legacy.get("priority")
        project.url = legacy.get("url")
        project.notes = legacy.get("notes")
        project.completion_percent = completion
        project.source = "master_tracker_seed"
        project.metadata = {
            field: value
            for field, value in legacy.items()
            if field not in {"name", "status", "owner", "priority", "url", "notes", "features"}
        }

        db.session.flush()
        for index, feature in enumerate(features):
            db.session.add(BrainProjectFeature(
                project_id=project.id,
                name=feature.get("name", f"Feature {index + 1}"),
                status=normalize_status(feature.get("status")),
                cost=feature.get("cost"),
                notes=feature.get("notes"),
                sort_order=index,
                metadata={
                    field: value
                    for field, value in feature.items()
                    if field not in {"name", "status", "cost", "notes"}
                },
            ))

    if seeded or updated:
        db.session.commit()

    return {"seeded": seeded, "updated": updated, "force": force}


def ensure_tracker_seeded():
    if BrainProject.query.count() == 0:
        return seed_tracker_from_legacy(force=False)
    return {"seeded": 0, "updated": 0, "force": False}


def list_projects():
    ensure_tracker_seeded()
    return BrainProject.query.order_by(
        BrainProject.completion_percent.asc(),
        BrainProject.priority.desc().nullslast(),
        BrainProject.name.asc(),
    ).all()


def tracker_summary(projects=None):
    projects = projects if projects is not None else list_projects()
    total = len(projects)
    if not total:
        return {
            "total_projects": 0,
            "implemented": 0,
            "partially_integrated": 0,
            "designed_not_implemented": 0,
            "needs_audit": 0,
            "average_completion_percent": 0,
        }

    return {
        "total_projects": total,
        "implemented": sum(1 for p in projects if p.phase == "implemented"),
        "partially_integrated": sum(1 for p in projects if p.phase == "partially_integrated"),
        "designed_not_implemented": sum(1 for p in projects if p.phase == "designed_not_implemented"),
        "needs_audit": sum(1 for p in projects if p.phase == "needs_audit"),
        "average_completion_percent": round(sum(p.completion_percent for p in projects) / total),
    }


def update_project(project_key, status=None, notes=None, completed_by=None, priority=None, owner=None, url=None):
    ensure_tracker_seeded()
    project = BrainProject.query.filter_by(project_key=project_key).first()
    if not project:
        return None

    old_status = project.status

    if status is not None:
        project.status = normalize_status(status)
        project.phase = project_phase(project.status)
    if notes:
        project.notes = notes
    if priority is not None:
        project.priority = priority
    if owner is not None:
        project.owner = owner
    if url is not None:
        project.url = url

    features_payload = [feature.to_dict() for feature in project.features]
    project.completion_percent = calculate_completion(project.status, features_payload)

    if project.status == "complete" and old_status != "complete":
        project.completed_at = datetime.utcnow()
        project.completed_by = completed_by or "Unknown"

    db.session.add(BrainDecisionLog(
        project_key=project_key,
        decision_type="status_update",
        decision=f"Updated {project_key} from {old_status} to {project.status}",
        rationale=notes,
        decided_by=completed_by,
        previous_status=old_status,
        new_status=project.status,
    ))
    db.session.commit()
    return project


def create_or_update_project(payload):
    ensure_tracker_seeded()
    project_key = payload.get("project_key") or payload.get("key")
    if not project_key:
        raise ValueError("project_key is required")

    project = BrainProject.query.filter_by(project_key=project_key).first()
    created = False
    if not project:
        project = BrainProject(project_key=project_key)
        db.session.add(project)
        created = True

    project.name = payload.get("name", project.name or project_key)
    project.status = normalize_status(payload.get("status", project.status))
    project.phase = project_phase(project.status)
    project.owner = payload.get("owner", project.owner)
    project.priority = payload.get("priority", project.priority)
    project.url = payload.get("url", project.url)
    project.notes = payload.get("notes", project.notes)
    project.source = payload.get("source", project.source or "api")
    project.metadata = payload.get("metadata", project.metadata or {})

    if "features" in payload:
        db.session.flush()
        BrainProjectFeature.query.filter_by(project_id=project.id).delete()
        for index, feature in enumerate(payload.get("features") or []):
            db.session.add(BrainProjectFeature(
                project_id=project.id,
                name=feature.get("name", f"Feature {index + 1}"),
                status=normalize_status(feature.get("status")),
                cost=feature.get("cost"),
                notes=feature.get("notes"),
                sort_order=index,
                metadata=feature.get("metadata") or {},
            ))

    db.session.flush()
    features_payload = [feature.to_dict() for feature in project.features]
    project.completion_percent = calculate_completion(project.status, features_payload)

    db.session.add(BrainDecisionLog(
        project_key=project_key,
        decision_type="project_created" if created else "project_updated",
        decision=("Created" if created else "Updated") + f" tracker project {project_key}",
        rationale=project.notes,
        decided_by=payload.get("completed_by") or payload.get("updated_by"),
        new_status=project.status,
    ))
    db.session.commit()
    return project
