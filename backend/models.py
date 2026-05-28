"""Database models for Matra maternal health decision support system.

All patient data is stored anonymized — no names, national IDs, or precise
geo-coordinates are captured.  Only the minimum fields required for clinical
triage and aggregate reporting are persisted.
"""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Application user (CHW, hospital staff, or district manager)."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(
        db.String(20),
        nullable=False,
        default="chw",  # chw | hospital | manager
    )
    clinic_name = db.Column(db.String(120), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    intakes = db.relationship("MaternalIntake", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class MaternalIntake(db.Model):
    """Single maternal triage assessment record (anonymized)."""

    __tablename__ = "maternal_intakes"

    id = db.Column(db.Integer, primary_key=True)

    # Demographics
    age = db.Column(db.Integer, nullable=False)
    parity = db.Column(db.Integer, nullable=False, default=0)

    # Vitals
    systolic_bp = db.Column(db.Integer, nullable=False)
    diastolic_bp = db.Column(db.Integer, nullable=False)
    pulse = db.Column(db.Integer, nullable=False)

    # Danger signs  (0 = absent, 1 = present; bleeding uses 0/1/2 for none/light/severe)
    bleeding = db.Column(db.Integer, nullable=False, default=0)
    fever = db.Column(db.Boolean, nullable=False, default=False)
    convulsions = db.Column(db.Boolean, nullable=False, default=False)
    reduced_fetal_movement = db.Column(db.Boolean, nullable=False, default=False)
    anemia = db.Column(db.Boolean, nullable=False, default=False)

    # Triage outcome
    risk_level = db.Column(db.String(15), nullable=False)  # high / intermediate / low
    recommended_action = db.Column(db.String(50), nullable=True)
    ml_probability = db.Column(db.Float, nullable=True)

    # Sync metadata
    is_synced = db.Column(db.Boolean, nullable=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self):
        """Serialize to JSON-safe dictionary."""
        return {
            "id": self.id,
            "age": self.age,
            "parity": self.parity,
            "systolic_bp": self.systolic_bp,
            "diastolic_bp": self.diastolic_bp,
            "pulse": self.pulse,
            "bleeding": self.bleeding,
            "fever": self.fever,
            "convulsions": self.convulsions,
            "reduced_fetal_movement": self.reduced_fetal_movement,
            "anemia": self.anemia,
            "risk_level": self.risk_level,
            "recommended_action": self.recommended_action,
            "ml_probability": self.ml_probability,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
