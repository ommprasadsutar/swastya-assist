import base64
import os
import tempfile
from pathlib import Path
import re

os.environ["SWASTYA_TEST_MODE"] = "1"
DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()
for key, value in {
    "DATABASE_URL": f"sqlite:///{DB_FILE.name}",
    "FLASK_SECRET_KEY": "test-secret-key-abcdefghijklmnopqrstuvwxyz",
    "ADMIN_USERNAME": "admin",
    "ADMIN_PASSWORD": "admin-password-12345",
    "SEED_DEMO_DATA": "0",
    "COOKIE_SECURE": "0",
    "GEMINI_API_KEY": "",
    "DEMO_ONLY_MODE": "1",
    "PRIVACY_GATE_ENABLED": "1",
}.items():
    os.environ[key] = value

import app as app_module  # noqa: E402
from app import app, db, User, Case  # noqa: E402


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def csrf(client):
    with client.session_transaction() as sess:
        return sess["csrf_token"]


def login_token(client):
    page = client.get("/login")
    assert page.status_code == 200
    match = re.search(rb'name="csrf_token"\s+value="([^"]+)"', page.data)
    assert match, "login page must render a CSRF token"
    return match.group(1).decode("utf-8")


def login(client):
    token = login_token(client)
    response = client.post(
        "/login",
        data={"csrf_token": token, "username": "admin", "password": "admin-password-12345", "role": "admin"},
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_health_ready():
    with app.test_client() as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 200


def test_auth_csrf_triage_and_media_privacy_gate_fails_closed(monkeypatch):
    with app.test_client() as client:
        assert client.get("/api/cases").status_code == 401
        client.get("/login")
        login(client)
        token = csrf(client)
        bad = client.post("/api/triage", data={"patient_name": "x"})
        assert bad.status_code == 400
        response = client.post(
            "/api/triage",
            data={
                "csrf_token": token,
                "patient_name": "Synthetic Test",
                "age": "42",
                "gender": "Female",
                "address": "Synthetic Facility",
                "language": "English",
                "scenario": "Outpatient queue triage",
                "symptoms": "Severe chest pain started today.",
                "consent": "on",
                "source": "Patient intake",
                "report_image": (tempfile.SpooledTemporaryFile(), "empty.png"),
            },
            content_type="multipart/form-data",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        # Empty upload must be rejected; this verifies strict upload validation.
        assert response.status_code == 415

        response = client.post(
            "/api/triage",
            data={
                "csrf_token": token,
                "patient_name": "Synthetic Test",
                "age": "42",
                "gender": "Female",
                "address": "Synthetic Facility",
                "language": "English",
                "scenario": "Outpatient queue triage",
                "symptoms": "Severe chest pain started today.",
                "consent": "on",
                "source": "Patient intake",
                "report_image": (tempfile.SpooledTemporaryFile(), ""),
            },
            content_type="multipart/form-data",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["note"]["risk_category"] == "Urgent review"

        # This deliberately unreadable 1x1 media must fail closed after the user
        # opts into external processing. No original media is forwarded or stored.
        # Make any unexpected external model call fail this test immediately.
        def forbidden_gemini_call(*_args, **_kwargs):
            raise AssertionError("Gemini must not be called when OCR redaction fails")
        monkeypatch.setattr(app_module, "gemini_generate", forbidden_gemini_call)
        count_before = Case.query.count()
        report_response = client.post(
            "/api/triage",
            data={
                "csrf_token": token,
                "patient_name": "Synthetic Report",
                "age": "33",
                "gender": "Male",
                "address": "Synthetic Facility",
                "language": "Hindi",
                "scenario": "Public health camp screening",
                "symptoms": "Fever and weakness.",
                "consent": "on",
                "source": "Gemini report/OCR",
                "external_ai_media_consent": "on",
                "report_image": (io_bytes(PNG_1X1), "sample.png"),
            },
            content_type="multipart/form-data",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert report_response.status_code == 422
        assert report_response.get_json()["code"] == "MEDIA_REDACTION_FAILED"
        assert Case.query.count() == count_before

        # The safe text-only intake still exists and can be reviewed normally.
        case_id = payload["id"]
        case = db.session.get(Case, case_id)
        assert case and not case.report_data
        review = client.post(
            f"/api/cases/{case_id}/review",
            data={"csrf_token": token, "status": "Reviewed", "reviewer_note": "Synthetic review completed.", "urgent_verified": "1"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert review.status_code == 200
        assert review.get_json()["case"]["status"] == "Reviewed"
        assert review.get_json()["case"]["reviewer_note"] == "Synthetic review completed."
        reloaded = client.get(f"/api/cases/{case_id}")
        assert reloaded.status_code == 200
        assert reloaded.get_json()["status"] == "Reviewed"
        assert reloaded.get_json()["reviewer_note"] == "Synthetic review completed."


def io_bytes(data):
    import io
    return io.BytesIO(data)


# Keep the ephemeral test DB out of the project and clean it after collection.
def teardown_module():
    try:
        Path(DB_FILE.name).unlink(missing_ok=True)
    except Exception:
        pass


def test_offline_sync_creates_needs_review_case_idempotently_without_ai(monkeypatch):
    import uuid

    client_id = "offline-test-" + uuid.uuid4().hex[:16]
    patient_ref = "OFFLINE-" + uuid.uuid4().hex[:10].upper()
    body = {
        "items": [{
            "client_id": client_id,
            "payload": {
                "patient_ref": patient_ref,
                "patient_name": "Synthetic Offline Patient",
                "age": 35,
                "gender": "Female",
                "language": "English",
                "address": "Synthetic Facility",
                "scenario": "Outpatient queue triage",
                "symptoms": "Fever and cough for two days.",
                "consent": True,
            },
        }]
    }
    def forbidden_gemini_call(*_args, **_kwargs):
        raise AssertionError("Offline synchronization must never call Gemini")
    monkeypatch.setattr(app_module, "gemini_generate", forbidden_gemini_call)

    with app.test_client() as client:
        unauthenticated = client.post("/api/offline-sync", json=body)
        assert unauthenticated.status_code == 401

        login(client)
        token = csrf(client)
        headers = {"X-CSRF-Token": token}
        first = client.post("/api/offline-sync", json=body, headers=headers)
        assert first.status_code == 200
        result = first.get_json()
        assert result["ai_called"] is False
        assert result["human_review_required"] is True
        synced = result["results"][0]
        assert synced["status"] == "synced"
        assert synced["duplicate"] is False

        case = db.session.get(Case, synced["case_id"])
        assert case is not None
        assert case.patient_ref == patient_ref
        assert case.status == "Needs review"
        assert case.processing_mode == "Offline sync"
        assert case.report_data is None
        assert "AI processing was not run" in case.ai_note["summary"]

        repeated = client.post("/api/offline-sync", json=body, headers=headers)
        assert repeated.status_code == 200
        duplicate = repeated.get_json()["results"][0]
        assert duplicate["status"] == "synced"
        assert duplicate["duplicate"] is True
        assert duplicate["case_id"] == synced["case_id"]
        assert Case.query.filter_by(patient_ref=patient_ref).count() == 1
