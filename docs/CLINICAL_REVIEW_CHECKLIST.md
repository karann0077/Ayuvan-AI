> Historical checklist from v0.1.0. The updated v0.2.0 plan is `docs/CLINICAL_VALIDATION_PLAN_V0.2.md` and the per-rule worksheet is `reports/rule_source_traceability_v0.2.0.csv`.

# AYUVAN clinical governance & release checklist

**Current approval state: NONE. ALL 6 pathway packages are engineering drafts.**

## 1. For each new clinical pathway version

- [ ] Named clinical owner, reviewers, independent validator and conflict-of-interest record.
- [ ] Intended medical purpose and jurisdiction documented and assessed under Indian requirements.
- [ ] Eligibility clearly defined: adult age cutoffs, pregnancy, immunosuppression, significant comorbidities, children and situations not safe to assess remotely.
- [ ] Vocabulary matches clinical concepts, including English, Hindi, Hinglish, spelling variants and explicit negations.
- [ ] Source mapped **to each individual rule**: citation, recommendation identifier, publication/revision date, local applicability and evidence uncertainty.
- [ ] Demonstrate no invented disease probabilities or unsupported diagnostic claims.
- [ ] All decision-table cutoffs, red flags, minimum urgencies, and timeframes reviewed by qualified clinicians.
- [ ] Missing/contradictory/stale answers reviewed; no silent assumption that unknown means absent.
- [ ] Emergency fallback and higher-priority overrides independently validated.
- [ ] Questions and button choices reviewed for comprehension and ability to change action.
- [ ] Approved response wording in each declared language; comprehension-tested with target population.
- [ ] Consent, privacy, follow-through schedule and transition to human care specified.
- [ ] Out-of-scope and safe-inconclusive outcomes tested, including previously resolved symptoms.
- [ ] Regression tests include boundary values, false positives/negatives, multi-symptom combinations, and real longitudinal cases.
- [ ] Signed approval and immutable release manifest; staged rollout and rollback procedure.

## 2. Rule-by-rule evidence limitations to resolve

| Pathway/rule examples | Evidence relationship | Required before approval |
|---|---|---|
| `COUGH_PERSISTENT_NTEP` | NTEP explicitly identifies cough lasting **more than two weeks** for presumptive pulmonary TB evaluation | Confirm the latest India NTEP threshold, exact interpretation, and appropriate assessment timeframe |
| `COUGH_MILD_BRIEF` | NICE discusses usually self-limiting acute cough; 3-day P0 threshold is **prototype-specific**, not a NICE-approved triage cutoff | Review low-acuity requirements, risk modifiers and appropriate safety-net conditions |
| `FEVER_PERSIST_AND_WORSEN` | Four-day cutoff is a **draft heuristic**; WHO SMART is an implementation framework, not a fever triage protocol | Replace with reviewed fever-specific national guidance |
| `FEVER_BLEEDING_RASH` | WHO dengue literature documents serious bleeding features; not all fever/rash presentations are dengue | Determine case definition, locality, season and validated escalation pathway |
| `ABDOMEN_MILD_BRIEF` | NHS general abdominal information does not validate a 1-day universal low-acuity rule | Review location, age, surgical risk and serious alternate diagnoses |
| `CHEST_UNEXPLAINED` | NICE CG95 supports assessing chest symptoms and signs of ACS, but the catch-all P3 mapping is prototype-specific | Build separate ACS/non-ACS pathways with reviewed time windows and differential safety checks |
| `METAB_THIRST_URINATION` | CDC lists classic diabetes symptoms; this combination does not diagnose diabetes | Define validated assessment advice and appropriate clinical test referral behavior |
| `EMERG_*` | Selected NHS/NICE/CDC warning signs; package is **not** a complete emergency triage system | Complete and validate cross-cutting emergency coverage for India, multiple languages and vulnerable groups |

## 3. Benchmark metrics before patient-facing use

Agree **clinician-defined acceptability thresholds** for emergency undertriage, non-emergency undertriage, overtriage, question relevance, question burden, false reassurance, multilingual accuracy, long-history continuity error, and time to appropriate recommended action. No arbitrary pass threshold should be presented as medically validated.

Separate retrospective training/dev scenarios from held-out real-world clinician-annotated scenarios. Test age, sex, social context, region, pregnancy, Hindi/Hinglish and other target languages. Record sign-off, date, rule version, model version, knowledge-source date, deployment cohort and post-release incident reporting.

## 4. Relevant sources

- NTEP diagnostic algorithm: https://www.ntep.in/node/1743/CP-diagnostic-algorithm-tb-disease-ntep
- WHO SMART Guidelines: https://smart.who.int/
- NICE acute cough: https://www.nice.org.uk/guidance/ng120/chapter/recommendations
- NICE chest pain: https://www.nice.org.uk/guidance/cg95/chapter/recommendations
- WHO dengue: https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue
- CDC diabetes: https://www.cdc.gov/diabetes/signs-symptoms/
- CDSCO Medical Device Software 2026 guidance: https://www.cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Guidance-document-on-Medical-Device-Software-under-MDR-2017.pdf
