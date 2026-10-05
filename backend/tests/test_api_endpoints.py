import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db, SessionLocal
from backend.app.models import UserModel, UserSessionModel

@pytest.fixture(scope="module")
def client():
    init_db()
    email = f"suite-{uuid4().hex}@example.test"
    with TestClient(app) as c:
        created = c.post("/api/auth/register", json={"full_name":"API Test User", "email":email, "password":"SuitePassword123", "confirm_password":"SuitePassword123"})
        assert created.status_code == 200
        try:
            yield c
        finally:
            c.delete("/api/cases/API-TEST-999")
            c.post("/api/auth/logout")
            db = SessionLocal()
            user = db.query(UserModel).filter(UserModel.email == email).first()
            if user:
                db.query(UserSessionModel).filter(UserSessionModel.user_id == user.id).delete(synchronize_session=False)
                db.delete(user)
                db.commit()
            db.close()

def test_authentication_lifecycle():
    email = f"auth-test-{uuid4().hex}@example.test"
    with TestClient(app) as c:
        assert c.get("/api/cases").status_code == 401
        payload = {"full_name":"Auth Test", "email":email, "password":"TestPassword123", "confirm_password":"TestPassword123"}
        assert c.post("/api/auth/register", json={**payload, "confirm_password":"Different123"}).status_code == 400
        registered = c.post("/api/auth/register", json=payload)
        assert registered.status_code == 200
        assert "password_hash" not in registered.text.lower()
        assert c.post("/api/auth/register", json=payload).status_code == 409
        assert c.post("/api/auth/login", json={"email":email, "password":"WrongPassword123"}).status_code == 401
        assert c.get("/api/cases").status_code == 200
        c.post("/api/auth/logout")
        assert c.get("/api/cases").status_code == 401
        assert c.post("/api/auth/login", json={"email":email, "password":payload["password"]}).status_code == 200
        assert c.get("/api/auth/me").status_code == 200
        c.post("/api/auth/logout")
        db = SessionLocal()
        user = db.query(UserModel).filter(UserModel.email == email).first()
        if user:
            db.query(UserSessionModel).filter(UserSessionModel.user_id == user.id).delete(synchronize_session=False)
            db.delete(user)
            db.commit()
        db.close()

def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_get_cases_and_templates(client):
    res = client.get("/api/cases/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 3
    
    res = client.get("/api/cases")
    assert res.status_code == 200
    cases = res.json()
    assert len(cases) >= 1

def test_create_case(client):
    # Ensure clean state
    client.delete("/api/cases/API-TEST-999")
    
    case_payload = {
        "id": "API-TEST-999",
        "title": "API Verification Incident",
        "description": "Testing case creation endpoint via FastAPI TestClient.",
        "category": "Verification"
    }
    res = client.post("/api/cases", json=case_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "API-TEST-999"
    assert data["status"] == "pending"

def test_investigate_and_poll_events(client):
    # Run sync investigation for quick test
    res = client.post("/api/cases/API-TEST-999/investigate?run_sync=true")
    assert res.status_code == 200
    
    # Poll workflow events
    res = client.get("/api/cases/API-TEST-999/workflow-events")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 5
    
    # Fetch state
    res = client.get("/api/cases/API-TEST-999/state")
    assert res.status_code == 200
    state = res.json()
    assert state["current_node"] == "reporter"

def test_report_and_human_review(client):
    # Fetch report
    res = client.get("/api/cases/API-TEST-999/report")
    assert res.status_code == 200
    report = res.json()
    assert report["case_id"] == "API-TEST-999"
    assert report["status"] == "awaiting_review"
    
    # Export report as markdown
    res = client.get("/api/cases/API-TEST-999/report?export_format=markdown")
    assert res.status_code == 200
    assert "text/markdown" in res.headers["content-type"]
    assert "# " in res.text
    
    # Submit human review
    review_payload = {
        "decision": "approved",
        "reviewer_name": "Chief Security Officer",
        "feedback": "Investigation verified. Findings are well-supported by evidence."
    }
    res = client.post("/api/cases/API-TEST-999/review", json=review_payload)
    assert res.status_code == 200
    rev = res.json()
    assert rev["decision"] == "approved"
    
    # Verify case status updated to completed
    res = client.get("/api/cases/API-TEST-999")
    assert res.status_code == 200
    assert res.json()["status"] == "completed"

def test_evidence_vault_search(client):
    res = client.get("/api/evidence?q=policy")
    assert res.status_code == 200
    records = res.json()
    assert len(records) > 0
    
    res = client.get("/api/evidence/source-types")
    assert res.status_code == 200
    types = res.json()
    assert "policy" in types
    assert "access_log" in types

def test_settings_endpoint(client):
    res = client.get("/api/settings")
    assert res.status_code == 200
    settings_data = res.json()
    assert "llm_provider" in settings_data
    assert "demo_mode_active" in settings_data
    # Ensure raw secret is not in response
    assert "OPENAI_API_KEY" not in settings_data
