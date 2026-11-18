from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.models import ExternalIdentity, PatientProfile, User
from app.db.session import get_db
from app.main import create_app


def client_with_database(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_db():
        with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr("app.api.mobile.get_settings", lambda: Settings(gemini_api_key=None))
    return TestClient(app)


def register(client, phone, name):
    response = client.post("/api/v1/mobile/auth/register", json={
        "phone": phone, "password": "secure-pass-123", "name": name,
        "terms_accepted": True, "health_processing_consent": True,
        "ai_assistance_consent": True,
    })
    assert response.status_code == 201, response.text
    data = response.json()
    return {"Authorization": "Bearer " + data["access_token"]}, data["patient"]["id"]


def test_registration_patient_isolation_and_session_lifecycle(monkeypatch):
    client = client_with_database(monkeypatch)
    alice_headers, alice_id = register(client, "9876543210", "Alice")
    bob_headers, bob_id = register(client, "9876543211", "Bob")
    assert client.get(f"/api/v1/mobile/patients/{alice_id}/health", headers=bob_headers).status_code == 404
    assert client.post(f"/api/v1/mobile/patients/{alice_id}/health-items/conditions",
                       headers=alice_headers, json={"name": "Asthma"}).status_code == 201
    assert client.get(f"/api/v1/mobile/patients/{alice_id}/health", headers=alice_headers).json()["conditions"][0]["name"] == "Asthma"
    record_id = client.get(f"/api/v1/mobile/patients/{alice_id}/health", headers=alice_headers).json()["conditions"][0]["id"]
    assert client.patch(f"/api/v1/mobile/patients/{alice_id}/health-items/conditions/{record_id}",
                        headers=alice_headers, json={"name": "Updated history"}).status_code == 200
    assert client.get("/api/v1/mobile/export", headers=alice_headers).json()["patients"][0]["conditions"][0]["name"] == "Updated history"
    assert client.get(f"/api/v1/mobile/patients/{bob_id}/health", headers=bob_headers).json()["conditions"] == []
    assert client.post("/api/v1/mobile/auth/logout", headers=alice_headers).status_code == 200
    assert client.get("/api/v1/mobile/me", headers=alice_headers).status_code == 401
    login = client.post("/api/v1/mobile/auth/login", json={"phone": "9876543210", "password": "secure-pass-123"})
    assert login.status_code == 200
    assert login.json()["patients"][0]["id"] == alice_id


def test_chat_reuses_clinical_engine_and_tasks_are_real(monkeypatch):
    client = client_with_database(monkeypatch)
    headers, patient_id = register(client, "9876543220", "Test Patient")
    sent = client.post(f"/api/v1/mobile/patients/{patient_id}/chat/messages", headers=headers,
                       json={"text": "I have a headache for five days", "client_message_id": "message-12345"})
    assert sent.status_code == 200, sent.text
    assert len(sent.json()["messages"]) >= 2
    assert len(client.get(f"/api/v1/mobile/patients/{patient_id}/health", headers=headers).json()["episodes"]) == 1
    repeated = client.post(f"/api/v1/mobile/patients/{patient_id}/chat/messages", headers=headers,
                           json={"text": "I have a headache for five days", "client_message_id": "message-12345"})
    assert repeated.status_code == 200
    assert len(repeated.json()["messages"]) == len(sent.json()["messages"])
    task = client.post(f"/api/v1/mobile/patients/{patient_id}/care-tasks", headers=headers,
                       json={"description": "Book a consultation"})
    assert task.status_code == 201, task.text
    updated = client.patch(f"/api/v1/mobile/patients/{patient_id}/care-tasks/{task.json()['id']}",
                           headers=headers, json={"status": "completed"})
    assert updated.status_code == 200
    assert client.get(f"/api/v1/mobile/patients/{patient_id}/care-tasks", headers=headers).json()["tasks"][0]["status"] == "completed"
    edited = client.patch(f"/api/v1/mobile/patients/{patient_id}/care-tasks/{task.json()['id']}",
                          headers=headers, json={"description": "Book follow-up", "due_at": "2026-12-01T09:00:00+05:30"})
    assert edited.status_code == 200, edited.text
    assert edited.json()["description"] == "Book follow-up"
    assert client.post(f"/api/v1/mobile/patients/{patient_id}/consents", headers=headers,
                       json={"purpose": "ai_assistance", "granted": False}).status_code == 200
    blocked = client.post(f"/api/v1/mobile/patients/{patient_id}/chat/messages", headers=headers,
                          json={"text": "New headache", "client_message_id": "message-54321"})
    assert blocked.status_code == 403
    assert client.delete(f"/api/v1/mobile/patients/{patient_id}/care-tasks/{task.json()['id']}",
                         headers=headers).status_code == 200


def test_account_deletion_removes_family_and_blocks_old_session(monkeypatch):
    client = client_with_database(monkeypatch)
    headers, patient_id = register(client, "9876543230", "Parent")
    assert client.post("/api/v1/mobile/patients", headers=headers,
                       json={"name": "Child", "relationship": "child"}).status_code == 422
    family = client.post("/api/v1/mobile/patients", headers=headers,
                         json={"name": "Child", "relationship": "child", "authorized_caregiver": True})
    assert family.status_code == 201, family.text
    deleted = client.post("/api/v1/mobile/auth/delete", headers=headers,
                          json={"password": "secure-pass-123"})
    assert deleted.status_code == 200, deleted.text
    assert client.get("/api/v1/mobile/me", headers=headers).status_code == 401
    assert client.post("/api/v1/mobile/auth/login", json={
        "phone": "9876543230", "password": "secure-pass-123"}).status_code == 401


def test_whatsapp_history_requires_code_before_account_can_read_it(monkeypatch):
    client = client_with_database(monkeypatch)
    headers, _ = register(client, "9876543240", "Mobile account")
    db_generator = client.app.dependency_overrides[get_db]()
    db = next(db_generator)
    whatsapp_user = User()
    db.add(whatsapp_user)
    db.flush()
    whatsapp_patient = PatientProfile(user_id=whatsapp_user.id)
    db.add(whatsapp_patient)
    db.add(ExternalIdentity(user_id=whatsapp_user.id, provider="whatsapp",
                            external_id="919876543240", is_active=True))
    db.commit()
    whatsapp_patient_id = whatsapp_patient.id
    db_generator.close()
    assert client.get(f"/api/v1/mobile/patients/{whatsapp_patient_id}/health", headers=headers).status_code == 404

    sent = []
    async def fake_send(self, to, text):
        sent.append(text)
        return "provider-id"
    monkeypatch.setattr("app.api.mobile.WhatsAppClient.send_text", fake_send)
    requested = client.post("/api/v1/mobile/whatsapp-link/request", headers=headers)
    assert requested.status_code == 200, requested.text
    assert client.post("/api/v1/mobile/whatsapp-link/verify", headers=headers,
                       json={"code": "000000"}).status_code == 400
    code = sent[0].split("code: ")[1][:6]
    verified = client.post("/api/v1/mobile/whatsapp-link/verify", headers=headers,
                           json={"code": code})
    assert verified.status_code == 200, verified.text
    assert verified.json()["patients"][0]["id"] == whatsapp_patient_id
    assert client.get(f"/api/v1/mobile/patients/{whatsapp_patient_id}/health", headers=headers).status_code == 200


def test_document_facts_remain_draft_until_patient_review(monkeypatch):
    client = client_with_database(monkeypatch)
    headers, patient_id = register(client, "9876543250", "Document Patient")
    stored = {}
    class Blob:
        def __init__(self, key): self.key = key
        def upload_from_string(self, data, **kwargs): stored[self.key] = data
        def download_as_bytes(self): return stored[self.key]
        def delete(self, **kwargs): stored.pop(self.key, None)
    class Bucket:
        def blob(self, key): return Blob(key)
    monkeypatch.setattr("app.api.mobile._documents_bucket", lambda: Bucket())
    uploaded = client.post(f"/api/v1/mobile/patients/{patient_id}/documents", headers=headers,
                           files={"file": ("prescription.pdf", b"%PDF-1.4\nexample", "application/pdf")})
    assert uploaded.status_code == 201, uploaded.text
    document_id = uploaded.json()["id"]
    assert client.get(f"/api/v1/mobile/patients/{patient_id}/health", headers=headers).json()["medications"] == []
    assert client.get(f"/api/v1/mobile/patients/{patient_id}/documents/{document_id}/download",
                      headers=headers).content == b"%PDF-1.4\nexample"

    class FakeResponse:
        def raise_for_status(self): pass
        def json(self): return {"candidates": [{"content": {"parts": [{"text":
            '{"title":"Prescription","notes":"","conditions":[],"medications":["Medicine A"],"allergies":[]}'}]}}]}
    class FakeClient:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, *args, **kwargs): return FakeResponse()
    monkeypatch.setattr("app.api.mobile.httpx.AsyncClient", FakeClient)
    monkeypatch.setattr("app.api.mobile.get_settings", lambda: Settings(gemini_api_key="fake"))
    extracted = client.post(f"/api/v1/mobile/patients/{patient_id}/documents/{document_id}/extract",
                            headers=headers)
    assert extracted.status_code == 200, extracted.text
    assert client.get(f"/api/v1/mobile/patients/{patient_id}/health", headers=headers).json()["medications"] == []
    rejected_fact = client.post(f"/api/v1/mobile/patients/{patient_id}/documents/{document_id}/review",
                                headers=headers, json={"accepted": True, "medications": ["Invented medicine"]})
    assert rejected_fact.status_code == 422
    reviewed = client.post(f"/api/v1/mobile/patients/{patient_id}/documents/{document_id}/review",
                           headers=headers, json={"accepted": True, "medications": ["Medicine A"]})
    assert reviewed.status_code == 200, reviewed.text
    assert client.get(f"/api/v1/mobile/patients/{patient_id}/health", headers=headers).json()["medications"][0]["name"] == "Medicine A"
    assert client.post(f"/api/v1/mobile/patients/{patient_id}/documents/{document_id}/extract",
                       headers=headers).status_code == 409
    assert client.delete(f"/api/v1/mobile/patients/{patient_id}/documents/{document_id}",
                         headers=headers).status_code == 200
    assert client.get(f"/api/v1/mobile/patients/{patient_id}/documents", headers=headers).json()["documents"] == []
    assert client.get(f"/api/v1/mobile/patients/{patient_id}/health", headers=headers).json()["medications"][0]["name"] == "Medicine A"


def test_password_change_revokes_other_sessions(monkeypatch):
    client = client_with_database(monkeypatch)
    first, _ = register(client, "9876543260", "Security Patient")
    second_login = client.post("/api/v1/mobile/auth/login", json={
        "phone": "9876543260", "password": "secure-pass-123"})
    second = {"Authorization": "Bearer " + second_login.json()["access_token"]}
    changed = client.post("/api/v1/mobile/auth/change-password", headers=first, json={
        "current_password": "secure-pass-123", "new_password": "new-secure-pass-456"})
    assert changed.status_code == 200, changed.text
    assert client.get("/api/v1/mobile/me", headers=first).status_code == 200
    assert client.get("/api/v1/mobile/me", headers=second).status_code == 401
    assert client.post("/api/v1/mobile/auth/login", json={
        "phone": "9876543260", "password": "secure-pass-123"}).status_code == 401
    assert client.post("/api/v1/mobile/auth/login", json={
        "phone": "9876543260", "password": "new-secure-pass-456"}).status_code == 200
