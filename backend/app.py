"""Matra — Flask API and Admin Dashboard.

Endpoints
---------
Auth:
    POST /api/auth/register
    POST /api/auth/login

Sync:
    POST /api/sync          — receive batch of offline intakes
    POST /api/assess        — single real-time risk assessment

Metrics / Admin:
    GET  /api/metrics       — aggregated anonymized statistics
    GET  /api/referrals     — list of high/intermediate referrals
    GET  /admin             — server-rendered admin dashboard page
"""

import datetime
import functools
import os
import logging

import bcrypt
import jwt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from models import MaternalIntake, User, db
from model.triage_model import evaluate_risk

# Configure audit logging
audit_logger = logging.getLogger("matra.audit")
audit_handler = logging.StreamHandler()
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Rate limiting (CRITICAL for public endpoints)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config.get("RATELIMIT_STORAGE_URL", "memory://"),
        default_limits=[]
    )
    
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["*"])}},
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def _encode_token(user_id: int, role: str) -> str:
        payload = {
            "sub": user_id,
            "role": role,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=app.config["JWT_EXPIRATION_HOURS"]),
        }
        return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

    def token_required(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
            if not token:
                return jsonify({"error": "Token missing"}), 401
            try:
                payload = jwt.decode(
                    token, app.config["SECRET_KEY"], algorithms=["HS256"]
                )
                current_user = db.session.get(User, payload["sub"])
                if current_user is None:
                    raise ValueError("User not found")
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
                return jsonify({"error": "Invalid or expired token"}), 401
            return f(current_user, *args, **kwargs)

        return decorated

    # ------------------------------------------------------------------
    # Auth routes
    # ------------------------------------------------------------------

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")
        role = data.get("role", "chw")
        clinic = data.get("clinic_name", "")

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 409

        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(
            username=username,
            password_hash=pw_hash,
            role=role,
            clinic_name=clinic,
        )
        db.session.add(user)
        db.session.commit()
        token = _encode_token(user.id, user.role)
        return jsonify({"token": token, "user_id": user.id, "role": user.role}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user is None or not bcrypt.checkpw(
            password.encode(), user.password_hash.encode()
        ):
            return jsonify({"error": "Invalid credentials"}), 401

        token = _encode_token(user.id, user.role)
        return jsonify({"token": token, "user_id": user.id, "role": user.role}), 200

    # ------------------------------------------------------------------
    # Risk assessment
    # ------------------------------------------------------------------

    @app.route("/api/assess", methods=["POST"])
    @limiter.limit(app.config.get("RATELIMIT_DEFAULT", "200/hour"))
    def assess():
        """
        Run triage model on a single intake.
        
        SECURITY NOTE: In production (ASSESS_REQUIRES_AUTH=true), this endpoint
        requires authentication to prevent abuse. For offline mobile use, provide
        an API key or JWT token in the Authorization header:
            Authorization: Bearer <token>
        
        If ASSESS_REQUIRES_AUTH is disabled, the endpoint is accessible for 
        offline-first mobile apps, but is still rate-limited.
        """
        # Check if authentication is required
        if app.config.get("ASSESS_REQUIRES_AUTH", False):
            token = None
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1]
            if not token:
                audit_logger.warning(f"Unauthorized assess attempt from {get_remote_address()}")
                return jsonify({"error": "Authentication required for assess endpoint"}), 401
            try:
                payload = jwt.decode(
                    token, app.config["SECRET_KEY"], algorithms=["HS256"]
                )
                current_user = db.session.get(User, payload["sub"])
                if current_user is None:
                    raise ValueError("User not found")
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError) as e:
                audit_logger.warning(f"Invalid token for assess from {get_remote_address()}: {str(e)}")
                return jsonify({"error": "Invalid or expired token"}), 401
        
        data = request.get_json(force=True)
        result = evaluate_risk(data)
        
        # Log assessment for audit trail (if enabled)
        if app.config.get("AUDIT_LOG_ENABLED", True):
            audit_logger.info(
                f"Assessment: age={data.get('age')}, "
                f"risk_level={result.get('risk_level')}, "
                f"remote_addr={get_remote_address()}"
            )
        
        return jsonify(result), 200

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    @app.route("/api/sync", methods=["POST"])
    @token_required
    def sync(current_user):
        """Receive a batch of offline intakes and persist them."""
        records = request.get_json(force=True)
        if not isinstance(records, list):
            records = [records]

        saved = []
        for rec in records:
            risk = evaluate_risk(rec)
            intake = MaternalIntake(
                age=rec.get("age", 0),
                parity=rec.get("parity", 0),
                systolic_bp=rec.get("systolic_bp", 0),
                diastolic_bp=rec.get("diastolic_bp", 0),
                pulse=rec.get("pulse", 0),
                bleeding=rec.get("bleeding", 0),
                fever=bool(rec.get("fever", False)),
                convulsions=bool(rec.get("convulsions", False)),
                reduced_fetal_movement=bool(rec.get("reduced_fetal_movement", False)),
                anemia=bool(rec.get("anemia", False)),
                risk_level=risk["risk_level"],
                recommended_action=risk["recommended_action"],
                ml_probability=risk.get("ml_probability"),
                is_synced=True,
                user_id=current_user.id,
            )
            db.session.add(intake)
            saved.append(intake)

        db.session.commit()
        return jsonify({"synced": len(saved)}), 201

    # ------------------------------------------------------------------
    # Metrics & referrals
    # ------------------------------------------------------------------

    @app.route("/api/metrics", methods=["GET"])
    @token_required
    def metrics(current_user):
        total = MaternalIntake.query.count()
        high = MaternalIntake.query.filter_by(risk_level="high").count()
        intermediate = MaternalIntake.query.filter_by(risk_level="intermediate").count()
        low = MaternalIntake.query.filter_by(risk_level="low").count()

        from sqlalchemy import func

        avg_age = (
            db.session.query(func.avg(MaternalIntake.age)).scalar() or 0
        )

        return jsonify(
            {
                "total_assessments": total,
                "risk_distribution": {
                    "high": high,
                    "intermediate": intermediate,
                    "low": low,
                },
                "average_maternal_age": round(float(avg_age), 1),
                "referral_rate": round(high / total * 100, 1) if total else 0,
            }
        ), 200

    @app.route("/api/referrals", methods=["GET"])
    @token_required
    def referrals(current_user):
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        query = MaternalIntake.query.filter(
            MaternalIntake.risk_level.in_(["high", "intermediate"])
        ).order_by(MaternalIntake.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify(
            {
                "referrals": [r.to_dict() for r in pagination.items],
                "total": pagination.total,
                "page": pagination.page,
                "pages": pagination.pages,
            }
        ), 200

    # ------------------------------------------------------------------
    # Admin dashboard is now served via Streamlit (see admin_dashboard.py)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "matra-api"}), 200

    return app
