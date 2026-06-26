"""
Database-backed project tracker models for the Orchid Brain.

These tables turn the legacy in-memory Master Project Tracker into persistent project state
that survives deploys/restarts and can be queried by /api/brain/status.
"""

from datetime import datetime
from app import db


class BrainProject(db.Model):
    __tablename__ = "brain_projects"

    id = db.Column(db.Integer, primary_key=True)
    project_key = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="unknown", index=True)
    phase = db.Column(db.String(80), nullable=True, index=True)
    owner = db.Column(db.String(160), nullable=True)
    priority = db.Column(db.String(40), nullable=True, index=True)
    url = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    completion_percent = db.Column(db.Integer, nullable=False, default=0)
    source = db.Column(db.String(120), nullable=False, default="master_tracker_seed")
    extra_metadata = db.Column("metadata", db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    completed_by = db.Column(db.String(160), nullable=True)

    features = db.relationship(
        "BrainProjectFeature",
        backref="project",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="BrainProjectFeature.sort_order",
    )

    def to_dict(self, include_features=True):
        payload = {
            "key": self.project_key,
            "name": self.name,
            "status": self.status,
            "phase": self.phase,
            "owner": self.owner,
            "priority": self.priority,
            "url": self.url,
            "notes": self.notes,
            "completion_percent": self.completion_percent,
            "source": self.source,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completed_by": self.completed_by,
        }
        if include_features:
            payload["features"] = [feature.to_dict() for feature in self.features]
            payload["unfinished_features"] = [
                feature.to_dict() for feature in self.features
                if feature.status not in ("complete", "working")
            ]
            payload["next_action"] = (
                payload["unfinished_features"][0]["name"]
                if payload["unfinished_features"]
                else "Verify deployment and connect to active Brain/Research Station surfaces"
            )
        return payload


class BrainProjectFeature(db.Model):
    __tablename__ = "brain_project_features"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("brain_projects.id"), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(40), nullable=False, default="unknown", index=True)
    cost = db.Column(db.String(80), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    extra_metadata = db.Column("metadata", db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "cost": self.cost,
            "notes": self.notes,
            "sort_order": self.sort_order,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BrainDecisionLog(db.Model):
    __tablename__ = "brain_decision_log"

    id = db.Column(db.Integer, primary_key=True)
    project_key = db.Column(db.String(120), nullable=True, index=True)
    decision_type = db.Column(db.String(80), nullable=False, default="status_update")
    decision = db.Column(db.Text, nullable=False)
    rationale = db.Column(db.Text, nullable=True)
    decided_by = db.Column(db.String(160), nullable=True)
    previous_status = db.Column(db.String(40), nullable=True)
    new_status = db.Column(db.String(40), nullable=True)
    extra_metadata = db.Column("metadata", db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "project_key": self.project_key,
            "decision_type": self.decision_type,
            "decision": self.decision,
            "rationale": self.rationale,
            "decided_by": self.decided_by,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
