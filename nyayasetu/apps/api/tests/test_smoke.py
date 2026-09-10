"""
Minimal smoke test. Requires a running Postgres reachable at DATABASE_URL
(e.g. `docker compose up db -d` first). Run with: pytest tests/test_smoke.py
"""
import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def _signup_and_get_token() -> str:
    email = f"smoke-{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/auth/signup", json={"email": email, "password": "correct-horse-battery"})
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def test_signup_and_login():
    token = _signup_and_get_token()
    assert token

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert "@" in me.json()["email"]


def test_create_and_analyze_text_case():
    token = _signup_and_get_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = client.post(
        "/api/cases",
        headers=headers,
        json={
            "domain": "rental_tenancy",
            "input_type": "text",
            "text_input": (
                "This is a notice to vacate the rented premises. You must respond in writing "
                "within 15 days of receipt. The security deposit will be subject to deductions "
                "for damages and wear and tear."
            ),
            "consent": True,
        },
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    analyze_resp = client.post(f"/api/cases/{case_id}/analyze", headers=headers)
    assert analyze_resp.status_code == 200

    status_resp = client.get(f"/api/cases/{case_id}/status", headers=headers)
    assert status_resp.json()["status"] in ("extracting", "analyzing", "ready", "failed")


def test_cases_require_auth():
    resp = client.get("/api/cases")
    assert resp.status_code == 401
