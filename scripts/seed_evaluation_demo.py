"""Create one isolated account with three clearly fictional evaluation profiles.

Run from the repository root with --apply. This never modifies existing patient
records and deliberately does not create a WhatsApp identity or send a message.
"""

import argparse
import json
import os
import secrets
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    AuditLog, CarePlan, CareTask, ClinicalAssessment, ConsentRecord, Conversation,
    DocumentExtraction, ExternalIdentity, HealthEpisode, MedicalDocument,
    MedicationRecord, Message, MobileCredential, PatientAccess, PatientProfile,
    SymptomEvent, User,
)
from app.db.session import SessionLocal
from app.services.mobile_auth import password_hasher


MARKER = "evaluation-2026-11-v1"
DEMO_DOCUMENT_KEY = "demo://evaluation-consultation-v1"
DEMO_PHONE = "+919000000001"
IST = ZoneInfo("Asia/Kolkata")


def _at(days_ago: int, now: datetime, hour: int = 10) -> datetime:
    local = now.astimezone(IST) - timedelta(days=days_ago)
    return local.replace(hour=hour, minute=20, second=0, microsecond=0).astimezone(timezone.utc)


def _profile(db: Session, owner: User, name: str, relationship: str,
             role: str, now: datetime) -> PatientProfile:
    user = owner if role == "owner" else User()
    if user is not owner:
        db.add(user)
        db.flush()
    profile = PatientProfile(user_id=user.id, display_name=name, preferred_language="en",
                             created_at=_at(42, now))
    db.add(profile)
    db.flush()
    db.add(PatientAccess(account_user_id=owner.id, patient_id=profile.id,
                         relationship=relationship, role=role, created_at=_at(42, now)))
    for purpose in ("health_processing", "ai_assistance"):
        db.add(ConsentRecord(patient_id=profile.id, purpose=purpose,
                             status="granted", policy_version="2026-11",
                             granted_at=_at(42, now), created_at=_at(42, now)))
    db.add(AuditLog(patient_id=profile.id, actor_type="demo_seed",
                    action="synthetic_evaluation_profile", target_type="patient",
                    target_id=profile.id, details={"synthetic": True, "marker": MARKER},
                    created_at=_at(42, now)))
    return profile


def _conversation(db: Session, profile: PatientProfile, now: datetime) -> Conversation:
    row = Conversation(patient_id=profile.id, channel="mobile", status="active", state={},
                       created_at=_at(40, now))
    db.add(row)
    db.flush()
    return row


def _message(db: Session, profile: PatientProfile, conversation: Conversation,
             text: str, when: datetime, direction: str) -> Message:
    row = Message(patient_id=profile.id, conversation_id=conversation.id, provider="mobile",
                  provider_message_id="demo:" + secrets.token_hex(16),
                  direction=direction, message_type="text", content=text,
                  message_timestamp=when, processing_status="completed",
                  metadata_json={"synthetic_demo": True}, created_at=when)
    db.add(row)
    db.flush()
    return row


def _event(db: Session, episode: HealthEpisode, message: Message,
           when: datetime, symptom: str, detail: str) -> None:
    db.add(SymptomEvent(episode_id=episode.id, source_message_id=message.id,
                        symptom=symptom, normalized_symptom=episode.normalized_symptom,
                        details={"description": detail, "synthetic_demo": True},
                        source_type="patient_reported", verification_status="reported",
                        recorded_at=when, created_at=when))


def seed_demo(db: Session, now: datetime, password: str,
              phone: str = DEMO_PHONE) -> dict[str, str]:
    if db.scalar(select(ExternalIdentity).where(
        ExternalIdentity.provider == "demo", ExternalIdentity.external_id == MARKER)):
        raise ValueError("This synthetic evaluation set already exists; no records were changed")
    if db.scalar(select(MobileCredential).where(MobileCredential.phone == phone)):
        raise ValueError("The demo phone is already in use; no records were changed")
    if db.scalar(select(MedicalDocument).where(MedicalDocument.storage_key == DEMO_DOCUMENT_KEY)):
        raise ValueError("The synthetic document already exists; no records were changed")

    owner = User(created_at=_at(42, now))
    db.add(owner)
    db.flush()
    db.add(MobileCredential(user_id=owner.id, phone=phone,
                            password_hash=password_hasher.hash(password), created_at=_at(42, now)))
    db.add(ExternalIdentity(user_id=owner.id, provider="demo", external_id=MARKER,
                            verified_at=now, created_at=_at(42, now)))
    urgent = _profile(db, owner, "[DEMO] Urgent concern", "self", "owner", now)
    routine = _profile(db, owner, "[DEMO] Routine concern", "other", "guardian", now)
    care = _profile(db, owner, "[DEMO] Records and care", "other", "guardian", now)

    urgent_chat = _conversation(db, urgent, now)
    urgent_episode = HealthEpisode(patient_id=urgent.id, primary_symptom="Chest discomfort",
                                   normalized_symptom="chest pain", status="active",
                                   onset_date=(_at(38, now)).date(),
                                   last_reported_at=now - timedelta(minutes=20),
                                   summary={"synthetic_demo": True,
                                            "progression": "Reported intermittent discomfort, then new chest pain with breathing difficulty"},
                                   created_at=_at(38, now))
    db.add(urgent_episode)
    db.flush()
    for days, detail in ((38, "Intermittent mild chest discomfort after activity."),
                         (16, "Chest discomfort returned on two occasions."),
                         (3, "Episodes felt more frequent than before.")):
        when = _at(days, now)
        incoming = _message(db, urgent, urgent_chat, detail, when, "incoming")
        _event(db, urgent_episode, incoming, when, "Chest discomfort", detail)
        _message(db, urgent, urgent_chat,
                 "[DEMO] Your report was recorded. If symptoms change or become severe, seek care.",
                 when + timedelta(minutes=1), "outgoing")
    latest_time = now - timedelta(minutes=20)
    latest = _message(db, urgent, urgent_chat,
                      "[DEMO] I now have chest pain and difficulty breathing.", latest_time, "incoming")
    _event(db, urgent_episode, latest, latest_time, "Chest pain and difficulty breathing",
           "New chest pain and breathing difficulty reported together")
    urgent_chat.active_episode_id = urgent_episode.id
    db.add(ClinicalAssessment(patient_id=urgent.id, episode_id=urgent_episode.id,
                              pathway_name="synthetic_evaluation_scenario",
                              pathway_version="demo-seeded-v1", outcome="emergency",
                              inputs={"status": "assessed", "synthetic_demo": True,
                                      "basis": "Seeded scenario; not a live clinical assessment"},
                              created_at=now - timedelta(minutes=15)))
    _message(db, urgent, urgent_chat,
             "[DEMO] New chest pain with difficulty breathing needs emergency medical help now. Call 112 in India. Do not wait for a map search or further chat. This is a scripted synthetic demonstration, not a diagnosis.",
             now - timedelta(minutes=15), "outgoing")

    routine_chat = _conversation(db, routine, now)
    routine_episode = HealthEpisode(patient_id=routine.id,
                                    primary_symptom="Intermittent sneezing and nasal irritation",
                                    normalized_symptom="nasal irritation", status="active",
                                    onset_date=_at(31, now).date(),
                                    last_reported_at=_at(1, now),
                                    summary={"synthetic_demo": True, "severity": "mild",
                                             "progression": "Intermittent and improving; no reported impact on daily activities"},
                                    created_at=_at(31, now))
    db.add(routine_episode)
    db.flush()
    for days, detail in ((31, "Mild sneezing and nasal irritation started; I can do my usual activities."),
                         (20, "Still intermittent; no new symptoms."),
                         (9, "It is less frequent this week."),
                         (1, "Only occasional mild sneezing now; feeling otherwise well.")):
        when = _at(days, now)
        incoming = _message(db, routine, routine_chat, "[DEMO] " + detail, when, "incoming")
        _event(db, routine_episode, incoming, when, "Nasal irritation", detail)
    routine_chat.active_episode_id = routine_episode.id
    db.add(ClinicalAssessment(patient_id=routine.id, episode_id=routine_episode.id,
                              pathway_name="synthetic_evaluation_scenario",
                              pathway_version="demo-seeded-v1", outcome="routine",
                              inputs={"status": "assessed", "synthetic_demo": True,
                                      "basis": "Seeded scenario; not a live clinical assessment"},
                              created_at=_at(1, now) + timedelta(minutes=2)))
    _message(db, routine, routine_chat,
             "[DEMO] The mild, intermittent symptom appears to be improving. This example has no urgent warning. Keep tracking changes; seek a clinician if it persists, worsens, or new concerning symptoms appear. This is not a diagnosis.",
             _at(1, now) + timedelta(minutes=3), "outgoing")

    care_chat = _conversation(db, care, now)
    visit_time = _at(14, now)
    visit_message = _message(db, care, care_chat,
                             "[DEMO] I had a routine visit and want to keep my fictional consultation note here.",
                             visit_time, "incoming")
    care_episode = HealthEpisode(patient_id=care.id, primary_symptom="Routine consultation",
                                 normalized_symptom="routine visit", status="resolved",
                                 onset_date=visit_time.date(), last_reported_at=visit_time,
                                 summary={"synthetic_demo": True, "note": "Fictional consultation record"},
                                 created_at=visit_time)
    db.add(care_episode)
    db.flush()
    _event(db, care_episode, visit_message, visit_time, "Routine consultation",
           "Fictional doctor document recorded after a demonstration visit")
    _message(db, care, care_chat,
             "[DEMO] Your fictional visit and follow-up plan are in Records and My Care.",
             visit_time + timedelta(minutes=2), "outgoing")
    document = MedicalDocument(patient_id=care.id, storage_key=DEMO_DOCUMENT_KEY,
                               content_type="application/pdf", processing_status="extracted",
                               created_at=visit_time)
    db.add(document)
    db.flush()
    db.add(DocumentExtraction(document_id=document.id, result={
        "filename": "FICTIONAL consultation note - DEMO.pdf",
        "title": "Fictional consultation note", "notes": "Synthetic sample; no real doctor or prescription",
        "conditions": [], "medications": [], "allergies": []},
        verification_status="demo_sample", created_at=visit_time + timedelta(minutes=1)))
    db.add(MedicationRecord(patient_id=care.id, name="[DEMO] Medicine reminder example",
                            dosage="No real drug or dose; follow an actual prescriber",
                            status="reported", source_reference=document.id,
                            created_at=visit_time + timedelta(minutes=3)))
    plan = CarePlan(patient_id=care.id, status="active",
                    source_reference="Fictional demo consultation", created_at=visit_time)
    db.add(plan)
    db.flush()
    tomorrow = now.astimezone(IST).date() + timedelta(days=1)
    medicine_due = datetime.combine(tomorrow, time(20, 0), IST).astimezone(timezone.utc)
    followup_due = datetime.combine(tomorrow + timedelta(days=1), time(10, 0), IST).astimezone(timezone.utc)
    for description, due_at, status in (
        ("[DEMO] Review medicine instructions from your real prescriber", medicine_due, "pending"),
        ("[DEMO] Follow-up consultation: confirm with clinic", followup_due, "pending"),
        ("[DEMO] Save consultation note", visit_time + timedelta(hours=2), "completed"),
    ):
        db.add(CareTask(care_plan_id=plan.id, description=description, due_at=due_at,
                        status=status, created_at=visit_time))
    db.flush()
    return {"phone": phone, "urgent_patient_id": urgent.id,
            "routine_patient_id": routine.id, "care_patient_id": care.id}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write isolated synthetic records to the configured database")
    parser.add_argument("--credentials-file", type=Path,
                        default=Path(".demo-evaluation-login.json"))
    args = parser.parse_args()
    if not args.apply:
        print("Dry run: one fictional account, three profiles, historical events, one bundled PDF, care tasks. Use --apply to write.")
        return
    if args.credentials_file.exists():
        raise SystemExit("Credentials file exists; refusing to overwrite it or create duplicate profiles")
    password = secrets.token_urlsafe(18)
    with SessionLocal() as db:
        try:
            result = seed_demo(db, datetime.now(timezone.utc), password)
            db.commit()
        except Exception:
            db.rollback()
            raise
    payload = {"phone": result["phone"], "password": password,
               "profiles": {key: value for key, value in result.items() if key.endswith("_patient_id")},
               "synthetic_demo": True}
    path = args.credentials_file.resolve()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")
    print(f"Created three isolated synthetic profiles. Credentials saved to {path} (mode 0600).")


if __name__ == "__main__":
    main()
