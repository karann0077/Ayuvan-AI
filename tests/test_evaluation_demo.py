"""The evaluation set stays synthetic, private, and usable through the app API."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import ExternalIdentity
from app.db.session import get_db
from app.main import create_app
from scripts.seed_evaluation_demo import DEMO_PHONE, seed_demo


def test_three_isolated_demo_profiles_and_document(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        ids = seed_demo(db, datetime(2026, 11, 20, 6, 0, tzinfo=timezone.utc), "demo-secret-pass")
        db.commit()
        assert db.query(ExternalIdentity).filter_by(provider="whatsapp").count() == 0
        assert db.query(ExternalIdentity).filter_by(provider="demo").count() == 1
        try:
            seed_demo(db, datetime.now(timezone.utc), "another-password")
            assert False, "seed must refuse duplicates"
        except ValueError:
            db.rollback()

    app = create_app()
    def override_db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    login = client.post("/api/v1/mobile/auth/login", json={"phone": DEMO_PHONE, "password": "demo-secret-pass"})
    assert login.status_code == 200, login.text
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert len(login.json()["patients"]) == 3
    urgent = ids["urgent_patient_id"]
    routine = ids["routine_patient_id"]
    care = ids["care_patient_id"]
    assert client.get(f"/api/v1/mobile/patients/{urgent}/care-navigation", headers=headers).json()["action"] == "emergency"
    assert client.get(f"/api/v1/mobile/patients/{routine}/care-navigation", headers=headers).json()["action"] == "none"
    urgent_health = client.get(f"/api/v1/mobile/patients/{urgent}/health", headers=headers).json()
    assert len(urgent_health["episodes"][0]["events"]) == 4
    assert len(client.get(f"/api/v1/mobile/patients/{routine}/chat", headers=headers).json()["messages"]) == 5
    tasks = client.get(f"/api/v1/mobile/patients/{care}/care-tasks", headers=headers).json()["tasks"]
    assert len(tasks) == 3
    assert any("Follow-up" in task["description"] for task in tasks)
    docs = client.get(f"/api/v1/mobile/patients/{care}/documents", headers=headers).json()["documents"]
    assert len(docs) == 1
    document = client.get(f"/api/v1/mobile/patients/{care}/documents/{docs[0]['id']}/download", headers=headers)
    assert document.status_code == 200
    assert document.content.startswith(b"%PDF-")
    assert client.get(f"/api/v1/mobile/patients/{urgent}/documents/{docs[0]['id']}/download", headers=headers).status_code == 404
