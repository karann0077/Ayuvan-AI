# Clinical Validation and Release Acceptance Plan — v0.2.0

All checklist items are **open**. Automated software tests are not a substitute for clinical validation.

## Reference population and intended use

- [ ] Defined intended purpose, user, environment, legal/regulatory classification.
- [ ] Explicit eligible/unsupported groups: adult age range, pregnancy, immunocompromise, frailty, paediatrics, pregnancy-related emergencies, unreliable history.
- [ ] Review public-health localization (India NTEP/NCVBDC and variations in local services).
- [ ] Qualified clinical owner and independent clinical reviewer assigned to every release.

## Source and terminology

- [ ] Exact text/section/edition of the primary source recorded for every rule; source links alone are insufficient.
- [ ] All candidate disease-to-symptom associations reviewed and marked as typical/possible/asymptomatic with evidence where available.
- [ ] Clinical synonyms, Hindi, Hinglish, negation, attribution and temporal uncertainty tested with native language reviewers.
- [ ] Canonical SNOMED CT / ICD-11 identifiers assigned only under appropriate terminology/license review.

## Clinical rule safety

- [ ] Gold-standard scenarios independently labeled by multiple clinicians with disagreement resolution.
- [ ] Emergency criteria tested for no-delay overrides, false negatives, and uncertain inputs.
- [ ] P0 monitoring rules proven not to generate unsupported reassurance.
- [ ] P2/P3 referral timeframes documented, locally feasible and approved.
- [ ] Multi-symptom interactions, re-encounters, history contradictions and duplicate messages tested.
- [ ] Measured blood pressure/glucose/lab thresholds clinically validated including unit conversions, repeated readings and device measurement quality.
- [ ] Pregnancy and age ineligibility safely handled with appropriate alternative guidance.

## Evaluation methodology

- [ ] Prospective intended-user datasets and external clinician adjudication, not synthetic fixtures alone.
- [ ] Safety-critical performance limits and confidence intervals agreed before model evaluation.
- [ ] Emergency and non-emergency undertriage, overtriage, question burden and false reassurance separately measured.
- [ ] Stratification by age, language, comorbidity, region, literacy, sex/pregnancy relevance, and missing/contradictory facts.
- [ ] Failure analysis and remediation for every critical missed emergency case before release.
- [ ] Clinician-approved contraindication and emergency fallback information for unsupported features.

## Operations, governance and deployment

- [ ] Secure authenticated production API; never trust caller-provided user IDs.
- [ ] Privacy/consent requirements, encrypted audit, access control, retention and deletion controls signed off.
- [ ] Signed immutable approved pathway artifact and rollback/release attestation.
- [ ] Monitoring, incident response, human escalation and periodic revalidation installed.
- [ ] Indian medical software and data-protection legal review completed.

## Current report

`reports/COVERAGE_REPORT.md` and `reports/release_gate_v0.2.0.json` intentionally show zero completed clinical validation and a blocked release state.
