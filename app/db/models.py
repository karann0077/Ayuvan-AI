import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


def new_id() -> str:
    return str(uuid.uuid4())


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    patient_profile: Mapped["PatientProfile"] = relationship(back_populates="user", uselist=False)
    identities: Mapped[list["ExternalIdentity"]] = relationship(back_populates="user")


class PatientProfile(TimestampMixin, Base):
    __tablename__ = "patient_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    preferred_language: Mapped[str | None] = mapped_column(String(16))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    summary_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user: Mapped[User] = relationship(back_populates="patient_profile")
    episodes: Mapped[list["HealthEpisode"]] = relationship(back_populates="patient")


class ExternalIdentity(TimestampMixin, Base):
    __tablename__ = "external_identities"
    __table_args__ = (UniqueConstraint("provider", "external_id", name="provider_external_identity"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # whatsapp, mobile
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    user: Mapped[User] = relationship(back_populates="identities")


class ConsentRecord(TimestampMixin, Base):
    __tablename__ = "consent_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # granted, withdrawn
    policy_version: Mapped[str | None] = mapped_column(String(64))
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="whatsapp")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    active_episode_id: Mapped[str | None] = mapped_column(ForeignKey("health_episodes.id"))
    state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("provider", "provider_message_id", name="provider_message"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("conversations.id"), index=True)
    patient_id: Mapped[str | None] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="whatsapp")
    provider_message_id: Mapped[str] = mapped_column(String(128), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # incoming/outgoing
    message_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    content_reference: Mapped[str | None] = mapped_column(String(255))
    message_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="received")
    ai_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_applicable")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    conversation: Mapped[Conversation | None] = relationship(back_populates="messages")


class HealthEpisode(TimestampMixin, Base):
    __tablename__ = "health_episodes"
    __table_args__ = (Index("ix_episode_patient_status", "patient_id", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    primary_symptom: Mapped[str | None] = mapped_column(String(128), index=True)
    normalized_symptom: Mapped[str | None] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    onset_date: Mapped[date | None] = mapped_column(Date)
    last_reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    patient: Mapped[PatientProfile] = relationship(back_populates="episodes")
    symptom_events: Mapped[list["SymptomEvent"]] = relationship(back_populates="episode")


class SymptomEvent(TimestampMixin, Base):
    __tablename__ = "symptom_events"
    __table_args__ = (Index("ix_symptom_episode_recorded", "episode_id", "recorded_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    episode_id: Mapped[str] = mapped_column(ForeignKey("health_episodes.id"), nullable=False, index=True)
    source_message_id: Mapped[str | None] = mapped_column(ForeignKey("messages.id"))
    symptom: Mapped[str] = mapped_column(String(128), nullable=False)
    normalized_symptom: Mapped[str | None] = mapped_column(String(128), index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="patient_reported")
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="reported")
    confidence: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    episode: Mapped[HealthEpisode] = relationship(back_populates="symptom_events")


class MedicalCondition(TimestampMixin, Base):
    __tablename__ = "medical_conditions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="patient_reported")
    source_reference: Mapped[str | None] = mapped_column(String(255))


class Allergy(TimestampMixin, Base):
    __tablename__ = "allergies"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    allergen: Mapped[str] = mapped_column(String(255), nullable=False)
    reaction: Mapped[str | None] = mapped_column(String(255))
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="patient_reported")


class MedicationRecord(TimestampMixin, Base):
    __tablename__ = "medication_records"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="reported")
    source_reference: Mapped[str | None] = mapped_column(String(255))


class MedicalObservation(TimestampMixin, Base):
    __tablename__ = "medical_observations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(255))
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="reported")


class MedicalDocument(TimestampMixin, Base):
    __tablename__ = "medical_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    source_media_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    content_type: Mapped[str | None] = mapped_column(String(128))
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")


class DocumentExtraction(TimestampMixin, Base):
    __tablename__ = "document_extractions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("medical_documents.id"), nullable=False, index=True)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[int | None] = mapped_column(Integer)
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="unverified")


class ClinicalAssessment(TimestampMixin, Base):
    __tablename__ = "clinical_assessments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    episode_id: Mapped[str | None] = mapped_column(ForeignKey("health_episodes.id"))
    pathway_name: Mapped[str] = mapped_column(String(128), nullable=False)
    pathway_version: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(64), nullable=False)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    context_version: Mapped[int | None] = mapped_column(Integer)


class PatientSummary(TimestampMixin, Base):
    __tablename__ = "patient_summaries"
    __table_args__ = (UniqueConstraint("patient_id", "version", name="patient_summary_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    source_record_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)


class CarePlan(TimestampMixin, Base):
    __tablename__ = "care_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    source_reference: Mapped[str | None] = mapped_column(String(255))


class CareTask(TimestampMixin, Base):
    __tablename__ = "care_tasks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    care_plan_id: Mapped[str] = mapped_column(ForeignKey("care_plans.id"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patient_profiles.id"), nullable=False, index=True)
    provider_media_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    media_type: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(128))
    processing_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    storage_key: Mapped[str | None] = mapped_column(String(512))


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    patient_id: Mapped[str | None] = mapped_column(ForeignKey("patient_profiles.id"), index=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    target_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
