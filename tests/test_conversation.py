import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models import Conversation, HealthEpisode, Message
from app.schemas import NormalizedIncomingMessage
from app.services.conversation import ConversationService


def test_persists_episode_and_interactive_followup(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    settings = Settings(
        allow_test_user_auto_provision=True,
        test_user_phone="919999999999",
        gemini_api_key=None,
    )
    service = ConversationService(settings)

    async def no_send(*args, **kwargs):
        return None

    monkeypatch.setattr(service.whatsapp, "send_text", no_send)
    monkeypatch.setattr(service.whatsapp, "send_buttons", no_send)
    first = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.first", sender="919999999999", message_type="text",
        content="I have a headache for five days",
    ))
    assert first
    asyncio.run(service.process_message(session, first))
    episode = session.query(HealthEpisode).one()
    assert episode.normalized_symptom == "headache"
    assert session.query(Conversation).one().state["pending_question"]["field"] == "onset"

    second = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.second", sender="919999999999", message_type="text", content="Five days ago",
    ))
    asyncio.run(service.process_message(session, second))
    assert session.query(HealthEpisode).one().summary["onset"] == "Five days ago"
    assert session.query(Conversation).one().state["pending_question"]["field"] == "frequency"

    reply = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.third", sender="919999999999", message_type="interactive",
        content="Continuously", metadata={"reply_id": "FREQUENCY_CONTINUOUS"},
    ))
    asyncio.run(service.process_message(session, reply))
    assert session.query(HealthEpisode).one().summary["frequency"] == "Continuously"
    assert session.query(Message).filter_by(provider_message_id="wamid.third").one().processing_status == "processed"

    # Meta retries must not create another record or health event.
    assert service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.third", sender="919999999999", message_type="interactive", content="Continuously",
    )) is None
