"""Read-only bridge from AYUVAN records to the draft pathway simulator.

This adapter is for developer comparison only. It never sends a WhatsApp reply,
persists a disposition, or promotes extracted text to a confirmed clinical fact.
"""

from datetime import date, datetime, time, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinical.engine import assess
from app.clinical.loader import registry
from app.clinical.router import CONCEPTS
from app.clinical.types import AssessmentInput, AssessmentOutput, Episode, Fact, Population
from app.db.models import HealthEpisode, PatientProfile, SymptomEvent


def _utc(value: datetime) -> datetime:
    # AYUVAN stores UTC timestamps; SQLite may return them without tzinfo.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _age_on(birth_date: date | None, today: date) -> int | None:
    if birth_date is None or birth_date > today:
        return None
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def simulate_patient_episode(
    db: Session, patient_id: str, episode_id: str, *, pregnant: bool | None = None,
    as_of: datetime | None = None,
) -> AssessmentOutput:
    """Build a conservative structured simulation from an owned episode.

    Only exact concept codes are routed. The existing chat extractor and free-text
    summaries do not establish negated warning signs, onset, or pregnancy status.
    Those inputs remain unknown unless a later reviewed adapter supplies them.
    """
    patient = db.get(PatientProfile, patient_id)
    episode = db.get(HealthEpisode, episode_id)
    if patient is None or episode is None or episode.patient_id != patient_id:
        raise ValueError("Patient episode not found")

    now = _utc(as_of or datetime.now(timezone.utc))
    raw_code = (episode.normalized_symptom or "").strip().lower().replace(" ", "_")
    code = raw_code if raw_code in CONCEPTS else "unmapped_symptom"
    facts: list[Fact] = []
    events = db.scalars(select(SymptomEvent).where(SymptomEvent.episode_id == episode.id)
                        .order_by(SymptomEvent.recorded_at)).all()
    for event in events:
        event_code = (event.normalized_symptom or "").strip().lower().replace(" ", "_")
        if event_code == code and code in CONCEPTS and event.recorded_at:
            facts.append(Fact(
                code=code, state="present", observed_at=_utc(event.recorded_at),
                source_type="extracted", source_id=f"symptom_event:{event.id}",
                verification="unverified",
            ))

    def episode_input(record: HealthEpisode) -> Episode:
        continuity = (record.summary or {}).get("continuity")
        confirmed = continuity == "confirmed_continuous" and record.onset_date is not None
        return Episode(
            episode_id=record.id, symptom_code=code,
            # A date has no clock time; use its end to avoid overstating elapsed days.
            onset_at=datetime.combine(record.onset_date, time.max, tzinfo=timezone.utc) if confirmed else None,
            status="active" if record.status == "active" else (
                "resolved" if record.status == "resolved" else "uncertain"),
            continuity="continuous" if confirmed else (
                "resolved_then_recurred" if continuity == "returned_after_resolution" else "unknown"),
            onset_confirmed=confirmed,
        )

    same_symptom = db.scalars(select(HealthEpisode).where(
        HealthEpisode.patient_id == patient.id,
        HealthEpisode.normalized_symptom == episode.normalized_symptom,
    )).all()
    request = AssessmentInput(
        user_id=patient.id, request_id=f"episode:{episode.id}:{int(now.timestamp())}",
        as_of=now, population=Population(
            age_years=_age_on(patient.date_of_birth, now.date()),
            pregnant=pregnant,
        ),
        symptom_codes=[code], facts=facts, episodes=[episode_input(record) for record in same_symptom],
    )
    return assess(registry(), request, include_drafts=True)
