import asyncio
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.base import Base
import app.db.models  # noqa: F401
from app.db.models import Conversation, HealthEpisode, Message
from app.schemas import NormalizedIncomingMessage
from app.services.conversation import ConversationService


def test_old_cough_requires_continuity_confirmation_before_reusing_episode(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    service = ConversationService(Settings(
        allow_test_user_auto_provision=True, test_user_phone="919999999999", gemini_api_key=None,
    ))
    sent: list[str] = []

    async def no_send(*args, **kwargs):
        sent.append(args[1])
        return None

    monkeypatch.setattr(service.whatsapp, "send_text", no_send)
    monkeypatch.setattr(service.whatsapp, "send_buttons", no_send)
    monkeypatch.setattr(service.whatsapp, "send_list", no_send)
    first = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="cough.first", sender="919999999999", message_type="text",
        content="I have a cough",
    ))
    asyncio.run(service.process_message(session, first))
    old = session.query(HealthEpisode).one()
    old.last_reported_at -= timedelta(days=15)
    old.created_at -= timedelta(days=15)
    session.commit()

    second = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="cough.second", sender="919999999999", message_type="text",
        content="I am still coughing",
    ))
    asyncio.run(service.process_message(session, second))
    assert session.query(HealthEpisode).count() == 1
    assert session.query(Conversation).one().state["pending_continuity"]["episode_id"] == old.id

    answer = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="cough.third", sender="919999999999", message_type="interactive",
        content="Went away, returned", metadata={"reply_id": "RETURNED"},
    ))
    asyncio.run(service.process_message(session, answer))
    assert session.query(HealthEpisode).count() == 2
    assert session.query(HealthEpisode).filter_by(id=old.id).one().status == "resolved"
    current = session.query(HealthEpisode).filter_by(status="active").one()
    assert current.summary["continuity"] == "returned_after_resolution"
    assert service.review.assess(current, service.context_builder.build(
        session, current.patient_id, "cough"
    )).evidence["reported_duration_days"] is None

    current.last_reported_at -= timedelta(days=15)
    current.created_at -= timedelta(days=15)
    session.commit()
    later = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="cough.fourth", sender="919999999999", message_type="text",
        content="I am still coughing",
    ))
    asyncio.run(service.process_message(session, later))
    assert session.query(Conversation).one().state["pending_continuity"]
    continued = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="cough.fifth", sender="919999999999", message_type="interactive",
        content="Continued", metadata={"reply_id": "CONTINUED"},
    ))
    asyncio.run(service.process_message(session, continued))
    assert session.query(HealthEpisode).count() == 2
    assert service.review.assess(current, service.context_builder.build(
        session, current.patient_id, "cough"
    )).priority == "P2"


def test_guided_headache_intake_collects_change_and_impact_before_closing(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    settings = Settings(
        allow_test_user_auto_provision=True,
        test_user_phone="919999999999",
        gemini_api_key=None,
    )
    service = ConversationService(settings)

    sent: list[tuple[str, tuple, dict]] = []

    async def no_send(*args, **kwargs):
        sent.append(("text", args, kwargs))
        return None

    async def no_send_buttons(*args, **kwargs):
        sent.append(("buttons", args, kwargs))
        return None

    async def no_send_list(*args, **kwargs):
        sent.append(("list", args, kwargs))
        return None

    monkeypatch.setattr(service.whatsapp, "send_text", no_send)
    monkeypatch.setattr(service.whatsapp, "send_buttons", no_send_buttons)
    monkeypatch.setattr(service.whatsapp, "send_list", no_send_list)
    first = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.first", sender="919999999999", message_type="text",
        content="I have a headache for five days",
    ))
    assert first
    asyncio.run(service.process_message(session, first))
    episode = session.query(HealthEpisode).one()
    assert episode.normalized_symptom == "headache"
    assert session.query(Conversation).one().state["pending_question"]["field"] == "headache_warning_signs"
    assert sent[-1][0] == "list"

    second = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.second", sender="919999999999", message_type="interactive",
        content="No warning signs", metadata={"reply_id": "HEADACHE_SCREEN_NONE"},
    ))
    asyncio.run(service.process_message(session, second))
    assert session.query(HealthEpisode).one().summary["headache_warning_signs"] == "No warning signs"
    assert session.query(Conversation).one().state["pending_question"]["field"] == "severity"
    assert sent[-1][0] == "buttons"

    reply = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.third", sender="919999999999", message_type="interactive", content="Moderate",
        metadata={"reply_id": "SEVERITY_MODERATE"},
    ))
    asyncio.run(service.process_message(session, reply))
    assert session.query(HealthEpisode).one().summary["severity"] == "Moderate"
    assert session.query(Conversation).one().state["pending_question"]["field"] == "progression"

    fourth = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.fourth", sender="919999999999", message_type="interactive", content="About the same",
        metadata={"reply_id": "PROGRESSION_SAME"},
    ))
    asyncio.run(service.process_message(session, fourth))
    assert session.query(Conversation).one().state["pending_question"]["field"] == "functional_impact"

    fifth = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.fifth", sender="919999999999", message_type="interactive", content="Yes, mostly",
        metadata={"reply_id": "IMPACT_NORMAL"},
    ))
    asyncio.run(service.process_message(session, fifth))
    assert session.query(Conversation).one().state["pending_question"] is None
    assert session.query(Message).filter_by(provider_message_id="wamid.fifth").one().processing_status == "processed"
    assert sent[-1][0] == "text"
    assert "*Recorded*" in sent[-1][1][1]
    assert "clinician appointment soon" in sent[-1][1][1]

    # Meta retries must not create another record or health event.
    assert service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.fifth", sender="919999999999", message_type="interactive", content="Yes, mostly",
    )) is None


def test_headache_warning_selection_escalates_without_followup(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    settings = Settings(allow_test_user_auto_provision=True, test_user_phone="919999999999", gemini_api_key=None)
    service = ConversationService(settings)
    sent: list[str] = []

    async def text_send(*args, **kwargs):
        sent.append(args[1])
        return None

    async def interactive_send(*args, **kwargs):
        return None

    monkeypatch.setattr(service.whatsapp, "send_text", text_send)
    monkeypatch.setattr(service.whatsapp, "send_list", interactive_send)
    monkeypatch.setattr(service.whatsapp, "send_buttons", interactive_send)
    first = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.warning.first", sender="919999999999", message_type="text", content="I have a headache",
    ))
    asyncio.run(service.process_message(session, first))
    response = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.warning.second", sender="919999999999", message_type="interactive",
        content="Vision change / loss", metadata={"reply_id": "HEADACHE_SCREEN_VISION"},
    ))
    asyncio.run(service.process_message(session, response))
    assert any("urgent in-person assessment" in message for message in sent)
    assert session.query(Conversation).one().state["pending_question"] is None


def test_new_concern_interrupts_an_old_free_text_question(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    settings = Settings(allow_test_user_auto_provision=True, test_user_phone="919999999999", gemini_api_key=None)
    service = ConversationService(settings)

    async def no_send(*args, **kwargs):
        return None

    monkeypatch.setattr(service.whatsapp, "send_text", no_send)
    monkeypatch.setattr(service.whatsapp, "send_buttons", no_send)
    monkeypatch.setattr(service.whatsapp, "send_list", no_send)
    first = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.interrupt.first", sender="919999999999", message_type="text", content="I have a headache",
    ))
    asyncio.run(service.process_message(session, first))
    conversation = session.query(Conversation).one()
    conversation.state = {"pending_question": {"episode_id": conversation.active_episode_id, "field": "associated_symptoms", "options": {}}}
    session.commit()

    interrupt = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.interrupt.second", sender="919999999999", message_type="text", content="I have a fever for two days",
    ))
    asyncio.run(service.process_message(session, interrupt))
    episode = session.query(HealthEpisode).filter_by(normalized_symptom="fever").one()
    assert episode.summary["duration"] == "two days"
    assert session.query(Conversation).one().state["pending_question"]["field"] == "severity"


def test_flow_opens_after_headache_safety_screen_and_normalises_submitted_answers(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    settings = Settings(
        allow_test_user_auto_provision=True,
        test_user_phone="919999999999",
        whatsapp_symptom_intake_flow_id="flow-1",
        gemini_api_key=None,
    )
    service = ConversationService(settings)
    sent: list[str] = []

    async def no_send(*args, **kwargs):
        return None

    async def flow_send(*args, **kwargs):
        sent.append("flow")
        return None

    monkeypatch.setattr(service.whatsapp, "send_text", no_send)
    monkeypatch.setattr(service.whatsapp, "send_buttons", no_send)
    monkeypatch.setattr(service.whatsapp, "send_list", no_send)
    monkeypatch.setattr(service.whatsapp, "send_flow", flow_send)
    first = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.flow.first", sender="919999999999", message_type="text", content="I have a headache",
    ))
    asyncio.run(service.process_message(session, first))
    assert session.query(Conversation).one().state["pending_question"]["field"] == "headache_warning_signs"

    safety = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.flow.safety", sender="919999999999", message_type="interactive",
        content="No warning signs", metadata={"reply_id": "HEADACHE_SCREEN_NONE"},
    ))
    asyncio.run(service.process_message(session, safety))
    assert sent == ["flow"]
    assert session.query(Conversation).one().state["pending_flow"]

    submission = service.receive(session, NormalizedIncomingMessage(
        provider_message_id="wamid.flow.submit", sender="919999999999", message_type="interactive",
        content="Sent", metadata={"reply_type": "flow", "response_json": '{"severity":"moderate","progression":"getting_worse","functional_impact":"mostly_manageable"}'},
    ))
    asyncio.run(service.process_message(session, submission))
    episode = session.query(HealthEpisode).one()
    assert episode.summary["severity"] == "Moderate"
    assert episode.summary["progression"] == "Getting worse"
