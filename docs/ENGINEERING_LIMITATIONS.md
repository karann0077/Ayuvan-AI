> Historical v0.1.0 notes. For the expanded v0.2.0 project use `docs/V0.2_RELEASE_NOTES.md`, `reports/COVERAGE_REPORT.md` and `docs/CLINICAL_VALIDATION_PLAN_V0.2.md`.

# Current boundaries and next engineering tasks

## Intentionally NOT implemented

1. A medically validated, comprehensive emergency triage screen.
2. Natural-language symptom extraction with tested clinical negation, temporality, patient/other-person attribution and multilingual reliability. `symptoms.yaml` is a vocabulary seed, not a safe parser.
3. Full clinical pathways for 54 catalog diseases. There are five **symptom** pathway prototypes and one shared emergency draft, not disease-specific models for all entries.
4. Production auth, mobile/WhatsApp identity linking, authorization and access controls, privacy compliance, retention/deletion workflows, encrypted audit trail and notifications.
5. Full chronic disease management, specialist referral recommendations, dosing advice, appointments or diagnosis.
6. External guidelines auto-ingestion, coding-system licensing, clinical review dashboard, signed release registry or rollout/rollback deployment pipeline.
7. Clinically justified 0–100 priority scores, disease probabilities or safe production-ready P0–P4 thresholds.
8. Disease prediction from symptom associations. References and example rules do not establish probability.

## Important open hazards

- Clinical source-to-rule mismatch: several example cutoffs/urgency mappings are heuristic and need approval/replacement.
- Prototype `user_id` is request-controlled; never accept it for real protected records.
- Idempotency is demonstrated only for structured fact writes; production requires event-level deduplication and transactional assessment/question updates.
- Simultaneous observations or changing time zones need a clearly specified timeline-conflict resolution policy.
- `valid_until` is supported, but automatic expiration requires clinically reviewed fact-specific policies.
- The example emergency layer has limited patterns; even a non-match cannot be interpreted as absence of emergency.
- Prior disease history and medication information need explicit source and verification requirements.
- Caller-supplied pregnancy status must be verified where relevant; excluded populations need appropriate alternative routes.
- The Python package is not attached to your original FastAPI source code; integration adapters need to be implemented against your existing data models.

## Prioritized next milestones

1. Integrate an authenticated, medically reviewed intake and safety-screening flow into your existing FastAPI backend.
2. Build testable multilingual fact extraction with separate uncertainty/negation/duration benchmarks.
3. Complete the **adult cough India** pathway as a clinician-reviewed document, including all negative/boundary/longitudinal cases.
4. Finish appropriate chest/breathing and fever pathways; add emergency symptom screen coverage outside the five starter domains.
5. Use clinician-reviewed vignettes and independent evaluations, not only generated tests, to establish safety before release.
