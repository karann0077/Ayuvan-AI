import asyncio

from arq import create_pool
from arq.connections import RedisSettings

from app.core.config import get_settings
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


async def dispatch_incoming_message(message_id: str) -> None:
    """Use ARQ when explicitly enabled; retain a zero-infrastructure local fallback."""
    settings = get_settings()
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
