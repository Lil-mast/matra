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

import bcrypt
import jwt
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

from config import Config
from models import MaternalIntake, User, db
from model.triage_model import evaluate_risk

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
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
    def assess():
        """Run triage model on a single intake (no auth required — offline use)."""
        data = request.get_json(force=True)
        result = evaluate_risk(data)
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
    # Admin dashboard (server-rendered)
    # ------------------------------------------------------------------

    @app.route("/admin")
    def admin_dashboard():
        total = MaternalIntake.query.count()
        high = MaternalIntake.query.filter_by(risk_level="high").count()
        intermediate = MaternalIntake.query.filter_by(risk_level="intermediate").count()
        low = MaternalIntake.query.filter_by(risk_level="low").count()
        recent = (
            MaternalIntake.query.order_by(MaternalIntake.created_at.desc())
            .limit(15)
            .all()
        )
        return render_template_string(
            ADMIN_TEMPLATE,
            total=total,
            high=high,
            intermediate=intermediate,
            low=low,
            recent=recent,
        )

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "matra-api"}), 200

    return app


# ---------------------------------------------------------------------------
# Admin HTML template (embedded for single-file simplicity)
# ---------------------------------------------------------------------------

ADMIN_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Matra Admin Dashboard</title>
<style>
  :root{--bg:#0f1117;--surface:#1a1d27;--card:#22263a;--accent:#4fc3f7;
  --high:#ef5350;--mid:#ffb74d;--low:#66bb6a;--fg:#e4e6eb;--fg2:#9ea3b0;
  --radius:12px;--font:'Segoe UI',system-ui,sans-serif}
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:var(--bg);color:var(--fg);font-family:var(--font);
       padding:2rem;min-height:100vh}
  h1{font-size:1.8rem;margin-bottom:.4rem}
  .sub{color:var(--fg2);margin-bottom:2rem}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;margin-bottom:2rem}
  .card{background:var(--card);border-radius:var(--radius);padding:1.4rem;
        text-align:center;border:1px solid rgba(255,255,255,.06)}
  .card .num{font-size:2.2rem;font-weight:700}
  .card .label{color:var(--fg2);font-size:.85rem;margin-top:.3rem}
  .high .num{color:var(--high)} .mid .num{color:var(--mid)} .low .num{color:var(--low)}
  table{width:100%;border-collapse:collapse;background:var(--surface);
        border-radius:var(--radius);overflow:hidden}
  th,td{padding:.75rem 1rem;text-align:left;border-bottom:1px solid rgba(255,255,255,.06)}
  th{background:var(--card);color:var(--accent);font-size:.8rem;text-transform:uppercase;letter-spacing:.5px}
  .badge{display:inline-block;padding:.2rem .65rem;border-radius:20px;font-size:.75rem;font-weight:600;color:#fff}
  .badge.high{background:var(--high)} .badge.intermediate{background:var(--mid);color:#333}
  .badge.low{background:var(--low);color:#333}
</style>
</head>
<body>
<h1>🩺 Matra Admin Dashboard</h1>
<p class="sub">Aggregated anonymized maternal triage metrics</p>

<div class="grid">
  <div class="card"><div class="num">{{ total }}</div><div class="label">Total Assessments</div></div>
  <div class="card high"><div class="num">{{ high }}</div><div class="label">High Risk</div></div>
  <div class="card mid"><div class="num">{{ intermediate }}</div><div class="label">Intermediate</div></div>
  <div class="card low"><div class="num">{{ low }}</div><div class="label">Low Risk</div></div>
</div>

<h2 style="margin-bottom:1rem;font-size:1.2rem">Recent Assessments</h2>
<table>
<thead><tr>
  <th>ID</th><th>Age</th><th>BP</th><th>Pulse</th><th>Bleeding</th>
  <th>Risk</th><th>Action</th><th>Date</th>
</tr></thead>
<tbody>
{% for r in recent %}
<tr>
  <td>{{ r.id }}</td>
  <td>{{ r.age }}</td>
  <td>{{ r.systolic_bp }}/{{ r.diastolic_bp }}</td>
  <td>{{ r.pulse }}</td>
  <td>{{ r.bleeding }}</td>
  <td><span class="badge {{ r.risk_level }}">{{ r.risk_level }}</span></td>
  <td>{{ r.recommended_action }}</td>
  <td>{{ r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else '-' }}</td>
</tr>
{% endfor %}
{% if not recent %}
<tr><td colspan="8" style="text-align:center;color:var(--fg2)">No assessments yet</td></tr>
{% endif %}
</tbody>
</table>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
