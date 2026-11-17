# AYUVAN v0.2.0 — Clinical Knowledge Research and Design Evidence

**Prepared 16 November 2026 | India | Evidence mapping stage | NOT medical advice or clinician-approved decision support**

## What was researched, what was not

This engineering research uses India-first public sources (ICMR Standard Treatment Workflows, NTEP) and reputable international resources (WHO SMART guidance, WHO disease fact sheets, NICE, NIDDK, CDC, ADA, NHS) as **candidate literature** for clinician review. It does **not** reproduce full copyrighted guideline content and does not claim that individual decision-table thresholds were fully reviewed from primary clinical documents. The disease-to-symptom links are *potential presentations*, not diagnostic features or conditional probabilities. In particular, ICMR's index of condition-specific treatment workflows does not establish endorsement of this software's individual rules.

### 1 — Respiratory medicine (10 entries)

- **Conditions:** common cold, acute respiratory infections, bronchitis, asthma, COPD, pneumonia, pulmonary TB, allergic rhinitis, influenza, chronic bronchitis.
- **High-value presenting problems:** cough, wheeze, dyspnoea, sore throat, nasal symptoms, sputum change, cough with blood, exertional breathlessness.
- **History dimensions:** onset, same episode vs resolved-recurred, cough duration, nocturnal patterns, progression, fever/weight loss/night sweats, respiratory diagnoses, smoking or smoke exposure, functional restriction.
- **India-specific branch:** NTEP describes *cough lasting more than two weeks* as a presumptive pulmonary TB identification criterion requiring evaluation. The criterion must be applied to a **confirmed continuous episode**, never simply to two separated chat mentions. It does not diagnose TB. See [NTEP diagnostic algorithm](https://www.ntep.in/node/1743/CP-diagnostic-algorithm-tb-disease-ntep).
- **Cross-setting contrast:** [NICE NG120 acute cough](https://www.nice.org.uk/guidance/ng120/chapter/Recommendations) notes that many uncomplicated acute coughs resolve over several weeks. The apparent contrast shows why India-specific TB public-health assessment and general self-limited cough advice must coexist without applying one universal duration rule.
- **Clinical gaps:** full severe asthma/COPD exacerbation assessment, pneumonia observation/measurement criteria, young-child illness, pregnancy, immunosuppression, respiratory therapy context, severity calibration, local referral timeframes and safe patient wording. The existing short-cough P0 prototype is not validated reassurance.

### 2 — Infectious diseases (12 entries)

- **Conditions:** dengue, malaria, enteric fever, chikungunya, influenza, COVID-19, TB, acute viral respiratory infection, infectious gastroenteritis, viral hepatitis, UTIs, intestinal parasitic infections.
- **High-value presenting problems:** fever, rigors/chills, headache, joint and body aches, rash, vomiting/diarrhoea, urinary symptoms, jaundice, night sweats.
- **Clinical facts to distinguish:** exposure to local outbreaks/travel and time window; fever onset and trajectory; rash/bleeding; oral intake; urine output; new neurologic changes; abdominal symptoms; pregnancy and chronic illness.
- **Dengue:** [WHO dengue overview](https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue) and [India NCVBDC 2023 clinical guideline](https://ncvbdc.mohfw.gov.in/Doc/National%20Guidelines%20for%20Clinical%20Management%20of%20Dengue%20Fever%202023.pdf) support a separate clinician-reviewed warning-sign pathway that accounts for deterioration including after a fever decreases. The draft fever/rash pathway is **not** a full dengue algorithm, and symptoms alone cannot diagnose dengue.
- **Other presentations:** [WHO typhoid](https://www.who.int/news-room/fact-sheets/detail/typhoid/), [CDC malaria](https://www.cdc.gov/malaria/symptoms/index.html), and [WHO chikungunya](https://www.who.int/news-room/fact-sheets/detail/Chikungunya) demonstrate overlapping febrile presentations with different diagnostic needs.
- **Clinical gaps:** malaria test/referral criteria, haemodynamic assessment, dehydration, dengue day-of-illness and investigation history, fever in children, fever during pregnancy, antimicrobial stewardship, locally verified pathogen testing and clinical urgency timeframes.

### 3 — Gastroenterology (11 entries)

- **Conditions:** GERD, gastritis, gastroenteritis, peptic ulcer disease, IBS, constipation, infectious diarrhoea, hemorrhoids, gallstones, metabolic dysfunction-associated steatotic liver disease, intestinal helminths.
- **High-value presenting problems:** abdominal pain (location, onset, intensity, progression), loose stools, vomiting, constipation, heartburn/regurgitation, bloating, rectal bleeding, jaundice, swallowing difficulty.
- **Key distinctions:** painless reflux-like symptoms can overlap with cardiac chest complaints; GI bleeding requires different handling from uncomplicated constipation; inability to keep fluids down matters differently from occasional nausea. Use shared emergency evaluation first. [NHS diarrhoea and vomiting](https://www.nhs.uk/symptoms/diarrhoea-and-vomiting/) provides background symptoms and urgent warning patterns, which must be localized.
- **Clinical gaps:** appendicitis and pregnancy-related pain are outside current specialty disease list but must not be missed; surgical abdomen, abdominal pain localization, true GI bleeding severity, liver failure and dysphagia pathways need clinical authoring. The prototype does not interpret blood tests or establish a diagnosis.

### 4 — Cardiology (11 entries)

- **Conditions:** hypertension, coronary/ischemic artery disease, angina, heart failure, arrhythmia, atrial fibrillation, valvular heart disease, peripheral arterial disease, rheumatic heart disease and dyslipidemia (risk factor).
- **High-value presenting problems:** chest discomfort/pressure, palpitations, fainting/near-syncope, leg swelling, exertional breathlessness, unusual leg pain on walking, recorded blood pressure.
- **Emergency distinctions:** some acute chest presentations require immediate emergency assessment according to [NICE CG95 chest pain guidance](https://www.nice.org.uk/guidance/cg95/chapter/recommendations). Rules must not infer 'heart attack' from symptom overlap or wait through long questionnaires when an emergency criterion is met.
- **Measurement-based conditions:** [WHO hypertension guidance](https://www.who.int/news-room/fact-sheets/detail/hypertension) notes that most patients have no symptoms. Hypertension and dyslipidemia require appropriately collected measurements and clinician interpretation, **not** a generic symptom probability score. No numerical BP threshold is automated in v0.2.0.
- **Clinical gaps:** complete acute coronary syndrome differential, clinically validated timing, missing ECG and device provenance, pregnancy, unusual symptom presentations, vital sign thresholds and specialist referral timelines.

### 5 — Endocrinology/metabolic medicine (10 entries)

- **Conditions:** type 2 and type 1 diabetes, hypo-/hyperthyroidism, obesity, metabolic syndrome, PCOS, goitre/thyroid nodules, gestational diabetes, prediabetes.
- **High-value presenting problems:** thirst/urination changes, weight changes, fatigue, heat/cold intolerance, menstrual concerns, hair/skin changes, neck swelling, documented lab abnormalities.
- **Acute safety considerations:** [ADA 2026 Standards of Care](https://diabetesjournals.org/care/issue/49/Supplement_1) discuss hyperglycaemic crises with symptoms such as vomiting, dehydration and mental status changes. v0.2.0 has limited emergency pattern examples but does **not** diagnose DKA or automatically interpret glucose/ketone results.
- **PCOS:** [WHO PCOS fact sheet](https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome) describes irregular menstrual patterns and other possible features. This is not enough for a self-diagnostic rule.
- **Hypothyroidism:** [NIDDK](https://www.niddk.nih.gov/health-information/endocrine-diseases/hypothyroidism) describes symptoms such as fatigue/cold intolerance that can overlap with other disorders. Abnormal thyroid tests require verified values, reference intervals, and professional evaluation.
- **Special populations:** gestational diabetes needs an obstetric screening and assessment workflow. **Pregnancy is excluded** from routine adult draft pathways; it is not handled by treating a pregnant user as a typical adult.
- **Clinical gaps:** validated numerical glucose/lipid/thyroid/BP/weight interpretation; unit handling, fasting status, laboratory intervals, screening schedules, medication status, chronic-disease severity, and pregnancy-specific assessment.

## Shared high-risk engine — emergency and unknown handling

- Emergency candidates are in `global_emergency` and evaluated before other pathways. Existing coverage is **not exhaustive**; absence of a match does not mean 'safe'.
- Each patient fact includes a reported state (`present`,`absent`,`unknown`,`contradictory`), timestamp, source and verification status. Negation and uncertain language must be independently tested before any LLM-to-fact production integration.
- On simultaneous symptoms, evaluate every relevant pathway and preserve the highest matched urgency; also return unresolved pathways and unmapped complaints.
- Historical facts are not evidence of current symptom presence by themselves. Active event and continuity assessment require explicit confirmation; source and observation timestamps matter.
- The patient-facing endpoint must remain disabled because these drafts have no clinician signoff, calibrated clinical evidence, independent external validation or finalized regulatory/security assessment.

## Evidence architecture and intellectual-property constraints

- The evidence registry points to source publishers; it is not a downloaded textbook, full guideline ingestion, or license to reproduce source content.
- ICD-11 and SNOMED CT coding fields are intentionally blank rather than populated with unverified codes. Use [WHO ICD API](https://icd.who.int/icdapi/) and [SNOMED India](https://www.snomed.org/members/india) with applicable license obligations and terminology review.
- WHO [SMART guidelines](https://smart.who.int/) and its Digital Adaptation Kits provide a useful separation of data, workflows, rules, and indicators. This design adopts the separation **without** claiming WHO approval.
- Before implementation in India, obtain intended-purpose / product classification review using [CDSCO medical-device-software guidance](https://www.cdsco.gov.in/opencms/export/sites/CDSCO_WEB/Pdf-documents/Guidance-document-on-Medical-Device-Software-under-MDR-2017.pdf), plus qualified legal/privacy assessment.

## Required clinical-research work before a release

1. For every candidate rule, identify exact source document, edition/date, applicable location, population, statement/excerpt reference, clinical review status and contraindications. `reports/rule_source_traceability_v0.2.0.csv` is the checklist.
2. Replace generic prototype rules and vague timeframes with medically governed decision tables authored or approved by clinicians. Include explicit exclusions and necessary follow-up questions.
3. Independently adjudicate a sufficiently large dataset of cases, especially complex longitudinal symptom histories and high-risk populations, across relevant Indian languages and regional contexts.
4. Verify multilingual terms in Hindi, Hinglish and expanded local languages with qualified reviewers; lexicon coverage is not safe free-text triage.
5. Record failure modes, emergency undertriage, missed routine referrals, false reassurance, overtriage, temporal errors, and special-population performance.
6. Complete independent regulatory, security, consent, retention, incident-response and operational audits before real patient use.
