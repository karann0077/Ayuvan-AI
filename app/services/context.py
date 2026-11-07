from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Allergy, CarePlan, CareTask, Conversation, HealthEpisode, MedicalCondition,
    MedicationRecord, Message, PatientProfile, SymptomEvent,
)
from app.schemas import PatientContext


class PatientContextBuilder:
    """Builds minimal, relevant context; the database remains authoritative."""

    def build(self, db: Session, patient_id: str, current_symptom: str | None = None) -> PatientContext:
        patient = db.get(PatientProfile, patient_id)
        if patient is None:
            raise ValueError("Unknown patient")
        medications = db.scalars(select(MedicationRecord).where(MedicationRecord.patient_id == patient_id)).all()
        allergies = db.scalars(select(Allergy).where(Allergy.patient_id == patient_id)).all()
        conditions = db.scalars(select(MedicalCondition).where(MedicalCondition.patient_id == patient_id)).all()
        active = db.scalars(
            select(HealthEpisode).where(
                HealthEpisode.patient_id == patient_id, HealthEpisode.status == "active"
            ).order_by(HealthEpisode.last_reported_at.desc()).limit(5)
        ).all()

        related = self._related_episodes(db, patient_id, current_symptom)
        pending_tasks = db.scalars(
            select(CareTask).join(CarePlan).where(
                CarePlan.patient_id == patient_id, CareTask.status.in_(["pending", "in_progress"])
            ).limit(10)
        ).all()
        recent_messages = db.scalars(
            select(Message).where(Message.patient_id == patient_id).order_by(Message.created_at.desc()).limit(8)
        ).all()
        source_ids = [item.id for item in active] + [item.id for item in related]
        return PatientContext(
            patient_id=patient_id,
            summary_version=patient.summary_version,
            preferred_language=patient.preferred_language,
            current_medications=[m.name for m in medications if m.status in {"active", "reported", "confirmed"}],
            allergies=[a.allergen for a in allergies],
            conditions=[c.name for c in conditions],
            active_episodes=[self._episode_summary(item) for item in active],
            related_episodes=[self._episode_summary(item) for item in related],
            pending_tasks=[task.description for task in pending_tasks],
            recent_conversation=[
                {"role": "user" if item.direction == "incoming" else "assistant", "content": item.content or ""}
                for item in reversed(recent_messages) if item.content
            ],
            source_record_ids=source_ids,
        )

    def _related_episodes(self, db: Session, patient_id: str, symptom: str | None) -> list[HealthEpisode]:
        if not symptom:
            return []
        # Deterministic keyword retrieval is the safe Stage-1 baseline. A pgvector ranker can
        # be added later as a secondary candidate generator, never as the record of truth.
        token = symptom.lower().strip()
        if not token:
            return []
        return db.scalars(
            select(HealthEpisode).where(
                HealthEpisode.patient_id == patient_id,
                HealthEpisode.normalized_symptom.ilike(f"%{token}%"),
            ).order_by(HealthEpisode.last_reported_at.desc()).limit(3)
        ).all()

    @staticmethod
    def _episode_summary(item: HealthEpisode) -> dict:
        return {
            "id": item.id,
            "symptom": item.primary_symptom,
            "status": item.status,
            "onset_date": item.onset_date.isoformat() if item.onset_date else None,
            "last_reported_at": item.last_reported_at.isoformat() if isinstance(item.last_reported_at, datetime) else None,
            "summary": item.summary,
        }
