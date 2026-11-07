"""Optional ARQ worker entry point: `arq app.worker.WorkerSettings`."""
from arq.connections import RedisSettings

from app.core.config import get_settings
from app.tasks import process_incoming_message_job


async def startup(ctx: dict) -> None:
    """ARQ lifecycle hook."""


class WorkerSettings:
    functions = [process_incoming_message_job]
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url or "redis://localhost:6379/0")
    on_startup = startup
