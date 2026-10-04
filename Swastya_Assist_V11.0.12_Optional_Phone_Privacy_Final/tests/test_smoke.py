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
}.items():
    os.environ[key] = value

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


def test_auth_csrf_and_triage_report_roundtrip():
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
                "report_image": (io_bytes(PNG_1X1), "sample.png"),
            },
            content_type="multipart/form-data",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert report_response.status_code == 200
        case_id = report_response.get_json()["id"]
        case = db.session.get(Case, case_id)
        assert case and case.report_data
        opened = client.get(f"/api/cases/{case_id}/report")
        assert opened.status_code == 200
        assert opened.data == PNG_1X1

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
