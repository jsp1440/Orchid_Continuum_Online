"""Safe DB-backed tracker service used by /api/brain/status."""

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


def normalize_status(status):
    return str(status or "unknown").strip().lower()


def status_score(status):
    return STATUS_WEIGHTS.get(normalize_status(status), 0)


def project_phase(status):
    status = normalize_status(status)
    if status in {"complete", "working"}:
        return "implemented"
    if status in {"testing", "in_progress"}:
        return "partially_integrated"
    if status in {"designed", "available"}:
        return "designed_not_implemented"
    return "needs_audit"


def calculate_completion(status, features=None):
    features = features or []
    if features:
        return round(sum(status_score(f.get("status")) for f in features) / len(features))
    return status_score(status)


def seed_from_legacy(force=False):
    from master_tracker import PROJECT_STATUS
    seeded = 0
    updated = 0

    for key, legacy in PROJECT_STATUS.items():
        project = BrainProject.query.filter_by(project_key=key).first()
        if project and not force:
            continue

        if not project:
            project = BrainProject(project_key=key)
            db.session.add(project)
            seeded += 1
        else:
            BrainProjectFeature.query.filter_by(project_id=project.id).delete()
            updated += 1

        features = legacy.get("features") or []
        project.name = legacy.get("name", key)
        project.status = normalize_status(legacy.get("status"))
        project.phase = project_phase(project.status)
        project.owner = legacy.get("owner")
        project.priority = legacy.get("priority")
        project.url = legacy.get("url")
        project.notes = legacy.get("notes")
        project.completion_percent = calculate_completion(project.status, features)
        project.source = "master_tracker_seed"
        project.extra_metadata = {
            k: v for k, v in legacy.items()
            if k not in {"name", "status", "owner", "priority", "url", "notes", "features"}
        }

        db.session.flush()
        for i, feature in enumerate(features):
            db.session.add(BrainProjectFeature(
                project_id=project.id,
                name=feature.get("name", f"Feature {i + 1}"),
                status=normalize_status(feature.get("status")),
                cost=feature.get("cost"),
                notes=feature.get("notes"),
                sort_order=i,
                extra_metadata={
                    k: v for k, v in feature.items()
                    if k not in {"name", "status", "cost", "notes"}
                },
            ))

    if seeded or updated:
        db.session.commit()
    return {"seeded": seeded, "updated": updated, "force": force}


def ensure_seeded():
    if BrainProject.query.count() == 0:
        return seed_from_legacy(False)
    return {"seeded": 0, "updated": 0, "force": False}


def list_projects():
    ensure_seeded()
    return BrainProject.query.order_by(
        BrainProject.completion_percent.asc(),
        BrainProject.name.asc(),
    ).all()


def summary(projects=None):
    projects = projects if projects is not None else list_projects()
    total = len(projects)
    if total == 0:
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


def upsert_project(payload):
    ensure_seeded()
    key = payload.get("project_key") or payload.get("key")
    if not key:
        raise ValueError("project_key is required")

    project = BrainProject.query.filter_by(project_key=key).first()
    created = project is None
    if created:
        project = BrainProject(project_key=key)
        db.session.add(project)

    project.name = payload.get("name", project.name or key)
    project.status = normalize_status(payload.get("status", project.status))
    project.phase = project_phase(project.status)
    project.owner = payload.get("owner", project.owner)
    project.priority = payload.get("priority", project.priority)
    project.url = payload.get("url", project.url)
    project.notes = payload.get("notes", project.notes)
    project.source = payload.get("source", project.source or "api")
    project.extra_metadata = payload.get("metadata", project.extra_metadata or {})

    db.session.flush()
    if "features" in payload:
        BrainProjectFeature.query.filter_by(project_id=project.id).delete()
        for i, feature in enumerate(payload.get("features") or []):
            db.session.add(BrainProjectFeature(
                project_id=project.id,
                name=feature.get("name", f"Feature {i + 1}"),
                status=normalize_status(feature.get("status")),
                cost=feature.get("cost"),
                notes=feature.get("notes"),
                sort_order=i,
                extra_metadata=feature.get("metadata") or {},
            ))
        db.session.flush()

    project.completion_percent = calculate_completion(
        project.status,
        [f.to_dict() for f in project.features],
    )

    db.session.add(BrainDecisionLog(
        project_key=key,
        decision_type="project_created" if created else "project_updated",
        decision=("Created" if created else "Updated") + f" tracker project {key}",
        rationale=project.notes,
        decided_by=payload.get("updated_by") or payload.get("completed_by"),
        new_status=project.status,
    ))
    db.session.commit()
    return project


def update_project(key, payload):
    ensure_seeded()
    project = BrainProject.query.filter_by(project_key=key).first()
    if not project:
        return None
    old_status = project.status
    payload = dict(payload or {})
    payload["project_key"] = key
    project = upsert_project(payload)
    if project.status == "complete" and old_status != "complete":
        project.completed_at = datetime.utcnow()
        project.completed_by = payload.get("completed_by") or "Unknown"
        db.session.commit()
    return project
