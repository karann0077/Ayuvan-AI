from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import HealthEpisode, PatientProfile, SymptomEvent, User
from app.services.pathway_simulation import simulate_patient_episode


def test_episode_bridge_keeps_unknowns_unknown_and_does_not_write() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User()
        patient = PatientProfile(user=user, date_of_birth=date(1995, 1, 1))
        episode = HealthEpisode(patient=patient, normalized_symptom="cough", primary_symptom="cough")
        old = HealthEpisode(
            patient=patient, normalized_symptom="cough", primary_symptom="cough",
            status="resolved", onset_date=date(2026, 10, 1),
            summary={"continuity": "confirmed_continuous"},
        )
        db.add_all([user, patient, episode, old])
        db.flush()
        db.add(SymptomEvent(
            episode_id=episode.id, symptom="cough", normalized_symptom="cough",
            details={"duration": "15 days"},
            recorded_at=datetime(2026, 11, 16, 9, tzinfo=timezone.utc),
        ))
        db.flush()
        result = simulate_patient_episode(
            db, patient.id, episode.id, as_of=datetime(2026, 11, 16, 10, tzinfo=timezone.utc)
        )
        assert result.simulated is True
        assert result.priority is None
        assert result.status == "INSUFFICIENT_INFORMATION"
        assert result.pathway_versions["adult_cough_in"] == "0.2.0"
        assert "PREGNANCY_STATUS_UNKNOWN" in result.results[1].reason_codes
        # A reported free-text duration must not turn into a confirmed numeric fact.
        result_with_population = simulate_patient_episode(
            db, patient.id, episode.id, pregnant=False,
            as_of=datetime(2026, 11, 16, 10, tzinfo=timezone.utc),
        )
        assert result_with_population.priority is None
        assert result_with_population.status == "QUESTION_REQUIRED"
        assert not db.new


def test_episode_bridge_rejects_another_patients_episode() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        first = PatientProfile(user=User())
        second = PatientProfile(user=User())
        episode = HealthEpisode(patient=first, normalized_symptom="cough")
        db.add_all([first, second, episode])
        db.flush()
        with pytest.raises(ValueError, match="not found"):
            simulate_patient_episode(db, second.id, episode.id)
