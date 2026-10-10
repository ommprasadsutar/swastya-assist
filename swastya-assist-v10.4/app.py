import base64
import hashlib
import io
import json
import logging
import os
import re
import secrets
import time
import uuid
import tempfile
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from PIL import Image, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 20_000_000
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.utils import secure_filename

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover - dependency is part of requirements.txt
    Fernet = None
    InvalidToken = Exception

APP_VERSION = "10.4.3"
BASE = Path(__file__).resolve().parent
TEST_MODE = os.getenv("SWASTYA_TEST_MODE", "0") == "1"
load_dotenv(BASE / ".env", override=not TEST_MODE)
RUNNING_ON_VERCEL = bool(os.getenv("VERCEL"))
LOCAL_SECRET_FILE = BASE / "instance" / "local_secret.key"
LOGIN_CSRF_SECRET_FILE = BASE / "instance" / "login_csrf_secret.key"

def _persisted_local_secret(path: Path):
    """Return a stable local secret, creating it once when needed."""
    try:
        path.parent.mkdir(mode=0o700, exist_ok=True)
        if path.exists():
            saved = path.read_text(encoding="utf-8").strip()
            if saved:
                return saved
        saved = secrets.token_urlsafe(48)
        path.write_text(saved, encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return saved
    except OSError:
        return secrets.token_urlsafe(48)

def get_secret_key():
    configured = os.getenv("FLASK_SECRET_KEY", "").strip()
    if configured:
        return configured
    if RUNNING_ON_VERCEL:
        # Production deployments must supply FLASK_SECRET_KEY explicitly.
        return secrets.token_urlsafe(48)
    # Persist a generated local secret so restarting the local Flask server
    # does not invalidate signed login tokens or existing local sessions.
    return _persisted_local_secret(LOCAL_SECRET_FILE)
UPLOADS = BASE / "uploads"
if not RUNNING_ON_VERCEL:
    UPLOADS.mkdir(mode=0o700, exist_ok=True)

RAW_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if RAW_DATABASE_URL.startswith("postgres://"):
    RAW_DATABASE_URL = "postgresql+psycopg://" + RAW_DATABASE_URL[len("postgres://") :]
elif RAW_DATABASE_URL.startswith("postgresql://"):
    RAW_DATABASE_URL = "postgresql+psycopg://" + RAW_DATABASE_URL[len("postgresql://") :]
DATABASE_URL = RAW_DATABASE_URL or (f"sqlite:////tmp/swastya-triage.db" if RUNNING_ON_VERCEL else f"sqlite:///{BASE / 'triage.db'}")

MAX_UPLOAD_MB = max(1, min(int(os.getenv("MAX_UPLOAD_MB", "4")), 4))
MAX_CONTENT_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MIN_PASSWORD_LENGTH = 12
MAX_REPORT_BYTES = min(3 * 1024 * 1024, MAX_CONTENT_BYTES - 64 * 1024)
MAX_AUDIO_BYTES = min(2 * 1024 * 1024, MAX_CONTENT_BYTES - 64 * 1024)
RETENTION_DAYS = max(1, int(os.getenv("RETENTION_DAYS", "30")))
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_TRANSCRIBE_MODEL = os.getenv("GEMINI_TRANSCRIBE_MODEL", "gemini-3.8-flash")
GEMINI_FALLBACK_MODELS = []
GEMINI_RETRY_ATTEMPTS = 1
GEMINI_VOICE_MODEL = os.getenv("GEMINI_VOICE_MODEL", GEMINI_MODEL)
GEMINI_RETRY_BASE_SECONDS = 0.0
# Generate Content REST is the stable, documented path for Gemini 3.8 Flash.
# This transport is intentionally fixed to the documented v1beta GenerateContent REST endpoint.
GEMINI_GENERATE_API_VERSION = "v1beta"
GEMINI_GENERATE_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
LOCAL_RESET_ADMIN_PASSWORD = os.getenv("LOCAL_RESET_ADMIN_PASSWORD", "0") == "1"
HEALTH_INPUT_GATE = os.getenv("HEALTH_INPUT_GATE", "1") == "1"

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    SECRET_KEY=get_secret_key(),
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=MAX_CONTENT_BYTES,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=(os.getenv("COOKIE_SECURE", "1" if RUNNING_ON_VERCEL else "0") == "1"),
    SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
    REMEMBER_COOKIE_HTTPONLY=True,
)

db = SQLAlchemy(app)
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["300 per minute"],
    storage_uri=(os.getenv("RATELIMIT_STORAGE_URI", "").strip() or os.getenv("REDIS_URL", "").strip() or "memory://"),
)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("swastya_assist")

ALLOWED_REPORT_TYPES = {"image/png", "image/jpeg", "application/pdf"}
ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/mp4",
    "audio/ogg",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
}
ALLOWED_LANGUAGES = {
    "English", "Hindi", "Bengali", "Marathi", "Tamil", "Telugu", "Odia",
    "Kannada", "Malayalam", "Punjabi", "Gujarati", "Assamese", "Urdu",
}
ALLOWED_SCENARIOS = {
    "Outpatient queue triage",
    "Occupational health screening",
    "Campus fever triage",
    "Maternal follow-up",
    "Chronic disease check-in",
    "Public health camp screening",
    "Referral note preparation",
}
ALLOWED_REVIEW_STATUSES = {"Needs review", "Reviewed", "Escalated", "Needs more information"}
DISCLAIMER = (
    "Educational prototype and triage-support only. Non-diagnostic. "
    "A qualified health professional must review all outputs. Use synthetic/public data only."
)


class EncryptedText(db.TypeDecorator):
    """Optional Fernet encryption for sensitive database text fields."""

    impl = db.Text
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fernet = None
        key = os.getenv("DATA_ENCRYPTION_KEY", "").strip()
        if key:
            if Fernet is None:
                raise RuntimeError("cryptography is required when DATA_ENCRYPTION_KEY is configured")
            self._fernet = Fernet(key.encode())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        value = str(value)
        return self._fernet.encrypt(value.encode()).decode() if self._fernet else value

    def process_result_value(self, value, dialect):
        if value is None or not self._fernet:
            return value
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except (InvalidToken, ValueError, TypeError):
            # Backward-compatible read path for a database created before encryption was enabled.
            return value


class EncryptedBlob(db.TypeDecorator):
    """Optional Fernet encryption for uploaded report bytes stored in DB."""

    impl = db.LargeBinary
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fernet = None
        key = os.getenv("DATA_ENCRYPTION_KEY", "").strip()
        if key:
            if Fernet is None:
                raise RuntimeError("cryptography is required when DATA_ENCRYPTION_KEY is configured")
            self._fernet = Fernet(key.encode())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return self._fernet.encrypt(value) if self._fernet else value

    def process_result_value(self, value, dialect):
        if value is None or not self._fernet:
            return value
        try:
            return self._fernet.decrypt(value)
        except (InvalidToken, ValueError, TypeError):
            # Backward-compatible read path for a database created before encryption was enabled.
            return value


class User(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="reviewer")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class RegistrationRequest(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="reviewer")
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class Case(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    patient_ref = db.Column(db.String(80), nullable=False, index=True)
    patient_name = db.Column(EncryptedText(), nullable=False, default="")
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(40), nullable=False, default="")
    address = db.Column(EncryptedText(), nullable=False, default="")
    consent = db.Column(db.Boolean, nullable=False, default=False)
    report_filename = db.Column(db.String(255), nullable=False, default="")
    report_mime = db.Column(db.String(120), nullable=False, default="")
    report_data = db.Column(EncryptedBlob(), nullable=True)
    # Kept for backward compatibility with earlier local builds.
    report_path = db.Column(db.String(500), nullable=False, default="")
    language = db.Column(db.String(40), nullable=False, index=True)
    symptoms = db.Column(EncryptedText(), nullable=False, default="")
    report_text = db.Column(EncryptedText(), nullable=False, default="")
    ai_note = db.Column(db.JSON, nullable=False, default=dict)
    risk = db.Column(db.String(40), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, default="Needs review", index=True)
    reviewer_note = db.Column(EncryptedText(), nullable=False, default="")
    source = db.Column(db.String(80), nullable=False, default="Patient intake")
    scenario = db.Column(db.String(80), nullable=False, default="Outpatient queue triage")
    reviewed_by = db.Column(db.String(32), nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)


class AuditEvent(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = db.Column(db.String(32), nullable=True, index=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    case_id = db.Column(db.String(32), nullable=True, index=True)
    metadata_json = db.Column(db.JSON, nullable=False, default=dict)


class AIRequestClaim(db.Model):
    """Durable idempotency/once-only claim for each user AI attempt.

    The frontend uses one request id for a fresh submission and reuses that id
    for its single explicit retry. The unique (request_id, attempt_no) constraint
    prevents duplicate browser events or concurrent requests from creating a
    second provider call for the same attempt, including across Vercel instances.
    """
    id = db.Column(db.String(32), primary_key=True)
    request_id = db.Column(db.String(64), nullable=False, index=True)
    attempt_no = db.Column(db.Integer, nullable=False)
    feature = db.Column(db.String(40), nullable=False, index=True)
    user_id = db.Column(db.String(32), nullable=False, index=True)
    payload_hash = db.Column(db.String(64), nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="in_progress", index=True)
    error = db.Column(db.String(500), nullable=False, default="")
    retry_token = db.Column(db.String(96), nullable=False, default="", index=True)
    retry_used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    __table_args__ = (db.UniqueConstraint("request_id", "attempt_no", name="uq_ai_request_attempt"),)


def utcnow():
    return datetime.now(timezone.utc)


def current_user():
    uid = session.get("user_id")
    user = db.session.get(User, uid) if uid else None
    if user is not None and not user.active:
        session.clear()
        return None
    return user


def require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            if request.path.startswith("/api/"):
                return jsonify(error="Authentication required"), 401
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


def require_role(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            u = current_user()
            if not u:
                return jsonify(error="Authentication required"), 401
            if u.role not in roles:
                return jsonify(error="Insufficient permissions"), 403
            return fn(*args, **kwargs)
        return wrapper
    return deco


def get_login_csrf_secret():
    """Return a stable signing secret dedicated to the login CSRF token.

    Local development keeps this secret on disk so restarting Flask or changing
    unrelated app/session settings does not invalidate the login page token.
    A deployment may set LOGIN_CSRF_SECRET explicitly (recommended alongside
    FLASK_SECRET_KEY).
    """
    configured = os.getenv("LOGIN_CSRF_SECRET", "").strip()
    if configured:
        return configured
    if RUNNING_ON_VERCEL:
        return app.config["SECRET_KEY"]
    return _persisted_local_secret(LOGIN_CSRF_SECRET_FILE)


def login_csrf_token():
    """Create a login CSRF token that does not depend on a session cookie."""
    serializer = URLSafeTimedSerializer(get_login_csrf_secret(), salt="swastya-login-csrf")
    return serializer.dumps("login")


def login_csrf_ok(token):
    if not token:
        return False
    try:
        serializer = URLSafeTimedSerializer(get_login_csrf_secret(), salt="swastya-login-csrf")
        return serializer.loads(token, max_age=3600) == "login"
    except (BadSignature, SignatureExpired):
        return False


def csrf_ok():
    token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    session_token = session.get("csrf_token", "")
    return bool(token and session_token and secrets.compare_digest(token, session_token))


def audit(action, case_id=None, metadata=None):
    try:
        db.session.add(
            AuditEvent(
                id=uuid.uuid4().hex,
                user_id=session.get("user_id"),
                action=action,
                case_id=case_id,
                metadata_json=metadata or {},
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("Audit event failed")


def local_flags(text):
    t = (text or "").lower()
    rules = [
        (
            "Emergency signal",
            [
                "severe difficulty breathing", "unconscious", "not responding", "severe chest pain",
                "heavy bleeding", "blue lips", "convulsion", "seizure", "unable to breathe",
            ],
        ),
        (
            "Urgent review signal",
            [
                "high fever", "persistent vomiting", "fainting", "confusion", "blood in stool",
                "shortness of breath", "pregnant", "severe pain", "heavy bleeding", "very weak",
            ],
        ),
    ]
    hits = []
    for label, terms in rules:
        for term in terms:
            if term in t:
                hits.append({"label": label, "term": term})
    return hits


def fallback_note(symptoms, report, language):
    combined = ((symptoms or "") + " " + (report or "")).strip()
    flags = local_flags(combined)
    risk = "Urgent review" if any(x["label"] == "Emergency signal" for x in flags) else ("Priority review" if flags else "Routine review")
    details = [x.strip() for x in re.split(r"[\n,.;]+", symptoms or "") if x.strip()][:8]
    return {
        "summary": (symptoms or report or "No symptom narrative provided.").strip()[:1200],
        "timeline": "Timeline not reliably established from supplied information.",
        "key_details": details,
        "missing_information": [
            "Onset and duration",
            "Age and relevant history",
            "Current medications/allergies",
            "Vital signs if available",
        ],
        "follow_up_questions": [
            "When did symptoms start?",
            "Have symptoms worsened or changed?",
            "Any known medical conditions or medicines?",
            "Any relevant vital signs or recent test values?",
        ],
        "risk_category": risk,
        "risk_signals": flags,
        "handoff": "Reviewer-facing triage note only; verify all details with the patient and available records.",
        "evidence": [{"item": k, "source": "Patient narrative"} for k in details],
        "extracted_report_fields": [],
        "language": language,
    }




def ai_request_fingerprint(feature, payload):
    """Stable fingerprint of one user AI action for audit/idempotency checks."""
    canonical = json.dumps(
        {"feature": str(feature), "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_ai_request_id(value):
    value = (value or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{16,64}", value):
        return value
    return uuid.uuid4().hex


def _ai_circuit(feature=None):
    state = session.get("ai_circuit", {}) or {}
    if state.get("global"):
        return state.get("global") or {}
    if feature:
        return state.get(feature) or {}
    return {}


def _set_ai_session(feature, request_id, attempt_no, blocked=False, retry_used=False, retry_token="", reason=""):
    state = {
        "global": {
            "blocked": bool(blocked),
            "feature": feature,
            "request_id": request_id,
            "attempt_no": int(attempt_no),
            "retry_used": bool(retry_used),
            "retry_token": str(retry_token or ""),
            "reason": str(reason or "")[:300],
            "at": int(time.time()),
        },
        feature: {
            "blocked": bool(blocked),
            "request_id": request_id,
            "attempt_no": int(attempt_no),
            "retry_used": bool(retry_used),
            "retry_token": str(retry_token or ""),
            "reason": str(reason or "")[:300],
            "at": int(time.time()),
        },
    }
    session["ai_circuit"] = state
    session.modified = True


def ai_request_start(feature, request_id="", retry_token="", payload_hash=""):
    """Atomically claim exactly one provider attempt for a user action.

    A fresh request creates attempt 1. The server-issued retry token can create
    exactly one attempt 2 for that same request id. A database unique constraint
    protects against duplicate browser submits and concurrent Vercel instances.
    """
    user_id = session.get("user_id")
    if not user_id:
        return False, "Authentication required. Sign in again.", request_id, 0
    request_id = _normalize_ai_request_id(request_id)
    retry_token = (retry_token or "").strip()
    payload_hash = (payload_hash or "")[:64]

    try:
        if retry_token:
            previous = (
                AIRequestClaim.query
                .filter_by(request_id=request_id, user_id=user_id)
                .order_by(AIRequestClaim.attempt_no.desc())
                .with_for_update()
                .first()
            )
            valid = bool(
                previous
                and previous.attempt_no == 1
                and previous.feature == feature
                and previous.status == "failed"
                and not previous.retry_used
                and previous.retry_token
                and secrets.compare_digest(previous.retry_token, retry_token)
            )
            if not valid:
                db.session.rollback()
                return False, "This retry is no longer valid. Start a new patient input or recording.", request_id, 0

            previous.retry_used = True
            claim = AIRequestClaim(
                id=uuid.uuid4().hex,
                request_id=request_id,
                attempt_no=2,
                feature=feature,
                user_id=user_id,
                payload_hash=payload_hash,
                status="in_progress",
                retry_used=True,
            )
            db.session.add(claim)
            db.session.commit()
            _set_ai_session(feature, request_id, 2, blocked=False, retry_used=True)
            return True, "", request_id, 2

        existing = (
            AIRequestClaim.query
            .filter_by(request_id=request_id, user_id=user_id)
            .order_by(AIRequestClaim.attempt_no.desc())
            .first()
        )
        if existing:
            db.session.rollback()
            return False, "This AI request was already started or processed. Start a new patient input for another attempt.", request_id, existing.attempt_no

        claim = AIRequestClaim(
            id=uuid.uuid4().hex,
            request_id=request_id,
            attempt_no=1,
            feature=feature,
            user_id=user_id,
            payload_hash=payload_hash,
            status="in_progress",
            retry_used=False,
        )
        db.session.add(claim)
        db.session.commit()
        _set_ai_session(feature, request_id, 1, blocked=False, retry_used=False)
        return True, "", request_id, 1
    except IntegrityError:
        db.session.rollback()
        return False, "This AI request is already being processed. Duplicate provider calls were blocked; start a new request if needed.", request_id, 0
    except Exception:
        db.session.rollback()
        log.exception("AI request claim failed")
        return False, "The AI request could not be started safely. Start a new patient input or recording.", request_id, 0


def _active_ai_claim(feature=None):
    state = _ai_circuit(feature)
    request_id = str(state.get("request_id") or "")
    attempt_no = int(state.get("attempt_no") or 0)
    user_id = session.get("user_id")
    if not request_id or attempt_no < 1 or not user_id:
        return None
    return AIRequestClaim.query.filter_by(
        request_id=request_id, attempt_no=attempt_no, user_id=user_id,
    ).first()


def ai_request_blocked(feature=None):
    state = session.get("ai_circuit", {}) or {}
    global_state = state.get("global") or {}
    feature_state = state.get(feature) or {} if feature else {}
    return bool(global_state.get("blocked") or feature_state.get("blocked"))


def ai_retry_allowed():
    state = session.get("ai_circuit", {}) or {}
    global_state = state.get("global") or {}
    return bool(
        global_state.get("blocked")
        and int(global_state.get("attempt_no") or 0) == 1
        and not bool(global_state.get("retry_used"))
        and bool(global_state.get("retry_token"))
    )


def ai_retry_token():
    return str((session.get("ai_circuit", {}) or {}).get("global", {}).get("retry_token", ""))


def ai_request_failed(feature, reason):
    state = _ai_circuit(feature)
    request_id = str(state.get("request_id") or "")
    attempt_no = int(state.get("attempt_no") or 0)
    retry_used = bool(state.get("retry_used")) or attempt_no >= 2
    reason = str(reason or "AI request failed")[:300]
    retry_token = "" if retry_used or attempt_no != 1 else secrets.token_urlsafe(24)
    claim = None
    try:
        claim = _active_ai_claim(feature)
        if claim:
            claim.status = "failed"
            claim.error = reason
            claim.retry_used = retry_used
            claim.retry_token = retry_token
            claim.completed_at = utcnow()
            db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("AI request failure claim update failed")
    _set_ai_session(feature, request_id, attempt_no or 1, blocked=True, retry_used=retry_used, retry_token=retry_token, reason=reason)


def ai_request_finish(feature, status="completed"):
    claim = None
    try:
        claim = _active_ai_claim(feature)
        if claim:
            claim.status = str(status or "completed")[:20]
            claim.completed_at = utcnow()
            db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("AI request claim completion failed")
    state = _ai_circuit(feature)
    _set_ai_session(
        feature,
        str(state.get("request_id") or ""),
        int(state.get("attempt_no") or 1),
        blocked=False,
        retry_used=bool(state.get("retry_used")),
        reason="",
    )


def ai_failure_message(feature=None):
    state = _ai_circuit(feature)
    reason = state.get("reason") or "The previous AI request failed."
    if ai_retry_allowed():
        return f"AI processing stopped after one failed request. {reason} You have one explicit Retry for this same input."
    return f"AI processing stopped after the failed request. {reason} No further retry is available for this input; start a new patient input or recording."


def ai_stop_response(message=None, status=503):
    return jsonify(
        error=message or ai_failure_message(),
        code="AI_PROCESSING_STOPPED",
        retryable=ai_retry_allowed(),
        retry_token=ai_retry_token() if ai_retry_allowed() else "",
    ), status


class GeminiHTTPError(RuntimeError):
    def __init__(self, status_code, body="", provider_code=""):
        self.status_code = int(status_code)
        self.body = str(body or "")[:1200]
        self.provider_code = str(provider_code or "")[:120]
        suffix = f" {self.provider_code}" if self.provider_code else ""
        super().__init__(f"Gemini HTTP {self.status_code}{suffix}")


def _gemini_error_details(response):
    code = ""
    message = response.text[:1000] if response is not None else ""
    try:
        body = response.json()
        error = body.get("error") if isinstance(body, dict) else None
        if isinstance(error, dict):
            code = str(error.get("status") or error.get("code") or "")
            message = str(error.get("message") or message)[:1000]
    except Exception:
        pass
    return code, message


def _normalize_gemini_model(model):
    model = str(model or "").strip()
    if model.startswith("models/"):
        model = model[len("models/"):]
    return model


def _direct_gemini_generate_content(model, input_items):
    """Exactly one direct Gemini GenerateContent POST; no SDK, no retry, no fallback."""
    import httpx
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    model = _normalize_gemini_model(model)
    if not re.fullmatch(r"[A-Za-z0-9._-]{3,120}", model):
        raise ValueError("Invalid Gemini model name")

    if isinstance(input_items, str):
        parts = [{"text": input_items}]
    elif isinstance(input_items, list):
        parts = []
        for item in input_items:
            if not isinstance(item, dict):
                raise ValueError("Invalid Gemini input part")
            if item.get("type") == "text":
                text_value = str(item.get("text") or "")
                if text_value:
                    parts.append({"text": text_value})
            elif item.get("type") == "audio":
                parts.append({"inline_data": {
                    "mime_type": str(item.get("mime_type") or "audio/webm"),
                    "data": str(item.get("data") or ""),
                }})
            elif item.get("type") == "image":
                parts.append({"inline_data": {
                    "mime_type": str(item.get("mime_type") or "image/png"),
                    "data": str(item.get("data") or ""),
                }})
            elif item.get("type") == "document":
                parts.append({"inline_data": {
                    "mime_type": str(item.get("mime_type") or "application/pdf"),
                    "data": str(item.get("data") or ""),
                }})
            else:
                raise ValueError("Unsupported Gemini input part")
        if not parts:
            raise ValueError("Gemini input is empty")
    else:
        raise ValueError("Unsupported Gemini input")

    payload = {"contents": [{"role": "user", "parts": parts}]}
    url = GEMINI_GENERATE_URL_TEMPLATE.format(model=model)
    response = httpx.post(
        url,
        headers={"x-goog-api-key": key, "content-type": "application/json"},
        json=payload,
        timeout=110.0,
        follow_redirects=False,
    )
    if response.status_code >= 400:
        code, message = _gemini_error_details(response)
        raise GeminiHTTPError(response.status_code, message, code)
    try:
        data = response.json()
    except Exception as exc:
        raise RuntimeError("Gemini returned a non-JSON GenerateContent response") from exc
    return data


def _direct_output_text(data):
    """Extract text from the GenerateContent response candidates."""
    if not isinstance(data, dict):
        return ""
    direct = data.get("text")
    if direct:
        return str(direct).strip()
    chunks = []
    for candidate in data.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content") or {}
        for part in content.get("parts") or []:
            if isinstance(part, dict) and part.get("text"):
                chunks.append(str(part["text"]))
    return "\n".join(chunks).strip()


def _generate_content_input(prompt, file_bytes=None, mime_type=None):
    """Build documented GenerateContent REST parts using inline media for small uploads."""
    parts = [{"type": "text", "text": prompt}]
    if not file_bytes or not mime_type:
        return parts
    encoded = base64.b64encode(file_bytes).decode("ascii")
    if mime_type == "application/pdf":
        parts.append({"type": "document", "data": encoded, "mime_type": mime_type})
    elif mime_type in {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif", "image/gif", "image/bmp", "image/tiff"}:
        parts.append({"type": "image", "data": encoded, "mime_type": mime_type})
    else:
        raise ValueError("Unsupported Gemini media type")
    return parts


def _gemini_interaction(_client, model, prompt, file_bytes=None, mime_type=None, json_output=False):
    # Compatibility wrapper: all application AI calls now use GenerateContent REST.
    if json_output:
        prompt = prompt + "\nReturn ONLY one valid JSON object. Do not use Markdown fences or commentary outside the JSON."
    items = _generate_content_input(prompt, file_bytes, mime_type)
    data = _direct_gemini_generate_content(model, items)
    return _direct_output_text(data)

def gemini_generate(prompt, file_bytes=None, mime_type=None, feature="triage", json_output=True):
    if ai_request_blocked(feature):
        return None, ai_failure_message(feature)
    if not os.getenv("GEMINI_API_KEY", "").strip():
        ai_request_failed(feature, "Gemini is not configured.")
        return None, "Gemini is not configured. Add GEMINI_API_KEY and start a new request."
    try:
        text = _gemini_interaction(None, GEMINI_MODEL, prompt, file_bytes, mime_type, json_output=json_output)
        if text:
            return text, None
        raise RuntimeError("Gemini returned an empty model output")
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        provider_code = getattr(exc, "provider_code", "")
        ai_request_failed(feature, f"Gemini request failed ({status_code or type(exc).__name__}{(': '+provider_code) if provider_code else ''}).")
        log.warning("Gemini request failed for %s: %s | detail=%s", feature, str(exc)[:240], getattr(exc, "body", "")[:600])
        if status_code == 429:
            return None, "Gemini rate limit/quota response (HTTP 429). Processing stopped. Use the one Retry after quota/rate limit is available."
        if status_code == 400:
            return None, "Gemini rejected the request (HTTP 400). Processing stopped. The request was not retried automatically."
        return None, f"Gemini is temporarily unavailable ({type(exc).__name__}). Processing stopped; no automatic retry or fallback was used."


def gemini_text_generate(prompt, feature="translation"):
    return gemini_generate(prompt, feature=feature, json_output=False)

GEMINI_TRIAGE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "input_valid": {"type": "boolean"},
        "error": {"type": "string"},
        "summary": {"type": "string"},
        "timeline": {"type": "string"},
        "key_details": {"type": "array", "items": {"type": "string"}},
        "missing_information": {"type": "array", "items": {"type": "string"}},
        "follow_up_questions": {"type": "array", "items": {"type": "string"}},
        "risk_category": {"type": "string", "enum": ["Routine review", "Priority review", "Urgent review", "Needs review"]},
        "risk_signals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"label": {"type": "string"}, "term": {"type": "string"}},
                "required": ["label", "term"],
            },
        },
        "handoff": {"type": "string"},
        "extracted_report_fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"},
                    "value": {"type": "string"},
                    "source": {"type": "string"},
                },
            },
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"item": {"type": "string"}, "source": {"type": "string"}},
                "required": ["item", "source"],
            },
        },
    },
    "required": [
        "input_valid", "summary", "timeline", "key_details", "missing_information",
        "follow_up_questions", "risk_category", "risk_signals", "handoff",
        "extracted_report_fields", "evidence",
    ],
}

GEMINI_VOICE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "transcript": {"type": "string"},
        "translation": {"type": "string"},
    },
    "required": ["transcript", "translation"],
}


def parse_ai(text, symptoms, report, language):
    if not text:
        return None
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S).strip()
    try:
        data = json.loads(cleaned)
    except Exception:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        try:
            data = json.loads(match.group(0)) if match else None
        except Exception:
            data = None
    if isinstance(data, dict):
        data.setdefault("input_valid", True)
        data.setdefault("error", "")
        data.setdefault("summary", "")
        data.setdefault("timeline", "Timeline needs reviewer verification.")
        data.setdefault("key_details", [])
        data.setdefault("missing_information", [])
        data.setdefault("follow_up_questions", [])
        data.setdefault("risk_category", "Needs review")
        data.setdefault("risk_signals", local_flags((symptoms or "") + " " + (report or "")))
        data.setdefault("evidence", [])
        data.setdefault("extracted_report_fields", [])
        return data
    return None


HEALTH_CONTEXT_TERMS = {
    "health", "medical", "medicine", "medication", "patient", "doctor", "clinic", "hospital", "symptom",
    "illness", "disease", "diagnosis", "treatment", "injury", "wound", "pain", "fever", "cough", "cold",
    "headache", "vomit", "vomiting", "diarrhea", "breathing", "breathless", "chest", "blood", "urine",
    "sugar", "diabetes", "pressure", "hypertension", "pregnancy", "pregnant", "maternal", "child", "infant",
    "infection", "allergy", "allergic", "rash", "swelling", "fracture", "burn", "ultrasound", "xray", "x-ray",
    "mri", "ct scan", "scan", "ecg", "ekg", "lab", "laboratory", "pathology", "radiology", "prescription",
    "tablet", "capsule", "dose", "blood test", "urine test", "report", "screening", "referral", "vital", "pulse",
    "temperature", "oxygen", "spo2", "heart", "lung", "kidney", "liver", "maternal", "chronic", "occupational"
}
UNRELATED_TERMS = {
    "resume", "cv", "assignment", "school assignment", "college assignment", "homework", "exam paper", "question paper", "research paper", "invoice", "receipt", "bank statement", "credit card", "passport", "aadhaar", "pan card",
    "driving licence", "flight ticket", "hotel booking", "restaurant menu", "shopping receipt", "movie", "song lyrics",
    "homework", "exam paper", "math problem", "programming code", "source code", "car manual", "vehicle registration",
    "property document", "rental agreement", "legal contract", "wedding invitation", "travel itinerary"
}

def health_relevance_error(symptoms, report, filename=""):
    """Reject clearly unrelated text; a filename alone never proves a document is medical."""
    body = " ".join(x for x in (symptoms, report) if x).lower()
    name = (filename or "").lower()
    for term in UNRELATED_TERMS:
        if term in body or term in name:
            return f"This input appears unrelated to healthcare ({term}). Please provide a patient symptom description or a genuine health report."
    if not body.strip() and not name.strip():
        return "Provide symptoms, health context, or a healthcare-related report."
    normalized = re.sub(r"[^a-z0-9+/#.\- ]+", " ", body)
    if body.strip() and len(normalized.split()) >= 4 and not any(term in normalized for term in HEALTH_CONTEXT_TERMS):
        return "This input does not appear to contain healthcare information. Please provide symptoms, health context, or a medical report."
    # Names such as medical-report.pdf are only hints; content must still be checked by AI.
    return None

def validate_report(raw, mime_type):
    if mime_type not in ALLOWED_REPORT_TYPES:
        raise ValueError("Upload PNG, JPG/JPEG, or PDF only")
    if not raw:
        raise ValueError("The uploaded report is empty")
    if len(raw) > MAX_REPORT_BYTES:
        raise OverflowError(f"Report must be smaller than {MAX_REPORT_BYTES // (1024 * 1024)} MB")
    try:
        if mime_type in {"image/png", "image/jpeg"}:
            image = Image.open(io.BytesIO(raw))
            image.verify()
        elif not raw.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF file")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as exc:
        raise ValueError("Invalid or unsafe report file") from exc
    return raw


def extract_pdf_text(raw):
    """Best-effort local text extraction; image OCR remains optional via Gemini."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        return text.strip()[:10000]
    except Exception:
        return ""


def serialize_case(c):
    return {
        "id": c.id,
        "created_at": c.created_at.isoformat(),
        "patient_ref": c.patient_ref,
        "patient_name": c.patient_name,
        "age": c.age,
        "gender": c.gender,
        "address": c.address,
        "consent": c.consent,
        "report_filename": c.report_filename,
        "report_available": bool(c.report_data) or bool(c.report_path),
        "language": c.language,
        "symptoms": c.symptoms,
        "report_text": c.report_text,
        "ai_note": c.ai_note,
        "risk": c.risk,
        "status": c.status,
        "reviewer_note": c.reviewer_note,
        "source": c.source,
        "scenario": c.scenario,
        "reviewed_by": c.reviewed_by,
        "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
    }


def risk_sort_key(case):
    priority = {"Urgent review": 0, "Priority review": 1, "Needs review": 2, "Routine review": 3}
    status_priority = {"Needs review": 0, "Needs more information": 1, "Escalated": 2, "Reviewed": 3}
    return (priority.get(case.risk, 2), status_priority.get(case.status, 4), -case.created_at.timestamp())


@app.errorhandler(413)
def too_large(_error):
    if request.path.startswith("/api/"):
        return jsonify(error=f"Request is too large. Keep the entire upload request under {MAX_CONTENT_BYTES // (1024 * 1024)} MB."), 413
    return "Request is too large.", 413


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify(error="Not found"), 404
    return render_template("home.html"), 404


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=(), payment=()"
    resp.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    resp.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    resp.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data: blob:; media-src 'self' blob:; "
        "style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
        "base-uri 'self'; form-action 'self'; object-src 'none'"
    )
    if request.path.startswith("/api/") or request.path in {"/console", "/admin", "/login", "/register"}:
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    if request.is_secure:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp


@app.context_processor
def globals_ctx():
    u = current_user()
    return {"current_user": u, "disclaimer": DISCLAIMER, "csrf_token": session.get("csrf_token", "")}


@app.get("/healthz")
def healthz():
    return jsonify(status="ok", service="swastya-assist")


@app.get("/readyz")
def readyz():
    checks = {"database": False, "secret": False, "encryption": False, "persistent_db": False, "rate_limit_store": False, "cron_secret": False, "admin_config": False, "login_csrf_secret": False, "secure_cookie": False}
    try:
        db.session.execute(db.text("SELECT 1"))
        checks["database"] = True
    except Exception:
        log.exception("Readiness database check failed")
    checks["secret"] = bool(os.getenv("FLASK_SECRET_KEY")) or not RUNNING_ON_VERCEL
    checks["encryption"] = bool(os.getenv("DATA_ENCRYPTION_KEY")) or not RUNNING_ON_VERCEL
    checks["persistent_db"] = bool(RAW_DATABASE_URL) if RUNNING_ON_VERCEL else True
    rate_store = (os.getenv("RATELIMIT_STORAGE_URI", "").strip() or os.getenv("REDIS_URL", "").strip() or "memory://").lower()
    checks["rate_limit_store"] = (not rate_store.startswith("memory://")) if RUNNING_ON_VERCEL else True
    checks["cron_secret"] = bool(os.getenv("CRON_SECRET", "").strip()) if RUNNING_ON_VERCEL else True
    checks["admin_config"] = bool(os.getenv("ADMIN_USERNAME", "").strip()) and bool(os.getenv("ADMIN_PASSWORD", "").strip()) if RUNNING_ON_VERCEL else True
    checks["login_csrf_secret"] = bool(os.getenv("LOGIN_CSRF_SECRET", "").strip()) if RUNNING_ON_VERCEL else True
    checks["secure_cookie"] = bool(app.config.get("SESSION_COOKIE_SECURE")) if RUNNING_ON_VERCEL else True
    ok = all(checks.values())
    return jsonify(status="ready" if ok else "not_ready", checks=checks, ai_enabled=bool(os.getenv("GEMINI_API_KEY"))), (200 if ok else 503)


def safe_next_url(value):
    value = (value or "").strip()
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or not value.startswith("/"):
        return None
    return value


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()[:120]
        password = request.form.get("password", "")[:512]
        selected_role = request.form.get("role", "clinical")
        if not login_csrf_ok(request.form.get("csrf_token", "")):
            response = render_template(
                "login.html",
                error="The sign-in token is stale or the app secret changed. Reload the sign-in page and submit again. Keep FLASK_SECRET_KEY fixed in .env for local testing.",
                selected_role=selected_role,
                csrf_token=login_csrf_token(),
            )
            return response, 400
        u = User.query.filter_by(username=username).first()
        if not u or not u.active or not check_password_hash(u.password_hash, password):
            audit("login_failed", metadata={"role_hint": selected_role})
            return render_template("login.html", error="Invalid credentials", selected_role=selected_role), 401
        if selected_role == "admin" and u.role != "admin":
            audit("login_role_mismatch", metadata={"username": username, "requested": selected_role})
            return render_template("login.html", error="This account is not an administrator. Choose Clinical Team or use an admin account.", selected_role=selected_role), 403
        if selected_role == "clinical" and u.role == "admin":
            audit("login_role_mismatch", metadata={"username": username, "requested": selected_role})
            return render_template("login.html", error="This is an administrator account. Choose Administrator to continue.", selected_role=selected_role), 403
        session.clear()
        session["user_id"] = u.id
        session["csrf_token"] = secrets.token_urlsafe(32)
        audit("login")
        next_url = safe_next_url(request.args.get("next")) or url_for("admin_dashboard" if u.role == "admin" else "index")
        return redirect(next_url)
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    response = render_template("login.html", csrf_token=login_csrf_token())
    response = app.make_response(response)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def register():
    if request.method == "POST":
        if not csrf_ok():
            abort(400)
        username = request.form.get("username", "").strip().lower()[:120]
        password = request.form.get("password", "")[:512]
        role = request.form.get("role", "reviewer")
        if not re.fullmatch(r"[a-z0-9._-]{3,120}", username) or len(password) < MIN_PASSWORD_LENGTH or role not in {"reviewer", "doctor"}:
            return render_template("register.html", error="Use a valid username, a password of at least 12 characters, and Doctor or Reviewer."), 400
        if User.query.filter_by(username=username).first():
            return render_template("register.html", error="That username is already in use."), 409
        existing_request = RegistrationRequest.query.filter_by(username=username).first()
        if existing_request and existing_request.status == "pending":
            return render_template("register.html", error="That username is already awaiting approval."), 409
        if existing_request:
            existing_request.password_hash = generate_password_hash(password)
            existing_request.role = role
            existing_request.status = "pending"
        else:
            db.session.add(RegistrationRequest(id=uuid.uuid4().hex, username=username, password_hash=generate_password_hash(password), role=role))
        db.session.commit()
        audit("registration_requested", metadata={"username": username, "role": role})
        return render_template("register.html", submitted=True, username=username)
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return render_template("register.html")


@app.post("/logout")
@require_login
def logout():
    if not csrf_ok():
        abort(400)
    audit("logout")
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
def home():
    return render_template("home.html")


@app.get("/console")
@require_role("reviewer", "doctor", "admin")
def index():
    cases = Case.query.order_by(Case.created_at.desc()).limit(100).all()
    return render_template("index.html", cases=[serialize_case(c) for c in cases])


@app.get("/admin")
@require_role("admin")
def admin_dashboard():
    cases = Case.query.order_by(Case.created_at.desc()).limit(100).all()
    users = User.query.order_by(User.created_at.desc()).all()
    requests = RegistrationRequest.query.filter_by(status="pending").order_by(RegistrationRequest.created_at.asc()).all()
    recent_cutoff = utcnow() - timedelta(minutes=5)
    events = AuditEvent.query.filter(AuditEvent.created_at >= recent_cutoff).order_by(AuditEvent.created_at.desc()).limit(100).all()
    total = len(cases)
    reviewed = sum(1 for c in cases if c.status in ["Reviewed", "Escalated"])
    urgent = sum(1 for c in cases if c.risk == "Urgent review")
    return render_template("admin.html", cases=cases, users=users, requests=requests, events=events, total=total, reviewed=reviewed, urgent=urgent, review_rate=round(reviewed / total * 100, 1) if total else 0)


@app.post("/admin/users")
@require_role("admin")
def admin_create_user():
    if not csrf_ok():
        abort(400)
    username = request.form.get("username", "").strip().lower()[:120]
    password = request.form.get("password", "")[:512]
    role = request.form.get("role", "reviewer")
    if not re.fullmatch(r"[a-z0-9._-]{3,120}", username) or len(password) < MIN_PASSWORD_LENGTH or role not in {"reviewer", "doctor", "admin"}:
        return redirect(url_for("admin_dashboard", error="Invalid user details"))
    if User.query.filter_by(username=username).first():
        return redirect(url_for("admin_dashboard", error="Username already exists"))
    db.session.add(User(id=uuid.uuid4().hex, username=username, password_hash=generate_password_hash(password), role=role))
    db.session.commit()
    audit("admin_user_created", metadata={"username": username, "role": role})
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/requests/<rid>/approve")
@require_role("admin")
def approve_request(rid):
    if not csrf_ok():
        abort(400)
    req = db.session.get(RegistrationRequest, rid)
    if not req or req.status != "pending":
        return redirect(url_for("admin_dashboard"))
    if User.query.filter_by(username=req.username).first():
        req.status = "rejected"
        db.session.commit()
        return redirect(url_for("admin_dashboard"))
    db.session.add(User(id=uuid.uuid4().hex, username=req.username, password_hash=req.password_hash, role=req.role, active=True))
    req.status = "approved"
    db.session.commit()
    audit("registration_approved", metadata={"username": req.username, "role": req.role})
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/requests/<rid>/reject")
@require_role("admin")
def reject_request(rid):
    if not csrf_ok():
        abort(400)
    req = db.session.get(RegistrationRequest, rid)
    if req and req.status == "pending":
        req.status = "rejected"
        db.session.commit()
        audit("registration_rejected", metadata={"username": req.username, "role": req.role})
    return redirect(url_for("admin_dashboard"))


def delete_report_blob(case):
    if case.report_path:
        try:
            path = Path(case.report_path).resolve()
            path.relative_to(UPLOADS.resolve())
            path.unlink(missing_ok=True)
        except Exception:
            log.warning("Legacy report path could not be removed", exc_info=True)
    case.report_data = None
    case.report_path = ""


@app.post("/admin/cases/<cid>/delete")
@require_role("admin")
def admin_delete_case(cid):
    if not csrf_ok():
        abort(400)
    c = db.session.get(Case, cid)
    if not c:
        return redirect(url_for("admin_dashboard"))
    patient_ref = c.patient_ref
    delete_report_blob(c)
    db.session.delete(c)
    db.session.commit()
    audit("case_deleted", metadata={"patient_ref": patient_ref})
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/users/<uid>/delete")
@require_role("admin")
def admin_delete_user(uid):
    if not csrf_ok():
        abort(400)
    u = db.session.get(User, uid)
    if not u or u.id == session.get("user_id"):
        return redirect(url_for("admin_dashboard"))
    username = u.username
    db.session.delete(u)
    db.session.commit()
    audit("admin_user_deleted", metadata={"username": username})
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/users/<uid>/toggle")
@require_role("admin")
def admin_toggle_user(uid):
    if not csrf_ok():
        abort(400)
    u = db.session.get(User, uid)
    if not u or u.id == session.get("user_id"):
        return redirect(url_for("admin_dashboard"))
    u.active = not u.active
    db.session.commit()
    audit("admin_user_status_changed", metadata={"username": u.username, "active": u.active})
    return redirect(url_for("admin_dashboard"))


@app.post("/api/triage")
@require_login
@limiter.limit("30 per minute")
def triage():
    retry_token = request.form.get("_ai_retry_token", "").strip()
    request_id = request.form.get("_ai_request_id", "").strip()
    if not csrf_ok():
        return jsonify(error="CSRF validation failed"), 400

    symptoms = request.form.get("symptoms", "").strip()
    report = request.form.get("report_text", "").strip()
    language = request.form.get("language", "English").strip()
    source = request.form.get("source", "Patient intake").strip()[:80]
    scenario = request.form.get("scenario", "Outpatient queue triage").strip()[:80]
    patient_ref = (request.form.get("patient_ref", "").strip() or "SYN-" + uuid.uuid4().hex[:8].upper())[:80]
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,80}", patient_ref):
        return jsonify(error="Patient reference may contain letters, numbers, underscores and hyphens only"), 400
    patient_name = request.form.get("patient_name", "").strip()[:160]
    gender = request.form.get("gender", "").strip()[:40]
    address = request.form.get("address", "").strip()[:2000]
    consent = request.form.get("consent") == "on"
    age_raw = request.form.get("age", "").strip()
    age = int(age_raw) if age_raw.isdigit() and 0 <= int(age_raw) <= 130 else None

    if not patient_name:
        return jsonify(error="Patient name is required"), 400
    if age is None:
        return jsonify(error="Valid patient age is required"), 400
    if not consent:
        return jsonify(error="Consent confirmation is required"), 400
    if not address:
        return jsonify(error="Address is required"), 400
    if language not in ALLOWED_LANGUAGES:
        return jsonify(error="Unsupported language"), 400
    if scenario not in ALLOWED_SCENARIOS:
        return jsonify(error="Unsupported care scenario"), 400
    if len(symptoms) > 10000 or len(report) > 10000:
        return jsonify(error="Input too large"), 413

    upload = request.files.get("report_image")
    filename_hint = secure_filename(upload.filename)[:255] if upload and upload.filename else ""
    relevance_error = health_relevance_error(symptoms, report, filename_hint) if HEALTH_INPUT_GATE else None
    if relevance_error:
        return jsonify(error=relevance_error, code="NON_HEALTH_INPUT"), 422
    image_bytes = None
    mime = None
    report_filename = ""
    report_mime = ""
    report_data = None

    if upload and upload.filename:
        mime = (upload.mimetype or "").split(";", 1)[0].lower()
        raw = upload.read()
        try:
            validate_report(raw, mime)
        except OverflowError as exc:
            return jsonify(error=str(exc)), 413
        except ValueError as exc:
            return jsonify(error=str(exc)), 415
        image_bytes = raw
        report_mime = mime
        report_filename = secure_filename(upload.filename)[:255]
        report_data = raw
        if mime == "application/pdf" and not report:
            extracted = extract_pdf_text(raw)
            if extracted:
                report = extracted

    relevance_error = health_relevance_error(symptoms, report, filename_hint) if HEALTH_INPUT_GATE else None
    if relevance_error:
        return jsonify(error=relevance_error, code="NON_HEALTH_REPORT"), 422

    payload_hash = ai_request_fingerprint("triage", {
        "patient_ref": patient_ref, "patient_name": patient_name, "age": age, "gender": gender,
        "address": address, "language": language, "scenario": scenario, "symptoms": symptoms,
        "report": report, "report_sha256": hashlib.sha256(report_data).hexdigest() if report_data else "",
        "source": source,
    })
    started, start_error, request_id, _attempt_no = ai_request_start("triage", request_id, retry_token, payload_hash)
    if not started:
        return jsonify(error=start_error, code="AI_REQUEST_DUPLICATE" if "already" in start_error.lower() or "processed" in start_error.lower() else "AI_RETRY_INVALID", retryable=False), 409

    prompt = f"""
You are a non-diagnostic healthcare triage documentation assistant for Indian public/institutional health facilities.
Produce ONLY valid JSON with keys: input_valid, error, summary, timeline, key_details (array), missing_information (array),
follow_up_questions (array), risk_category, risk_signals (array), handoff, extracted_report_fields (array),
evidence (array). Set input_valid=false and give a short error if the supplied narrative/report is clearly unrelated to healthcare. Do not create a case when input_valid=false. Evidence items must contain item and source from: Patient narrative, Report text,
Uploaded report, Not provided. Do not diagnose, prescribe, or recommend treatment. Risk category must be one of
Routine review, Priority review, Urgent review, Needs review. Highlight urgency signals conservatively and tell a
qualified reviewer to verify. Language: {language}. Patient age: {age}. Gender: {gender}. Scenario: {scenario}.
Symptoms: {symptoms}. Report text: {report}.
If an image or PDF is supplied, first decide whether its actual contents are healthcare-related. A filename such as "medical-report.pdf" is untrusted and is NOT evidence that the document is medical. If the document content is an assignment, invoice, identity document, travel document, unrelated paperwork, or otherwise not healthcare-related, set input_valid=false and explain the error. Extract only clearly readable factual values and mark uncertainty. Never invent values.
Scenario guidance: outpatient=queue prioritization; occupational=workplace exposure/injury context;
campus fever=fever duration and associated symptoms; maternal follow-up=gestational/follow-up details if provided;
chronic disease=condition history and adherence information if provided; public health camp=basic screening completeness;
referral note=reason for referral and information gaps. AI output is reviewer-facing only.
""".strip()

    if TEST_MODE and not os.getenv("GEMINI_API_KEY", "").strip():
        test_note = fallback_note(symptoms, report, language)
        test_note["input_valid"] = True
        test_note["error"] = ""
        ai_text, warning = json.dumps(test_note), ""
    else:
        ai_text, warning = gemini_generate(prompt, image_bytes, mime, feature="triage", json_output=True)
        if warning and not ai_text:
            return ai_stop_response(warning, 503)
    data = parse_ai(ai_text, symptoms, report, language)
    if data is None:
        ai_request_failed("triage", "Gemini returned an invalid structured response.")
        return ai_stop_response("Gemini returned an invalid structured response. No case was created.", 502)
    if data.get("input_valid") is False:
        ai_request_finish("triage", "rejected")
        return jsonify(error=(data.get("error") or "The supplied material does not appear to be healthcare-related."), code="NON_HEALTH_INPUT"), 422
    flags = local_flags(symptoms + " " + report)
    if any(f["label"] == "Emergency signal" for f in flags):
        data["risk_category"] = "Urgent review"
    elif flags and data.get("risk_category") == "Routine review":
        data["risk_category"] = "Priority review"
    deduped = {}
    for flag in (data.get("risk_signals") or []) + flags:
        key = (str(flag.get("label", "")), str(flag.get("term", ""))) if isinstance(flag, dict) else ("Signal", str(flag))
        deduped[key] = flag if isinstance(flag, dict) else {"label": "Signal", "term": str(flag)}
    data["risk_signals"] = list(deduped.values())
    data["language"] = language
    data["safety"] = "Advisory reviewer-facing documentation; not a diagnosis or treatment recommendation."

    c = Case(
        id=uuid.uuid4().hex,
        patient_ref=patient_ref,
        patient_name=patient_name,
        age=age,
        gender=gender,
        address=address,
        consent=consent,
        report_filename=report_filename,
        report_mime=report_mime,
        report_data=report_data,
        report_path="",
        language=language,
        symptoms=symptoms,
        report_text=report,
        ai_note=data,
        risk=data.get("risk_category", "Needs review"),
        status="Needs review",
        source=source,
        scenario=scenario,
    )
    db.session.add(c)
    db.session.commit()
    audit("triage_created", c.id, {"source": source, "has_report": bool(report_data), "risk": c.risk})
    ai_request_finish("triage", "completed")
    payload = jsonify(
        id=c.id,
        note=data,
        warning=warning,
        disclaimer=DISCLAIMER,
        patient={"name": patient_name, "age": age, "gender": gender, "reference": patient_ref},
    )
    if request.headers.get("X-Requested-With") != "XMLHttpRequest" and request.accept_mimetypes.best == "text/html":
        return redirect(url_for("index", created=c.id, ai_warning=warning or ""))
    return payload


@app.get("/api/cases/<cid>/report")
@require_role("reviewer", "doctor", "admin")
def case_report(cid):
    c = db.session.get(Case, cid)
    if not c:
        return jsonify(error="Not found"), 404
    audit("case_report_opened", cid)
    if c.report_data:
        return send_file(io.BytesIO(c.report_data), mimetype=c.report_mime or "application/octet-stream", download_name=c.report_filename or "report", as_attachment=False, max_age=0)
    if c.report_path:
        path = Path(c.report_path).resolve()
        try:
            path.relative_to(UPLOADS.resolve())
        except ValueError:
            return jsonify(error="Invalid report location"), 400
        if path.is_file():
            return send_file(path, download_name=c.report_filename or "report", as_attachment=False, max_age=0)
    return jsonify(error="Report file is no longer available"), 404


@app.get("/api/cases/<cid>/packet")
@require_role("reviewer", "doctor", "admin")
def case_packet(cid):
    c = db.session.get(Case, cid)
    if not c:
        return jsonify(error="Not found"), 404
    audit("case_packet_viewed", cid)
    n = c.ai_note or {}
    return jsonify(
        packet={
            "title": "Swastya Assist Reviewer Packet",
            "patient": {
                "reference": c.patient_ref, "name": c.patient_name, "age": c.age,
                "gender": c.gender, "language": c.language, "scenario": c.scenario,
            },
            "inputs": {"symptoms": c.symptoms, "report_text": c.report_text, "report_filename": c.report_filename},
            "ai": n,
            "risk": c.risk,
            "status": c.status,
            "reviewer_note": c.reviewer_note,
            "reviewer": c.reviewed_by,
            "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
            "disclaimer": DISCLAIMER,
        }
    )




def _parse_voice_sections(text):
    cleaned = re.sub(r"^```(?:text|txt)?\s*|\s*```$", "", (text or "").strip(), flags=re.I | re.S).strip()
    m = re.search(r"TRANSCRIPT\s*:\s*(.*?)\s*TRANSLATION\s*:\s*(.*)$", cleaned, flags=re.I | re.S)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Be tolerant if a model returns the same payload as JSON despite the plain-text instruction.
    try:
        data = json.loads(cleaned)
        return str(data.get("transcript", "")).strip(), str(data.get("translation", "")).strip()
    except Exception:
        return "", ""

@app.post("/api/voice")
@require_login
@limiter.limit("10 per minute")
def voice_api():
    retry_token = request.form.get("_ai_retry_token", "").strip()
    request_id = request.form.get("_ai_request_id", "").strip()
    if not csrf_ok():
        return jsonify(error="CSRF validation failed"), 400
    audio = request.files.get("audio")
    source_language = request.form.get("source_language", "en-IN").strip()[:20]
    target_language = request.form.get("target_language", "English").strip()[:40]
    browser_transcript = request.form.get("browser_transcript", "").strip()[:12000]
    if not audio or not audio.filename:
        return jsonify(error="Audio recording is required"), 400
    mime = (audio.mimetype or "audio/webm").split(";", 1)[0].lower()
    if mime not in ALLOWED_AUDIO_TYPES and mime != "application/octet-stream":
        return jsonify(error="Unsupported audio format. Use WebM, OGG, MP4 or WAV."), 415
    raw = audio.read()
    if not raw:
        return jsonify(error="The recording is empty. Record again and try once more."), 400
    if len(raw) > MAX_AUDIO_BYTES:
        return jsonify(error=f"Audio must be smaller than {MAX_AUDIO_BYTES // (1024 * 1024)} MB"), 413

    audio_mime = "audio/webm" if mime == "application/octet-stream" else mime
    # Inline audio is small enough for our 2 MB limit and removes the Files API
    # upload/delete traffic. One user action therefore equals one provider POST.
    payload_hash = ai_request_fingerprint("voice", {
        "audio_sha256": hashlib.sha256(raw).hexdigest(),
        "source_language": source_language, "target_language": target_language,
        "browser_transcript": browser_transcript,
    })
    started, start_error, request_id, _attempt_no = ai_request_start("voice", request_id, retry_token, payload_hash)
    if not started:
        return jsonify(error=start_error, code="AI_REQUEST_DUPLICATE" if "already" in start_error.lower() else "AI_RETRY_INVALID", retryable=False), 409
    if not os.getenv("GEMINI_API_KEY", "").strip():
        ai_request_failed("voice", "Gemini is not configured.")
        return ai_stop_response("Gemini is not configured. Add GEMINI_API_KEY and start a new voice request.", 503)

    voice_prompt = (
        "You are a multilingual speech transcription and translation assistant for a non-diagnostic "
        "healthcare intake workflow. Listen to the attached patient recording. Transcribe the patient's "
        "spoken words faithfully without diagnosing, summarizing, inferring, or adding information. "
        f"The browser-selected source locale is {source_language}; use it only as a hint and auto-detect "
        "when different. Translate the same patient statement into " + target_language + ". "
        "Return JSON with exactly two strings: transcript and translation. Preserve the patient's meaning "
        "and do not invent words, medical facts, symptoms, or treatment advice."
    )
    voice_items = [
        {"type": "text", "text": voice_prompt},
        {"type": "audio", "data": base64.b64encode(raw).decode("ascii"), "mime_type": audio_mime},
    ]
    try:
        data = _direct_gemini_generate_content(GEMINI_VOICE_MODEL, voice_items)
        output = _direct_output_text(data)
        transcript, translation = _parse_voice_sections(output)
        if not transcript:
            raise RuntimeError("Gemini returned no transcript")
        if not translation and target_language.lower() in {source_language.lower(), "english"} and source_language.lower().startswith("en"):
            translation = transcript
        if not translation:
            raise RuntimeError("Gemini returned no translation")
    except Exception as exc:
        status_code = getattr(exc, "status_code", None)
        provider_code = getattr(exc, "provider_code", "")
        ai_request_failed("voice", f"Voice Gemini request failed ({status_code or type(exc).__name__}{(': '+provider_code) if provider_code else ''}).")
        log.warning("Gemini voice request failed: %s | detail=%s", str(exc)[:240], getattr(exc, "body", "")[:600])
        message = (
            "Gemini rejected the voice request (HTTP 400)." if status_code == 400 else
            "Gemini rate limit/quota response (HTTP 429)." if status_code == 429 else
            "Gemini is temporarily unavailable." if status_code in {500, 502, 503, 504} else
            "Gemini voice processing failed."
        )
        if browser_transcript:
            response, status = ai_stop_response(message + " Processing stopped. Retry this recording once.", 503)
            body = response.get_json() or {}
            body.update({"transcript": browser_transcript, "translation": "", "ai_available": False})
            return jsonify(**body), status
        return ai_stop_response(message + " Processing stopped. Retry this recording once.", 503)

    ai_request_finish("voice", "completed")
    audit("voice_ai_processed", metadata={"source_language": source_language, "target_language": target_language, "model": GEMINI_VOICE_MODEL})
    warning = "AI transcription and translation are advisory; verify the patient statement with the patient."
    return jsonify(transcript=transcript, translation=translation, warning=warning, ai_available=True, model=GEMINI_VOICE_MODEL)


@app.get("/api/cases")
@require_login
def cases_api():
    try:
        limit = min(max(int(request.args.get("limit", "100")), 1), 200)
    except ValueError:
        limit = 100
    status = request.args.get("status", "").strip()
    risk = request.args.get("risk", "").strip()
    query = Case.query
    if status:
        query = query.filter_by(status=status)
    if risk:
        query = query.filter_by(risk=risk)
    cases = query.order_by(Case.created_at.desc()).limit(200).all()
    cases.sort(key=risk_sort_key)
    return jsonify(cases=[serialize_case(c) for c in cases[:limit]])


@app.get("/api/cases/<cid>")
@require_login
def case_api(cid):
    c = db.session.get(Case, cid)
    if not c:
        return jsonify(error="Not found"), 404
    audit("case_viewed", cid)
    return jsonify(serialize_case(c))


@app.post("/api/cases/<cid>/review")
@require_role("reviewer", "doctor", "admin")
@limiter.limit("60 per minute")
def review(cid):
    if not csrf_ok():
        return jsonify(ok=False, error="CSRF validation failed. Refresh the console and try again."), 400
    c = db.session.get(Case, cid)
    if not c:
        return jsonify(ok=False, error="Case not found"), 404
    payload = request.get_json(silent=True) or {}
    status = (payload.get("status") if payload else request.form.get("status", "Needs review")) or "Needs review"
    note = (payload.get("reviewer_note") if payload else request.form.get("reviewer_note", "")) or ""
    status = str(status).strip()
    note = str(note).strip()[:5000]
    if status not in ALLOWED_REVIEW_STATUSES:
        return jsonify(ok=False, error="Invalid reviewer status"), 400
    ai_risk = (c.risk or "").strip()
    urgent_verified = str(payload.get("urgent_verified") if payload else request.form.get("urgent_verified", "")).lower() in {"1", "true", "on", "yes"}
    if ai_risk == "Urgent review" and status in {"Reviewed", "Escalated"} and not urgent_verified:
        return jsonify(ok=False, error="This AI result is marked Urgent review. Confirm that you checked the urgency signal before saving Reviewed or Escalated."), 400
    if ai_risk == "Urgent review" and urgent_verified:
        audit("urgent_ai_signal_verified", cid, {"reviewer": current_user().id, "status": status})
    try:
        now = utcnow()
        c.reviewer_note = note
        c.status = status
        c.reviewed_by = current_user().id
        c.reviewed_at = now
        db.session.commit()
    except Exception:
        db.session.rollback()
        log.exception("Reviewer decision save failed")
        return jsonify(ok=False, error="Reviewer decision could not be saved. Check the server log for details."), 500
    audit("case_reviewed", cid, {"status": status})
    return jsonify(ok=True, case=serialize_case(c), message="Reviewer decision saved.", saved_at=now.isoformat())


@app.get("/api/analytics")
@require_role("reviewer", "doctor", "admin")
def analytics():
    cases = Case.query.all()
    risks, statuses, languages, scenarios = {}, {}, {}, {}
    for c in cases:
        risks[c.risk] = risks.get(c.risk, 0) + 1
        statuses[c.status] = statuses.get(c.status, 0) + 1
        languages[c.language] = languages.get(c.language, 0) + 1
        scenarios[c.scenario] = scenarios.get(c.scenario, 0) + 1
    reviewed = sum(1 for c in cases if c.status in ["Reviewed", "Escalated"])
    urgent = sum(1 for c in cases if c.risk == "Urgent review")
    return jsonify(
        total=len(cases), risks=risks, statuses=statuses, languages=languages, scenarios=scenarios,
        reviewed=reviewed, urgent=urgent, review_rate=round(reviewed / len(cases) * 100, 1) if cases else 0,
    )


@app.get("/api/diagnostics")
@require_login
def diagnostics():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    return jsonify(
        authenticated=True,
        app_version=APP_VERSION,
        gemini_configured=bool(key),
        gemini_model=GEMINI_MODEL,
        gemini_transcribe_model=GEMINI_TRANSCRIBE_MODEL,
        gemini_generate_api_version=GEMINI_GENERATE_API_VERSION,
        microphone_note="Microphone is browser-controlled and requires permission; localhost/127.0.0.1 or HTTPS is supported.",
        report_limit_mb=round(MAX_REPORT_BYTES / 1024 / 1024, 1),
        health_input_gate=HEALTH_INPUT_GATE,
        ai_circuits={k: {"blocked": bool(v.get("blocked")), "reason": v.get("reason", "")} for k, v in (session.get("ai_circuit", {}) or {}).items()},
    )


@app.post("/api/diagnostics/gemini")
@require_login
@limiter.limit("6 per minute")
def gemini_diagnostic():
    retry_token = request.form.get("_ai_retry_token", "").strip()
    request_id = request.form.get("_ai_request_id", "").strip()
    if not csrf_ok():
        return jsonify(ok=False, error="CSRF validation failed. Refresh the clinical workspace and try again."), 400
    payload_hash = ai_request_fingerprint("diagnostic", {"test": True})
    started, start_error, request_id, _attempt_no = ai_request_start("diagnostic", request_id, retry_token, payload_hash)
    if not started:
        return jsonify(ok=False, error=start_error, code="AI_REQUEST_DUPLICATE" if "already" in start_error.lower() else "AI_RETRY_INVALID", retryable=False), 409
    if not os.getenv("GEMINI_API_KEY", "").strip():
        ai_request_failed("diagnostic", "Gemini is not configured.")
        return jsonify(ok=False, ai_available=False, error="GEMINI_API_KEY is not configured.", detail="Add a valid Gemini API key to .env and restart the app.", retryable=ai_retry_allowed(), retry_token=ai_retry_token() if ai_retry_allowed() else ""), 200
    started = time.time()
    text, warning = gemini_text_generate(
        "Reply with exactly one short sentence: Swastya Assist AI connection test successful. Do not add any medical advice.", feature="diagnostic"
    )
    elapsed_ms = round((time.time() - started) * 1000)
    if text:
        ai_request_finish("diagnostic", "completed")
        audit("gemini_diagnostic_ok", metadata={"latency_ms": elapsed_ms})
        return jsonify(ok=True, ai_available=True, message=text.strip(), warning=warning or "", latency_ms=elapsed_ms)
    audit("gemini_diagnostic_unavailable", metadata={"latency_ms": elapsed_ms})
    return jsonify(ok=False, ai_available=False, error=warning or "Gemini is currently unavailable.", latency_ms=elapsed_ms), 200


@app.get("/api/ocr")
@require_login
def ocr_info():
    return jsonify(
        enabled=bool(os.getenv("GEMINI_API_KEY")),
        model=GEMINI_MODEL,
        transcribe_model=GEMINI_TRANSCRIBE_MODEL,
        voice_model=GEMINI_VOICE_MODEL,
        generate_content_api_version=GEMINI_GENERATE_API_VERSION,
        fallback_models=[],
        report_max_mb=round(MAX_REPORT_BYTES / 1024 / 1024, 1),
        local_pdf_text=True,
        local_image_ocr=False,
        disclaimer=DISCLAIMER,
    )


@app.route("/api/maintenance/retention", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def retention_cleanup():
    expected = os.getenv("CRON_SECRET", "").strip()
    supplied = request.headers.get("Authorization", "")
    if not expected or not secrets.compare_digest(supplied, f"Bearer {expected}"):
        return jsonify(error="Unauthorized"), 401
    cutoff = utcnow() - timedelta(days=RETENTION_DAYS)
    old_cases = Case.query.filter(Case.created_at < cutoff).all()
    count = 0
    for case in old_cases:
        audit("case_retention_deleted", metadata={"patient_ref": case.patient_ref, "retention_days": RETENTION_DAYS})
        delete_report_blob(case)
        db.session.delete(case)
        count += 1
    db.session.commit()
    return jsonify(ok=True, deleted_cases=count, retention_days=RETENTION_DAYS)


def migrate_sqlite_columns():
    if not str(app.config["SQLALCHEMY_DATABASE_URI"]).startswith("sqlite"):
        return
    insp = db.inspect(db.engine)
    if "case" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("case")}
    additions = {
        "patient_name": "ALTER TABLE case ADD COLUMN patient_name TEXT NOT NULL DEFAULT ''",
        "age": "ALTER TABLE case ADD COLUMN age INTEGER",
        "gender": "ALTER TABLE case ADD COLUMN gender VARCHAR(40) NOT NULL DEFAULT ''",
        "address": "ALTER TABLE case ADD COLUMN address TEXT NOT NULL DEFAULT ''",
        "consent": "ALTER TABLE case ADD COLUMN consent BOOLEAN NOT NULL DEFAULT 0",
        "report_filename": "ALTER TABLE case ADD COLUMN report_filename VARCHAR(255) NOT NULL DEFAULT ''",
        "report_mime": "ALTER TABLE case ADD COLUMN report_mime VARCHAR(120) NOT NULL DEFAULT ''",
        "report_data": "ALTER TABLE case ADD COLUMN report_data BLOB",
        "report_path": "ALTER TABLE case ADD COLUMN report_path VARCHAR(500) NOT NULL DEFAULT ''",
        "scenario": "ALTER TABLE case ADD COLUMN scenario VARCHAR(80) NOT NULL DEFAULT 'Outpatient queue triage'",
    }
    with db.engine.begin() as conn:
        for name, sql in additions.items():
            if name not in cols:
                conn.exec_driver_sql(sql)


def seed_demo_data():
    """Idempotent synthetic-only demo cases for judges and local demos."""
    samples = [
        {
            "patient_ref": "DEMO-001", "patient_name": "Asha Demo", "age": 34, "gender": "Female",
            "address": "Synthetic District Hospital", "language": "Hindi", "scenario": "Outpatient queue triage",
            "symptoms": "Fever for two days with headache and weakness.",
        },
        {
            "patient_ref": "DEMO-002", "patient_name": "Ravi Demo", "age": 52, "gender": "Male",
            "address": "Synthetic Industrial Estate Clinic", "language": "Bengali", "scenario": "Occupational health screening",
            "symptoms": "Severe difficulty breathing since this morning during work. No report attached.",
        },
        {
            "patient_ref": "DEMO-003", "patient_name": "Meera Demo", "age": 28, "gender": "Female",
            "address": "Synthetic Campus Health Center", "language": "Odia", "scenario": "Campus fever triage",
            "symptoms": "Mild fever and sore throat since yesterday.",
        },
    ]
    for item in samples:
        if Case.query.filter_by(patient_ref=item["patient_ref"]).first():
            continue
        note = fallback_note(item["symptoms"], "", item["language"])
        case = Case(
            id=uuid.uuid4().hex,
            patient_ref=item["patient_ref"], patient_name=item["patient_name"], age=item["age"], gender=item["gender"],
            address=item["address"], consent=True, language=item["language"], symptoms=item["symptoms"], report_text="",
            ai_note=note, risk=note["risk_category"], status="Needs review", source="Synthetic demo seed", scenario=item["scenario"],
        )
        db.session.add(case)
    db.session.commit()


with app.app_context():
    db.create_all()
    migrate_sqlite_columns()
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    existing_admin = User.query.filter_by(username=admin_username).first()
    if admin_password and not existing_admin:
        try:
            db.session.add(
                User(
                    id=uuid.uuid4().hex,
                    username=admin_username,
                    password_hash=generate_password_hash(admin_password),
                    role="admin",
                )
            )
            db.session.commit()
        except Exception:
            db.session.rollback()
            log.exception("Initial admin creation raced or failed")
    elif admin_password and existing_admin and LOCAL_RESET_ADMIN_PASSWORD and not RUNNING_ON_VERCEL:
        existing_admin.password_hash = generate_password_hash(admin_password)
        existing_admin.active = True
        existing_admin.role = "admin"
        db.session.commit()
        log.warning("LOCAL_RESET_ADMIN_PASSWORD=1 reset the local administrator password for %s", admin_username)
    if os.getenv("SEED_DEMO_DATA", "0") == "1":
        seed_demo_data()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
