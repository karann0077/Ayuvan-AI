# AYUVAN pathway version and release policy

- `major.minor.patch` applies to the **clinical decision package**, not the backend version.
- PATCH: spelling or nonclinical text correction requiring clinician confirmation and response regression tests.
- MINOR: question changes, translation changes, new non-breaking rules, or addition of limited eligibility; needs complete clinical review.
- MAJOR: changed clinical scope, primary care action, medical thresholds, critical safety rules, or backwards-incompatible data schema; requires independent validation and regulatory assessment.
- Never edit the content of a previously shipped package in place. A cached patient decision stores `pathway_id`, `version`, `sha256`, source facts, and triggered rule.
- Draft → reviewed → approved → active → retired is the intended lifecycle. Currently the software schema only accepts `draft`, `approved`, and `retired`, and **every packaged pathway is draft**.
- Clinical review sign-off is not simply entering a text field. A real release system should attest a content digest using a trusted key or approved deployment process, store an immutable manifest, and allow rollback to last safe artifact.
- Create a subsequent draft with `python scripts/new_version.py adult_cough_in 0.3.0 --reason "Clinical logic changes under review"`.
- Always run `make test` and rerun independent clinician-labeled evaluations before activation.

## Assessment reproducibility

The simulator records pathway versions and SHA-256 digests. If `AYUVAN_AUDIT_DATABASE_URL` is set, it also writes a full **plaintext** structured input/output snapshot for local testing. This is unsuitable for actual patient health data without encryption, access controls, retention policies and consent governance.
