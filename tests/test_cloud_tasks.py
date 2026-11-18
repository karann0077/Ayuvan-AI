import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import routes
from app.core.config import Settings, get_settings
from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models import Message
from app.db.session import get_db
from app.schemas import NormalizedIncomingMessage
from app.services.conversation import ConversationService, MessageProcessingInProgress
from app.tasks import _enqueue_cloud_task


def test_cloud_task_contains_only_message_id_and_authenticated_target(monkeypatch):
    class Client:
        def queue_path(self, project, location, queue):
            return f"projects/{project}/locations/{location}/queues/{queue}"

        def create_task(self, request):
            self.request = request

    client = Client()
    monkeypatch.setattr("app.tasks._cloud_tasks_client", lambda: client)
    settings = Settings(
        _env_file=None,
        cloud_tasks_project="test-project",
        cloud_tasks_location="asia-south1",
        cloud_tasks_queue="test-queue",
        cloud_tasks_target_url="https://example.run.app",
        cloud_tasks_invoker_service_account="tasks@example.iam.gserviceaccount.com",
    )
    _enqueue_cloud_task("00000000-0000-0000-0000-000000000001", settings)
    task = client.request.task
    assert task.http_request.url == "https://example.run.app/api/v1/tasks/whatsapp"
    assert task.http_request.body == b'{"message_id": "00000000-0000-0000-0000-000000000001"}'
    assert task.http_request.oidc_token.audience == "https://example.run.app"
    assert task.http_request.oidc_token.service_account_email == "tasks@example.iam.gserviceaccount.com"


def test_duplicate_webhook_can_requeue_unfinished_message():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    service = ConversationService(Settings(
        _env_file=None, allow_test_user_auto_provision=True, test_user_phone="919999999999",
        gemini_api_key=None,
    ))
    incoming = NormalizedIncomingMessage(
        provider_message_id="wamid.retry", sender="919999999999",
        message_type="text", content="A headache",
    )
    message_id = service.receive(db, incoming)
    assert service.receive(db, incoming) == message_id
    message = db.get(Message, message_id)
    message.processing_status = "processed"
    db.commit()
    assert service.receive(db, incoming) is None


def test_active_claim_is_retried_instead_of_acknowledged():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    message = Message(
        provider_message_id="wamid.busy", direction="incoming", message_type="text",
        processing_status="processing", updated_at=datetime.now(timezone.utc),
    )
    db.add(message)
    db.commit()
    service = ConversationService(Settings(_env_file=None, gemini_api_key=None))
    with pytest.raises(MessageProcessingInProgress):
        asyncio.run(service.process_message(db, message.id))


def test_failed_processing_remains_retryable():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()
    message = Message(
        provider_message_id="wamid.invalid", direction="incoming", message_type="text",
        processing_status="received", conversation_id="00000000-0000-0000-0000-000000000002",
        patient_id="00000000-0000-0000-0000-000000000003",
    )
    db.add(message)
    db.commit()
    service = ConversationService(Settings(_env_file=None, gemini_api_key=None))
    with pytest.raises(ValueError, match="no conversation or patient"):
        asyncio.run(service.process_message(db, message.id))
    assert db.get(Message, message.id).processing_status == "failed"
    with pytest.raises(ValueError, match="no conversation or patient"):
        asyncio.run(service.process_message(db, message.id))


def test_task_endpoint_rejects_missing_identity_and_processes_verified_task(monkeypatch):
    settings = Settings(
        _env_file=None, use_cloud_tasks=True,
        cloud_tasks_target_url="https://example.run.app",
        cloud_tasks_queue="test-queue",
        cloud_tasks_invoker_service_account="tasks@example.iam.gserviceaccount.com",
    )
    app = FastAPI()
    app.include_router(routes.router, prefix="/api/v1")
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_db] = lambda: iter([object()])
    processed = []

    async def fake_process(self, db, message_id):
        processed.append(message_id)

    monkeypatch.setattr(ConversationService, "process_message", fake_process)
    monkeypatch.setattr(routes, "verify_cloud_task_identity", lambda *args: True)
    client = TestClient(app)
    url = "/api/v1/tasks/whatsapp"
    body = {"message_id": "00000000-0000-0000-0000-000000000001"}
    assert client.post(url, json=body, headers={"X-CloudTasks-QueueName": "test-queue"}).status_code == 401
    assert client.post(url, json=body, headers={"X-CloudTasks-QueueName": "wrong"}).status_code == 403
    monkeypatch.setattr(routes, "verify_cloud_task_identity", lambda *args: False)
    assert client.post(url, json=body, headers={
        "X-CloudTasks-QueueName": "test-queue", "Authorization": "Bearer test-token",
    }).status_code == 403
    monkeypatch.setattr(routes, "verify_cloud_task_identity", lambda *args: True)
    response = client.post(url, json=body, headers={
        "X-CloudTasks-QueueName": "test-queue", "Authorization": "Bearer test-token",
    })
    assert response.status_code == 200
    assert processed == [body["message_id"]]
