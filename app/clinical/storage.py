"""Optional persistence adapter to integrate into the existing AYUVAN backend.
Use PostgreSQL + Alembic migrations in production; SQLite create_all is for tests.
Caller MUST supply an authenticated user_ref, never use a client-chosen ID in production.
"""
import json
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, DateTime, Text, Boolean, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column, Session
from .audit import Base
from .types import Fact, Episode

class HealthEpisodeRow(Base):
    __tablename__ = 'ayuvan_health_episodes'
    episode_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_ref: Mapped[str] = mapped_column(String(128), index=True)
    symptom_code: Mapped[str] = mapped_column(String(80), index=True)
    onset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(24), default='uncertain')
    continuity: Mapped[str] = mapped_column(String(40), default='unknown')
    onset_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)

class ClinicalFactRow(Base):
    __tablename__ = 'ayuvan_clinical_facts'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_ref: Mapped[str] = mapped_column(String(128), index=True)
    episode_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    code: Mapped[str] = mapped_column(String(80), index=True)
    state: Mapped[str] = mapped_column(String(24))
    value_json: Mapped[str] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)
    source_type: Mapped[str] = mapped_column(String(24))
    source_id: Mapped[str] = mapped_column(String(128))
    verification: Mapped[str] = mapped_column(String(32))
    __table_args__ = (UniqueConstraint('user_ref','source_id','code','observed_at',
                                      name='uq_fact_event_idempotency'),)

class AssessmentQuestionRow(Base):
    __tablename__ = 'ayuvan_assessment_questions'
    question_ref: Mapped[str] = mapped_column(String(128), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(String(80), index=True)
    user_ref: Mapped[str] = mapped_column(String(128), index=True)
    question_id: Mapped[str] = mapped_column(String(100))
    pathway_id: Mapped[str] = mapped_column(String(100))
    pathway_version: Mapped[str] = mapped_column(String(30))
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    answer_source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


def put_episode(session: Session, user_ref: str, episode: Episode):
    row = session.get(HealthEpisodeRow, episode.episode_id)
    if row and row.user_ref != user_ref:
        raise PermissionError('Episode belongs to another user')
    if row is None:
        row = HealthEpisodeRow(episode_id=episode.episode_id, user_ref=user_ref, symptom_code=episode.symptom_code)
        session.add(row)
    for name in ('onset_at','resolution_at','status','continuity','onset_confirmed'):
        setattr(row,name,getattr(episode,name))
    session.flush()
    return row


def put_fact(session: Session, user_ref: str, fact: Fact, episode_id: str | None = None) -> bool:
    """Return True if new, False if retry. Reject changed payload with same idempotency key."""
    if episode_id:
        ep=session.get(HealthEpisodeRow, episode_id)
        if ep is None or ep.user_ref!=user_ref:
            raise PermissionError('No authorized episode')
    exists=session.scalar(select(ClinicalFactRow).where(
        ClinicalFactRow.user_ref == user_ref, ClinicalFactRow.source_id == fact.source_id,
        ClinicalFactRow.code == fact.code, ClinicalFactRow.observed_at == fact.observed_at))
    body=json.dumps(fact.value,sort_keys=True)
    if exists:
        if (exists.state,exists.value_json,exists.source_type,exists.verification,
            exists.valid_until) != (fact.state.value,body,fact.source_type,fact.verification,
            fact.valid_until.replace(tzinfo=None) if fact.valid_until and exists.valid_until and exists.valid_until.tzinfo is None else fact.valid_until):
            raise ValueError('Idempotency-key collision with different clinical content')
        return False
    session.add(ClinicalFactRow(user_ref=user_ref,episode_id=episode_id,code=fact.code,
        state=fact.state.value,value_json=body,observed_at=fact.observed_at,
        recorded_at=fact.recorded_at or datetime.now(timezone.utc),
        valid_until=fact.valid_until,
        source_type=fact.source_type,source_id=fact.source_id,verification=fact.verification))
    session.flush()
    return True


def load_facts(session: Session,user_ref: str,episode_id: str | None=None) -> list[Fact]:
    q=select(ClinicalFactRow).where(ClinicalFactRow.user_ref==user_ref)
    if episode_id: q=q.where(ClinicalFactRow.episode_id==episode_id)
    rows=session.scalars(q.order_by(ClinicalFactRow.observed_at)).all()
    def utc_aware(v):return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v
    return [Fact(code=r.code,state=r.state,value=json.loads(r.value_json),
                 observed_at=utc_aware(r.observed_at),recorded_at=utc_aware(r.recorded_at),
                 valid_until=utc_aware(r.valid_until) if r.valid_until else None,
                 source_type=r.source_type,source_id=r.source_id,verification=r.verification) for r in rows]
