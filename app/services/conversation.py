import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import (
    AuditLog, Conversation, ExternalIdentity, HealthEpisode, Message, PatientProfile,
    PatientSummary, SymptomEvent, User,
)
from app.schemas import SafetyOutcome, SymptomExtraction
from app.services.ai import GeminiService
from app.services.context import PatientContextBuilder
from app.services.intake import QuestionEngine
from app.services.review import ClinicalReviewEngine, ClinicalReviewOutcome
from app.services.safety import ClinicalSafetyEngine
from app.services.whatsapp import NormalizedIncomingMessage, WhatsAppClient, WhatsAppSendError, save_outgoing_message

logger = logging.getLogger(__name__)


URGENT_PATHWAY_RESPONSE = (
    "The symptom you selected can need urgent in-person assessment. Please seek emergency medical help now "
    "or contact your local emergency service. AYUVAN cannot assess an emergency through chat."
)


class ConversationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.context_builder = PatientContextBuilder()
        self.ai = GeminiService(self.settings)
        self.safety = ClinicalSafetyEngine()
        self.questions = QuestionEngine()
        self.review = ClinicalReviewEngine()
        self.whatsapp = WhatsAppClient(self.settings)

    def receive(self, db: Session, incoming: NormalizedIncomingMessage) -> str | None:
        """Persist the event before it is queued. Returns a message ID or None when duplicate."""
        existing = db.scalar(select(Message).where(
            Message.provider == "whatsapp", Message.provider_message_id == incoming.provider_message_id
        ))
        if existing:
            return None
        patient = self._find_or_provision_patient(db, incoming.sender)
        if patient is None:
            logger.warning("Rejected unlinked WhatsApp sender")
            return None
        conversation = self._active_conversation(db, patient.id)
        message = Message(
            patient_id=patient.id,
            conversation_id=conversation.id,
            provider="whatsapp",
            provider_message_id=incoming.provider_message_id,
            direction="incoming",
            message_type=incoming.message_type,
            content=incoming.content,
            content_reference=incoming.media_id,
            message_timestamp=incoming.timestamp,
            metadata_json=incoming.metadata,
        )
        db.add(message)
        db.add(AuditLog(patient_id=patient.id, actor_type="patient", action="message_received", target_type="message", target_id=message.id))
        db.commit()
        return message.id

    async def process_message(self, db: Session, message_id: str) -> None:
        message = db.get(Message, message_id)
        if message is None or message.processing_status in {"processed", "processing"}:
            return
        message.processing_status = "processing"
        db.commit()
        try:
            conversation = db.get(Conversation, message.conversation_id)
            if conversation is None or message.patient_id is None:
                raise ValueError("Message has no conversation or patient")
            if message.message_type not in {"text", "interactive"}:
                await self._send_and_record(
                    db, message.patient_id, conversation.id, self._phone_for_patient(db, message.patient_id),
                    "I received your file. Document and voice processing will be available shortly.", "text"
                )
                message.processing_status = "processed"
                db.commit()
                return
            user_text = message.content or ""
            safety = self.safety.assess(user_text)
            if safety.level == "emergency":
                self._record_assessment(db, message.patient_id, conversation.active_episode_id, safety)
                await self._send_and_record(
                    db, message.patient_id, conversation.id, self._phone_for_patient(db, message.patient_id),
                    safety.response or "Please seek emergency help.", "text"
                )
                message.processing_status = "processed"
                db.commit()
                return

            if self._is_explicit_resolution(user_text):
                active = db.get(HealthEpisode, conversation.active_episode_id) if conversation.active_episode_id else None
                if active and active.status == "active" and (active.normalized_symptom or "") in user_text.lower():
                    active.status = "resolved"
                    active.summary = {**(active.summary or {}), "resolution": "patient_reported"}
                    active.last_reported_at = message.message_timestamp or datetime.now(timezone.utc)
                    db.add(SymptomEvent(
                        episode_id=active.id, source_message_id=message.id,
                        symptom=active.primary_symptom or "symptom", normalized_symptom=active.normalized_symptom,
                        details={"resolution": "patient_reported"}, source_type="patient_reported",
                        verification_status="reported", confidence=100,
                    ))
                    conversation.state = {}
                    conversation.active_episode_id = None
                    self._refresh_summary(db, active.patient_id)
                    await self._send_and_record(
                        db, message.patient_id, conversation.id, self._phone_for_patient(db, message.patient_id),
                        "I've recorded that this concern has stopped. If it returns, tell me when it started again.", "text",
                    )
                    message.processing_status = "processed"
                    db.commit()
                    return

            pending_continuity = (conversation.state or {}).get("pending_continuity")
            if pending_continuity:
                old = db.get(HealthEpisode, pending_continuity["episode_id"])
                answer = message.metadata_json.get("reply_id")
                if not answer and message.message_type == "text":
                    lower = user_text.lower()
                    if any(term in lower for term in ("continued", "same cough", "never stopped")):
                        answer = "CONTINUED"
                    elif any(term in lower for term in ("went away", "came back", "returned", "again")):
                        answer = "RETURNED"
                if old and answer in {"CONTINUED", "RETURNED", "NOT_SURE"}:
                    extraction = SymptomExtraction.model_validate(pending_continuity["extraction"])
                    if answer == "CONTINUED":
                        episode = old
                        episode.status = "active"
                        # The earlier safety answers, severity and trajectory may no
                        # longer describe the patient's present condition.
                        stale_fields = {
                            "severity", "progression", "functional_impact", "associated_symptoms",
                            "headache_warning_signs", "chest_current_state", "breathing_status",
                        }
                        episode.summary = {
                            **{key: value for key, value in (episode.summary or {}).items()
                               if key not in stale_fields},
                            "continuity": "confirmed_continuous",
                        }
                    else:
                        old.status = "resolved" if answer == "RETURNED" else "continuity_unknown"
                        episode = HealthEpisode(
                            patient_id=message.patient_id, primary_symptom=extraction.main_symptom,
                            normalized_symptom=extraction.normalized_symptom,
                            summary={**self._extraction_summary(extraction), "continuity": (
                                "returned_after_resolution" if answer == "RETURNED" else "unknown")},
                        )
                        db.add(episode)
                        db.flush()
                    conversation.active_episode_id = episode.id
                    conversation.state = {"pending_continuity": None}
                    self._record_symptom_event(db, episode, message, extraction)
                    await self._respond_for_episode(db, conversation, message, episode, extraction)
                    message.processing_status = "processed"
                    db.commit()
                    return
                await self._send_and_record(
                    db, message.patient_id, conversation.id, self._phone_for_patient(db, message.patient_id),
                    "Please choose whether the earlier concern continued or went away and returned. If unsure, choose Not sure.", "text",
                )
                message.processing_status = "processed"
                db.commit()
                return

            pending = (conversation.state or {}).get("pending_question")
            pending_flow = (conversation.state or {}).get("pending_flow")
            if pending and message.message_type == "text":
                old_pending_episode = db.get(HealthEpisode, pending.get("episode_id"))
                symptom = (old_pending_episode.normalized_symptom or "").lower() if old_pending_episode else ""
                if symptom and symptom in user_text.lower() and self._needs_continuity_check(
                    old_pending_episode, SymptomExtraction(), message
                ):
                    # A fresh symptom report after a gap is not an answer to an old question.
                    conversation.state = {"pending_question": None}
                    pending = None
            if pending_flow:
                episode = db.get(HealthEpisode, pending_flow.get("episode_id"))
                if episode and message.metadata_json.get("reply_type") == "flow":
                    answers = self._apply_flow_answers(db, episode, message)
                    conversation.state = (
                        {"pending_flow": None}
                        if answers else {"pending_question": None, "flow_disabled_episode": episode.id}
                    )
                    if self._flow_has_urgent_answer(answers):
                        safety = SafetyOutcome(
                            level="emergency",
                            pathway_name="whatsapp_flow_warning_screen",
                            pathway_version=self.safety.pathway_version,
                            response=URGENT_PATHWAY_RESPONSE,
                            matched_terms=["flow_warning_answer"],
                        )
                        self._record_assessment(db, message.patient_id, episode.id, safety)
                        await self._send_and_record(
                            db, message.patient_id, conversation.id, self._phone_for_patient(db, message.patient_id),
                            URGENT_PATHWAY_RESPONSE, "text"
                        )
                    else:
                        await self._respond_for_episode(
                            db, conversation, message, episode, self._extraction_from_episode(episode)
                        )
                    message.processing_status = "processed"
                    db.commit()
                    return
                # A patient can type instead of opening the form; use the normal fallback.
                conversation.state = {"pending_flow": None}
            if pending:
                episode = db.get(HealthEpisode, pending.get("episode_id"))
                if episode:
                    replacement_extraction = await self._new_concern_extraction_if_present(
                        db, message, episode
                    )
                    if replacement_extraction:
                        conversation.state = {"pending_question": None}
                        replacement_episode = self._get_or_create_episode(
                            db, message.patient_id, replacement_extraction, conversation
                        )
                        self._record_symptom_event(db, replacement_episode, message, replacement_extraction)
                        await self._respond_for_episode(
                            db, conversation, message, replacement_episode, replacement_extraction
                        )
                        message.processing_status = "processed"
                        db.commit()
                        return
                    selected_id = self._apply_pending_answer(db, episode, message, pending)
                    conversation.state = {"pending_question": None}
                    db.flush()
                    if self._needs_urgent_escalation(pending, selected_id):
                        safety = SafetyOutcome(
                            level="emergency",
                            pathway_name=pending.get("pathway_id", "interactive_warning_screen"),
                            pathway_version=self.safety.pathway_version,
                            response=URGENT_PATHWAY_RESPONSE,
                            matched_terms=[selected_id],
                        )
                        self._record_assessment(db, message.patient_id, episode.id, safety)
                        await self._send_and_record(
                            db, message.patient_id, conversation.id, self._phone_for_patient(db, message.patient_id),
                            URGENT_PATHWAY_RESPONSE, "text"
                        )
                        message.processing_status = "processed"
                        db.commit()
                        return
                    extraction = self._extraction_from_episode(episode)
                    await self._respond_for_episode(db, conversation, message, episode, extraction)
                    message.processing_status = "processed"
                    db.commit()
                    return

            context = self.context_builder.build(db, message.patient_id)
            extraction = await self.ai.extract_symptoms(user_text, context)
            message.ai_status = "completed"
            if not extraction.main_symptom:
                await self._send_and_record(
                    db, message.patient_id, conversation.id, self._phone_for_patient(db, message.patient_id),
                    "I can help record a health concern. Please describe the symptom or concern you are experiencing.", "text"
                )
                message.processing_status = "processed"
                db.commit()
                return
            prior = db.scalar(select(HealthEpisode).where(
                HealthEpisode.patient_id == message.patient_id,
                HealthEpisode.normalized_symptom == (extraction.normalized_symptom or extraction.main_symptom),
            ).order_by(HealthEpisode.last_reported_at.desc()))
            if prior and self._needs_continuity_check(prior, extraction, message):
                conversation.state = {"pending_continuity": {
                    "episode_id": prior.id, "extraction": extraction.model_dump(mode="json"),
                }}
                label = extraction.main_symptom or "symptom"
                question = f"You mentioned {label} before. Did it continue since then, or go away and return?"
                provider_id = await self.whatsapp.send_buttons(
                    self._phone_for_patient(db, message.patient_id), question,
                    [("CONTINUED", "Continued"), ("RETURNED", "Went away, returned"), ("NOT_SURE", "Not sure")],
                )
                save_outgoing_message(db, message.patient_id, conversation.id, provider_id, question, "interactive")
                message.processing_status = "processed"
                db.commit()
                return
            episode = self._get_or_create_episode(db, message.patient_id, extraction, conversation)
            self._record_symptom_event(db, episode, message, extraction)
            await self._respond_for_episode(db, conversation, message, episode, extraction)
            message.processing_status = "processed"
            db.commit()
        except Exception as exc:
            db.rollback()
            failed = db.get(Message, message_id)
            if failed:
                failed.processing_status = "failed"
                failed.metadata_json = {
                    **(failed.metadata_json or {}),
                    "processing_error": exc.details if isinstance(exc, WhatsAppSendError) else {"type": type(exc).__name__},
                }
                db.commit()
            logger.exception("Message processing failed for internal message id %s", message_id)

    def _find_or_provision_patient(self, db: Session, phone: str) -> PatientProfile | None:
        identity = db.scalar(select(ExternalIdentity).where(
            ExternalIdentity.provider == "whatsapp", ExternalIdentity.external_id == phone,
            ExternalIdentity.is_active.is_(True)
        ))
        if identity:
            return db.scalar(select(PatientProfile).where(PatientProfile.user_id == identity.user_id))
        permitted_phone = self.settings.test_user_phone or self.settings.whatsapp_test_recipient
        if not (self.settings.allow_test_user_auto_provision and permitted_phone == phone):
            return None
        user = User()
        patient = PatientProfile(user=user)
        db.add_all([user, patient, ExternalIdentity(user=user, provider="whatsapp", external_id=phone, verified_at=datetime.now(timezone.utc))])
        db.flush()
        db.add(AuditLog(patient_id=patient.id, actor_type="system", action="test_patient_provisioned", target_type="patient", target_id=patient.id))
        db.commit()
        return patient

    @staticmethod
    def _active_conversation(db: Session, patient_id: str) -> Conversation:
        conversation = db.scalar(select(Conversation).where(
            Conversation.patient_id == patient_id, Conversation.channel == "whatsapp", Conversation.status == "active"
        ).order_by(Conversation.updated_at.desc()))
        if conversation is None:
            conversation = Conversation(patient_id=patient_id, channel="whatsapp", state={})
            db.add(conversation)
            db.flush()
        return conversation

    def _get_or_create_episode(
        self, db: Session, patient_id: str, extraction: SymptomExtraction, conversation: Conversation
    ) -> HealthEpisode:
        # Continue the explicitly active episode only when the normalised symptom matches.
        active = db.get(HealthEpisode, conversation.active_episode_id) if conversation.active_episode_id else None
        normalized = extraction.normalized_symptom or extraction.main_symptom
        if active and active.status == "active" and active.normalized_symptom == normalized:
            return active
        episode = db.scalar(select(HealthEpisode).where(
            HealthEpisode.patient_id == patient_id, HealthEpisode.status == "active",
            HealthEpisode.normalized_symptom == normalized,
        ).order_by(HealthEpisode.last_reported_at.desc()))
        if episode is None:
            episode = HealthEpisode(
                patient_id=patient_id, primary_symptom=extraction.main_symptom,
                normalized_symptom=normalized, summary=self._extraction_summary(extraction),
            )
            db.add(episode)
            db.flush()
        conversation.active_episode_id = episode.id
        return episode

    @staticmethod
    def _needs_continuity_check(prior: HealthEpisode, extraction: SymptomExtraction, message: Message) -> bool:
        if extraction.is_correction or extraction.duration:
            return False
        timestamp = message.message_timestamp or datetime.now(timezone.utc)
        last = prior.last_reported_at
        if timestamp.tzinfo and last and not last.tzinfo:
            last = last.replace(tzinfo=timezone.utc)
        return bool(last and (timestamp - last).total_seconds() >= 48 * 3600)

    @staticmethod
    def _is_explicit_resolution(text: str) -> bool:
        lower = text.lower()
        if any(phrase in lower for phrase in ("hasn't stopped", "has not stopped", "not gone away")):
            return False
        if any(phrase in lower for phrase in ("returned", "came back", "again")):
            return False
        return any(phrase in lower for phrase in (
            "has stopped", "have stopped", "stopped coughing", "cough stopped",
            "went away", "completely resolved", "completely gone",
        ))

    async def _new_concern_extraction_if_present(
        self, db: Session, message: Message, episode: HealthEpisode
    ) -> SymptomExtraction | None:
        """Allow a patient to interrupt a question to report a new health concern."""
        if message.message_type != "text" or not message.content:
            return None
        text = message.content.strip()
        lower = text.lower()
        if not lower.startswith(("i have ", "i am having ", "i'm having ", "new symptom", "another symptom")):
            return None
        extraction = await self.ai.extract_symptoms(
            text, self.context_builder.build(db, message.patient_id)
        )
        if not extraction.main_symptom:
            return None
        return extraction

    def _record_symptom_event(
        self, db: Session, episode: HealthEpisode, message: Message, extraction: SymptomExtraction
    ) -> None:
        details = extraction.model_dump(mode="json")
        event = SymptomEvent(
            episode_id=episode.id, source_message_id=message.id, symptom=extraction.main_symptom or episode.primary_symptom or "unclassified",
            normalized_symptom=extraction.normalized_symptom, details=details,
            source_type="patient_reported", verification_status="reported", confidence=extraction.confidence,
        )
        db.add(event)
        updated_summary = {**(episode.summary or {}), **{k: v for k, v in details.items() if v not in (None, [], "unknown")}}
        episode.summary = updated_summary
        episode.last_reported_at = datetime.now(timezone.utc)
        self._refresh_summary(db, episode.patient_id)

    def _apply_pending_answer(
        self, db: Session, episode: HealthEpisode, message: Message, pending: dict[str, Any]
    ) -> str | None:
        field = pending["field"]
        reply_id = message.metadata_json.get("reply_id") if message.message_type == "interactive" else None
        answer = pending.get("options", {}).get(reply_id) if reply_id else message.content
        if not answer:
            answer = message.content or "unknown"
        summary = {**(episode.summary or {}), field: answer}
        episode.summary = summary
        episode.last_reported_at = datetime.now(timezone.utc)
        db.add(SymptomEvent(
            episode_id=episode.id, source_message_id=message.id, symptom=episode.primary_symptom or "follow_up",
            normalized_symptom=episode.normalized_symptom, details={field: answer},
            source_type="patient_reported", verification_status="reported", confidence=100,
        ))
        self._refresh_summary(db, episode.patient_id)
        return reply_id

    def _apply_flow_answers(self, db: Session, episode: HealthEpisode, message: Message) -> dict[str, Any]:
        """Validate Flow fields before storing them as patient-reported facts."""
        raw = message.metadata_json.get("response_json")
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            parsed = {}
        if not isinstance(parsed, dict):
            return {}
        answers = parsed.get("response", parsed)
        if not isinstance(answers, dict):
            return {}
        clean = {
            key: self.questions.normalise_flow_answer(value) for key, value in answers.items()
            if key in self.questions.flow_fields and isinstance(value, (str, int, float, bool, list))
        }
        if not clean:
            return {}
        episode.summary = {**(episode.summary or {}), **clean}
        episode.last_reported_at = datetime.now(timezone.utc)
        db.add(SymptomEvent(
            episode_id=episode.id, source_message_id=message.id,
            symptom=episode.primary_symptom or "flow_follow_up", normalized_symptom=episode.normalized_symptom,
            details=clean, source_type="patient_reported", verification_status="reported", confidence=100,
        ))
        self._refresh_summary(db, episode.patient_id)
        return clean

    @staticmethod
    def _flow_has_urgent_answer(answers: dict[str, Any]) -> bool:
        text = json.dumps(answers).lower()
        urgent_markers = (
            "sudden", "worst", "weakness", "numb", "vision", "stiff neck", "hard to breathe", "faint",
        )
        return any(marker in text for marker in urgent_markers)

    async def _respond_for_episode(
        self, db: Session, conversation: Conversation, message: Message, episode: HealthEpisode,
        extraction: SymptomExtraction,
    ) -> None:
        context = self.context_builder.build(db, episode.patient_id, episode.normalized_symptom)
        related = [item for item in context.related_episodes if item["id"] != episode.id]
        prefix = ""
        if related:
            prefix = "*Previous record noted*\nI found an earlier report that may be related. I’ll keep it separate unless you tell me it is the same concern.\n\n"
        question = self.questions.next_question(episode, context)
        phone = self._phone_for_patient(db, episode.patient_id)
        if (
            self.settings.whatsapp_symptom_intake_flow_id and question
            and not question.urgent_option_ids
            and (conversation.state or {}).get("flow_disabled_episode") != episode.id
        ):
            # The Flow itself is configured and published in Meta. Its stable field IDs are
            # validated on return, while this backend owns episode/context association.
            conversation.state = {
                "pending_flow": {
                    "episode_id": episode.id,
                    "allowed_fields": sorted(self.questions.flow_fields),
                    "context_version": context.summary_version,
                }
            }
            flow_text = (
                "*Quick symptom update*\n"
                "Answer the short form in one go. I’ll only ask anything that is still missing."
            )
            provider_id = await self.whatsapp.send_flow(
                phone, prefix + flow_text, self.settings.whatsapp_symptom_intake_flow_id,
                self.settings.whatsapp_symptom_intake_flow_screen,
            )
            save_outgoing_message(
                db, episode.patient_id, conversation.id, provider_id, prefix + flow_text, "interactive",
                {"presentation": "flow", "episode_id": episode.id},
            )
            return
        if question:
            state = {
                "pending_question": {
                    "episode_id": episode.id, "field": question.field,
                    "options": dict(question.options), "context_version": context.summary_version,
                    "urgent_option_ids": question.urgent_option_ids,
                    "pathway_id": question.pathway_id,
                }
            }
            conversation.state = state
            if question.presentation == "list":
                provider_id = await self.whatsapp.send_list(
                    phone,
                    prefix + question.text,
                    question.button_label or "Choose one",
                    [(option_id, label, label) for option_id, label in question.options],
                )
                save_outgoing_message(
                    db, episode.patient_id, conversation.id, provider_id, prefix + question.text, "interactive",
                    {"field": question.field, "presentation": "list"},
                )
            elif question.options:
                provider_id = await self.whatsapp.send_buttons(phone, prefix + question.text, question.options)
                save_outgoing_message(
                    db, episode.patient_id, conversation.id, provider_id, prefix + question.text, "interactive",
                    {"field": question.field, "presentation": "buttons"},
                )
            else:
                provider_id = await self.whatsapp.send_text(phone, prefix + question.text)
                save_outgoing_message(db, episode.patient_id, conversation.id, provider_id, prefix + question.text, "text", {"field": question.field})
        else:
            conversation.state = {"pending_question": None}
            review = self.review.assess(episode, context)
            self._record_review_assessment(db, episode.patient_id, episode.id, review, context.summary_version)
            response = prefix + self._completion_message(episode, review)
            provider_id = await self.whatsapp.send_text(phone, response)
            save_outgoing_message(db, episode.patient_id, conversation.id, provider_id, response, "text")

    @staticmethod
    def _needs_urgent_escalation(pending: dict[str, Any], selected_id: str | None) -> bool:
        return bool(selected_id and selected_id in pending.get("urgent_option_ids", []))

    @staticmethod
    def _completion_message(episode: HealthEpisode, review: ClinicalReviewOutcome) -> str:
        """Close in short WhatsApp sections: factual, explainable, and non-diagnostic."""
        summary = episode.summary or {}
        details = [episode.primary_symptom or "your concern"]
        if summary.get("duration"):
            details.append(f"reported for {summary['duration']}")
        elif summary.get("onset"):
            details.append(f"starting {summary['onset']}")
        if summary.get("location"):
            details.append(f"at {summary['location']}")
        if summary.get("severity"):
            details.append(f"currently {summary['severity'].lower()}")
        lines = ["*Recorded*", "• " + "; ".join(details)]
        if review.level == "timely_assessment":
            lines.extend([
                "", "*Recommended next step*", "• Arrange a clinician appointment soon.",
                "", "*Why AYUVAN is flagging this*",
                *[f"• {reason}" for reason in review.reasons[:3]],
                "", "This does not identify the cause or predict a disease. A clinician can assess it with your full history.",
            ])
        elif review.status == "need_more_information":
            lines.extend([
                "", "*Next step*", "• Some important details are still unclear. Share when this began or any change you notice.",
                "", "This chat cannot rule out a serious cause. This is not a diagnosis.",
            ])
        else:
            lines.extend([
                "", "*Next step*", "• Keep an eye on how it changes and share any new or worsening symptom.",
                "", "This chat cannot rule out every serious cause. This is not a diagnosis.",
            ])
        lines.extend([
            "", "*Get urgent in-person help now* if it becomes sudden or severe, or if you notice new warning signs.",
        ])
        return "\n".join(lines)

    @staticmethod
    def _extraction_summary(extraction: SymptomExtraction) -> dict[str, Any]:
        return {key: value for key, value in extraction.model_dump(mode="json").items() if value not in (None, [], "unknown")}

    @staticmethod
    def _extraction_from_episode(episode: HealthEpisode) -> SymptomExtraction:
        summary = episode.summary or {}
        allowed = {key: summary[key] for key in SymptomExtraction.model_fields if key in summary}
        allowed["main_symptom"] = allowed.get("main_symptom") or episode.primary_symptom
        allowed["normalized_symptom"] = allowed.get("normalized_symptom") or episode.normalized_symptom
        return SymptomExtraction(**allowed)

    @staticmethod
    def _phone_for_patient(db: Session, patient_id: str) -> str:
        identity = db.scalar(select(ExternalIdentity).join(PatientProfile, ExternalIdentity.user_id == PatientProfile.user_id).where(
            PatientProfile.id == patient_id, ExternalIdentity.provider == "whatsapp", ExternalIdentity.is_active.is_(True)
        ))
        if identity is None:
            raise ValueError("Patient has no active WhatsApp identity")
        return identity.external_id

    @staticmethod
    def _record_assessment(db: Session, patient_id: str, episode_id: str | None, safety: SafetyOutcome) -> None:
        from app.db.models import ClinicalAssessment
        db.add(ClinicalAssessment(
            patient_id=patient_id, episode_id=episode_id, pathway_name=safety.pathway_name,
            pathway_version=safety.pathway_version, outcome=safety.level,
            inputs={"matched_terms": safety.matched_terms},
        ))

    @staticmethod
    def _record_review_assessment(
        db: Session, patient_id: str, episode_id: str, review: ClinicalReviewOutcome, context_version: int
    ) -> None:
        """Persist explainable non-diagnostic review evidence for future audit/clinical review."""
        from app.db.models import ClinicalAssessment
        db.add(ClinicalAssessment(
            patient_id=patient_id,
            episode_id=episode_id,
            pathway_name=review.pathway_name,
            pathway_version=review.pathway_version,
            outcome=review.level,
            inputs={"priority": review.priority, "status": review.status,
                    "trigger_codes": review.trigger_codes, "reasons": review.reasons,
                    "dimensions": review.dimensions, "evidence": review.evidence},
            context_version=context_version,
        ))

    @staticmethod
    def _refresh_summary(db: Session, patient_id: str) -> None:
        patient = db.get(PatientProfile, patient_id)
        if patient is None:
            return
        patient.summary_version += 1
        episodes = db.scalars(select(HealthEpisode).where(
            HealthEpisode.patient_id == patient_id, HealthEpisode.status == "active"
        ).order_by(HealthEpisode.last_reported_at.desc()).limit(10)).all()
        content = {"active_episodes": [
            {"id": item.id, "symptom": item.primary_symptom, "summary": item.summary, "status": item.status}
            for item in episodes
        ]}
        db.add(PatientSummary(patient_id=patient_id, version=patient.summary_version, content=content, source_record_ids=[item.id for item in episodes]))

    async def _send_and_record(self, db: Session, patient_id: str, conversation_id: str, phone: str, text: str, message_type: str) -> None:
        provider_id = await self.whatsapp.send_text(phone, text)
        save_outgoing_message(db, patient_id, conversation_id, provider_id, text, message_type)
