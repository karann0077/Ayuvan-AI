"""Mobile account authentication and patient access boundaries."""
import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import MobileCredential, MobileSession, PatientAccess, PatientProfile, User
from app.db.session import get_db

password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)


def normalize_indian_phone(value: str) -> str:
    digits = re.sub(r"[\s()-]", "", value)
    if re.fullmatch(r"[6-9][0-9]{9}", digits):
        return "+91" + digits
    if re.fullmatch(r"\+91[6-9][0-9]{9}", digits):
        return digits
    raise HTTPException(status_code=422, detail="Enter a valid Indian mobile number")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(db: Session, user_id: str) -> tuple[str, MobileSession]:
    token = secrets.token_urlsafe(48)
    session = MobileSession(
        user_id=user_id, token_hash=hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=get_settings().mobile_session_days),
    )
    db.add(session)
    db.flush()
    return token, session


def authenticate(db: Session, phone: str, password: str) -> MobileCredential:
    credential = db.scalar(select(MobileCredential).where(MobileCredential.phone == phone))
    now = datetime.now(timezone.utc)
    if credential is None:
        raise HTTPException(status_code=401, detail="Incorrect phone number or password")
    if credential.locked_until and credential.locked_until.replace(tzinfo=timezone.utc) > now:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later")
    try:
        password_hasher.verify(credential.password_hash, password)
    except (VerifyMismatchError, VerificationError):
        credential.failed_attempts += 1
        if credential.failed_attempts >= 5:
            credential.locked_until = now + timedelta(minutes=15)
            credential.failed_attempts = 0
        db.commit()
        raise HTTPException(status_code=401, detail="Incorrect phone number or password") from None
    credential.failed_attempts = 0
    credential.locked_until = None
    if password_hasher.check_needs_rehash(credential.password_hash):
        credential.password_hash = password_hasher.hash(password)
    return credential


def get_current_session(
    authorization: str | None = Header(default=None), db: Session = Depends(get_db)
) -> MobileSession:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Sign in required")
    session = db.scalar(select(MobileSession).where(MobileSession.token_hash == hash_token(token)))
    if session is None or session.revoked_at is not None or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired. Sign in again")
    user = db.get(User, session.user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail="Account unavailable")
    return session


def require_patient(db: Session, account_user_id: str, patient_id: str) -> tuple[PatientProfile, PatientAccess]:
    access = db.scalar(select(PatientAccess).where(
        PatientAccess.account_user_id == account_user_id, PatientAccess.patient_id == patient_id
    ))
    patient = db.get(PatientProfile, patient_id) if access else None
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    return patient, access
