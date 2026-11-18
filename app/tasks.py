import asyncio
import json
from functools import lru_cache

from arq import create_pool
from arq.connections import RedisSettings
from google.cloud import tasks_v2

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.services.conversation import ConversationService


async def process_incoming_message(message_id: str) -> None:
    """Development-safe task runner. Production can dispatch the same function through ARQ."""
    db = SessionLocal()
    try:
        await ConversationService().process_message(db, message_id)
    finally:
        db.close()


async def process_incoming_message_job(_: dict, message_id: str) -> None:
    """ARQ-compatible durable worker entry point."""
    await process_incoming_message(message_id)


@lru_cache(maxsize=1)
def _cloud_tasks_client() -> tasks_v2.CloudTasksClient:
    return tasks_v2.CloudTasksClient()


def _enqueue_cloud_task(message_id: str, settings: Settings) -> None:
    if not all((
        settings.cloud_tasks_project, settings.cloud_tasks_location,
        settings.cloud_tasks_queue, settings.cloud_tasks_target_url,
        settings.cloud_tasks_invoker_service_account,
    )):
        raise RuntimeError("Cloud Tasks is enabled but its deployment settings are incomplete")
    client = _cloud_tasks_client()
    base_url = settings.cloud_tasks_target_url.rstrip("/")
    request = tasks_v2.CreateTaskRequest(
        parent=client.queue_path(
            settings.cloud_tasks_project, settings.cloud_tasks_location, settings.cloud_tasks_queue
        ),
        task=tasks_v2.Task(http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=f"{base_url}{settings.api_prefix}/tasks/whatsapp",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"message_id": message_id}).encode("utf-8"),
            oidc_token=tasks_v2.OidcToken(
                service_account_email=settings.cloud_tasks_invoker_service_account,
                audience=base_url,
            ),
        )),
    )
    client.create_task(request=request)


async def dispatch_incoming_message(message_id: str, settings: Settings | None = None) -> None:
    """Enqueue durably on Cloud Run; keep ARQ/local behavior for development."""
    settings = settings or get_settings()
    if settings.use_cloud_tasks:
        await asyncio.to_thread(_enqueue_cloud_task, message_id, settings)
        return
    if not settings.use_arq:
        await process_incoming_message(message_id)
        return
    if not settings.redis_url:
        raise RuntimeError("USE_ARQ=true requires REDIS_URL")
    pool = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    try:
        await pool.enqueue_job("process_incoming_message_job", message_id)
    finally:
        await pool.aclose()
