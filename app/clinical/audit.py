"""Optional development audit store. Production requires PHI encryption and RBAC."""
import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

class Base(DeclarativeBase): pass

class AssessmentAudit(Base):
    __tablename__ = "clinical_assessment_audit"
    assessment_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    user_ref: Mapped[str] = mapped_column(String(128), index=True)
    request_ref: Mapped[str] = mapped_column(String(128), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    engine_result_json: Mapped[str] = mapped_column(Text)
    evidence_snapshot_json: Mapped[str] = mapped_column(Text)
    pathway_sha256_json: Mapped[str] = mapped_column(Text)
    pathway_versions_json: Mapped[str] = mapped_column(Text)
    reason_codes_json: Mapped[str] = mapped_column(Text)


def create_audit_engine(database_url: str):
    db = create_engine(database_url)
    from . import storage  # import mapped tables for local prototype setup
    Base.metadata.create_all(db)
    return db


def record_audit(db, request, result):
    with Session(db) as session:
        session.add(AssessmentAudit(
            assessment_id=result.assessment_id,
            user_ref=request.user_id, request_ref=request.request_id,
            created_at=datetime.now(timezone.utc),
            engine_result_json=result.model_dump_json(),
            evidence_snapshot_json=request.model_dump_json(),
            pathway_sha256_json=json.dumps(result.pathway_sha256),
            pathway_versions_json=json.dumps(result.pathway_versions),
            reason_codes_json=json.dumps(result.reason_codes)
        ))
        session.commit()
