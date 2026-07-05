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

import base64
import datetime
import functools
import io
import json
import os
import logging
import re
import tempfile
import uuid

import bcrypt
import jwt
import requests
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from config import Config
from models import MaternalIntake, User, VoiceSession, db
from model.triage_model import evaluate_risk

import sys


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

    # Fail fast at runtime (not import-time) for production secrets
    try:
        from config import require_secret_key
        require_secret_key()
    except Exception:
        # If require_secret_key isn't appropriate for current config, let it surface naturally
        pass


    # Rate limiting (CRITICAL for public endpoints)
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config.get("RATELIMIT_STORAGE_URL", "memory://"),
        default_limits=[],
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
    # Auth helpers (defined early because decorators use them)
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
    # Voice agent helpers (optional)
    # ------------------------------------------------------------------

    voice_enabled = str(app.config.get("VOICE_ENABLED", "false")).lower() == "true"

    if voice_enabled:
        if WhisperModel is None:
            raise RuntimeError(
                "Voice is enabled but 'faster-whisper' is not installed. "
                "Install it or set VOICE_ENABLED=false."
            )

        app.voice_model = WhisperModel(
            app.config["VOICE_STT_MODEL"],
            device=app.config.get("VOICE_STT_DEVICE", "cpu"),
        )
    else:
        app.voice_model = None

    def cleanup_voice_sessions():
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=app.config.get("VOICE_SESSION_TIMEOUT_SECONDS", 3600)
        )
        VoiceSession.query.filter(VoiceSession.last_seen < cutoff).delete(synchronize_session=False)
        db.session.commit()

    def generate_session_id():
        for _ in range(5):
            session_id = str(uuid.uuid4())
            if VoiceSession.query.get(session_id) is None:
                return session_id
        raise RuntimeError("Unable to generate a unique voice session ID")

    def get_voice_session(session_id, current_user):
        cleanup_voice_sessions()
        session = VoiceSession.query.get(session_id)
        if session is None:
            abort(404, description="Voice session not found")
        if session.user_id != current_user.id:
            abort(403, description="Not authorized to access this voice session")
        session.last_seen = datetime.datetime.now(datetime.timezone.utc)
        db.session.commit()
        return session

    def redact_pii(text):
        if not isinstance(text, str):
            return text
        patterns = [
            r"\b(name|patient name|full name)\b[: ]*[^.,;\n]+",
            r"\b(national id|national ID|ssn|social security number|passport number)\b[: ]*[^.,;\n]+",
            r"\b(phone|telephone|mobile)\b[: ]*\+?[0-9\-\s()]+",
            r"\b(email)\b[: ]*[^\s@]+@[^\s@]+"
        ]
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, "[REDACTED]", cleaned, flags=re.I)
        return cleaned

    def extract_json_payload(text):
        json_text = None
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
        if json_match:
            json_text = json_match.group(1)
        else:
            brace_match = re.search(r"(\{\s*[\s\S]*\})", text)
            if brace_match:
                json_text = brace_match.group(1)

        if not json_text:
            return None

        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return None

    def transcribe_audio(audio_file_path):
        result = app.voice_model.transcribe(audio_file_path)
        return " ".join([segment.text.strip() for segment in result])

    def call_ollama(messages):
        payload = {
            "model": app.config.get("OLLAMA_MODEL", "llama3"),
            "messages": messages,
            "stream": False
        }
        response = requests.post(
            f"{app.config.get('OLLAMA_URL')}/api/chat",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def generate_voice_audio(text):
        api_key = app.config.get("ELEVENLABS_API_KEY")
        voice_id = app.config.get("ELEVENLABS_VOICE_ID")
        if not api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not configured")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75
            }
        }
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")

    def build_voice_prompt(transcript, history):
        system_prompt = (
            "You are an empathetic maternal health assistant. "
            "Use the user transcription to ask one focused triage question at a time. "
            "Extract the following fields when provided: age, parity, systolic_bp, diastolic_bp, pulse, fever, bleeding, convulsions, reduced_fetal_movement, anemia. "
            "You may ask follow-up questions to complete missing triage values. "
            "At the end of your response, if any triage fields were collected or updated, include a JSON object in triple backticks with keys:"
            " age, parity, systolic_bp, diastolic_bp, pulse, bleeding, fever, convulsions, reduced_fetal_movement, anemia. "
            "Do not diagnose. Keep responses short, empathetic, and clinically safe."
        )
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": transcript})
        return messages

    def extract_form_fields_from_response(response_text):
        extracted = extract_json_payload(response_text)
        if not isinstance(extracted, dict):
            return None
        field_map = {
            "age": int,
            "parity": int,
            "systolic_bp": int,
            "diastolic_bp": int,
            "pulse": int,
            "bleeding": int,
            "fever": bool,
            "convulsions": bool,
            "reduced_fetal_movement": bool,
            "anemia": bool
        }
        result = {}
        for key, cast in field_map.items():
            if key in extracted:
                try:
                    value = extracted[key]
                    if cast is bool:
                        result[key] = bool(value)
                    else:
                        result[key] = cast(value)
                except (ValueError, TypeError):
                    continue
        return result

    def maybe_add_risk_fields(extracted):
        if not extracted:
            return extracted
        try:
            risk = evaluate_risk(extracted)
            extracted["risk_level"] = risk.get("risk_level")
            extracted["recommended_action"] = risk.get("recommended_action")
        except Exception as exc:
            audit_logger.error("Risk evaluation failed: %s", str(exc))
        return extracted

    @app.route("/api/voice/session", methods=["POST"])
    @token_required
    def create_voice_session(current_user):
        if app.voice_model is None:
            return jsonify({"error": "Voice features disabled"}), 503

        session_id = generate_session_id()
        session = VoiceSession(
            session_id=session_id,
            user_id=current_user.id,
            messages=json.dumps([]),
            created_at=datetime.datetime.now(datetime.timezone.utc),
            last_seen=datetime.datetime.now(datetime.timezone.utc),
        )
        db.session.add(session)
        db.session.commit()
        return jsonify({"session_id": session_id}), 201

    @app.route("/api/voice/session/<session_id>/audio", methods=["POST"])
    @token_required
    def voice_session_audio(current_user, session_id):
        if app.voice_model is None:
            return jsonify({"error": "Voice features disabled"}), 503

        if "audio" not in request.files:
            return jsonify({"error": "Audio file is required"}), 400

        session = get_voice_session(session_id, current_user)
        audio_file = request.files["audio"]

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
            audio_file.save(tmp_file)
            temp_path = tmp_file.name

        try:
            transcript = transcribe_audio(temp_path)
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

        transcript = redact_pii(transcript)
        session.append_message("user", transcript)
        db.session.commit()

        messages = build_voice_prompt(transcript, session.get_messages())

        try:
            assistant_text = call_ollama(messages)
        except Exception as exc:
            return jsonify({"error": "Failed to call Ollama", "details": str(exc)}), 502

        session.append_message("assistant", assistant_text)
        db.session.commit()

        extracted = extract_form_fields_from_response(assistant_text)
        maybe_add_risk_fields(extracted)

        try:
            audio_base64 = generate_voice_audio(assistant_text)
        except Exception as exc:
            return jsonify({
                "transcript": transcript,
                "assistant_text": assistant_text,
                "extracted_data": extracted,
                "warning": "TTS generation failed",
                "audio_base64": None,
                "error": str(exc)
            }), 502

        return jsonify({
            "session_id": session_id,
            "transcript": transcript,
            "assistant_text": assistant_text,
            "audio_base64": audio_base64,
            "extracted_data": extracted
        }), 200


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
