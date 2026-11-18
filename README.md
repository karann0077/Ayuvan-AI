# AYUVAN Backend and Android App

AYUVAN Stage 1 is a modular FastAPI backend for the WhatsApp-based health-concern intake flow. It stores a longitudinal, source-traceable patient record in PostgreSQL, processes Meta Cloud API webhooks, asks persistent interactive follow-up questions, and uses Gemini only for validated language extraction—not clinical decisions.

## What is implemented

- Meta webhook verification and `X-Hub-Signature-256` verification.
- Idempotent incoming WhatsApp message persistence and outgoing message-status updates.
- Text, button/list reply, document, audio, image, video, and location normalisation.
- Official Cloud API sender for text, buttons, lists, and an optional pre-published WhatsApp Flow.
- Durable conversation state, including the active health episode and pending question.
- Relational models for users, identities, consent, conversations, messages, health episodes, symptom events, conditions, allergies, medicines, documents, assessments, summaries, care plans/tasks, media, and audit logs.
- User-reported symptom provenance, verification status, confidence, and source-message references.
- Relevant-context builder that selects active and potentially related episodes rather than sending a lifetime record to the LLM.
- Gemini structured extraction validated by Pydantic, with a preferred model and automatic fallback when capacity is unavailable.
- Controlled symptom question packs: relevant safety screen, severity, change over time, and functional impact. Gemini extracts stated facts; it does not invent medical questions or escalation rules.
- Deterministic starter safety gate and explainable longitudinal clinician-review signals. They record observable reasons such as persistence, worsening, functional impact, a related earlier episode, or relevant documented history. They never predict or name a disease.
- Alembic migration, isolated tests, and OpenAPI documentation.

## Deliberate Stage 1 boundaries

### Versioned pathway library (engineering simulation)

The supplied v0.2.0 pathway pack is integrated under `app/clinical/` and
`clinical/`. It includes 49 draft pathway IDs, a restricted rule grammar,
provenance-aware facts, version and content hashes, 143 engineering cases,
coverage reports, and a release gate. All pathways remain **draft and
clinically unvalidated**. The condition catalog is a routing aid, not a
diagnosis engine. The existing WhatsApp intake and patient replies do not use
these draft pathway decisions.

`GET /api/v1/pathways` and `GET /api/v1/coverage` expose read-only engineering
metadata. `POST /api/v1/assess` always returns 503. To use
`POST /api/v1/simulate` with synthetic data, set `ENVIRONMENT=development`,
`ENABLE_PATHWAY_SIMULATOR=true`, and a random `PATHWAY_SIMULATION_KEY` of at least
32 characters. Send it in `X-Ayuvan-Simulation-Key`. The simulator is disabled
in staging and production even with those settings. Do not expose it to the
Internet or submit identifiable patient information. The request's `user_id`
is only a developer label, not an authenticated identity.

`app/services/pathway_simulation.py` provides a read-only adapter for comparing
an existing episode against the draft engine in a developer session. It routes
only exact concept codes and leaves free-text duration, missing safety answers,
and unknown pregnancy status unresolved. It does not write an assessment or
send a message. For isolated runs, use the synthetic files in `examples/` and
the imported checks:

```bash
.venv/bin/python scripts/validate_pathways.py
.venv/bin/python -m pytest -q
```

The release gate is intentionally blocked. Before any patient-facing use,
qualified clinical reviewers must approve the pathway content and questions,
independent testing must evaluate clinical safety, and the product needs
authenticated identity, release controls, and appropriate regulatory review.


Voice transcription, embeddings/pgvector, and clinician-approved pathways remain extension points. Incoming WhatsApp media is identified and persisted as a source reference; mobile document uploads use a separate private Cloud Storage path with an explicit patient review step.

## Android mobile integration

The Android app now uses authenticated `/api/v1/mobile` endpoints rather than demo data. It supports phone and password accounts, Argon2id password hashes, revocable sessions, distinct family profiles, a verified WhatsApp history link, the shared symptom conversation engine, symptom corrections, editable health items, private document upload/download and review, care tasks, local reminder notifications, Google Places search, consent controls, data export and deletion. See [docs/mobile-app.md](docs/mobile-app.md) for deployment and testing.

Registration does not prove ownership of the phone number. The app cannot read a WhatsApp health history until a one-time code sent to that WhatsApp number is verified. Google Places requests run only through the backend and are capped per account and service-wide; they require a billed Places API (New) key. Android reminder notifications are scheduled on the device and may arrive around their due time.

The webhook uses FastAPI background tasks only for local single-process testing. On Cloud Run, set `USE_CLOUD_TASKS=true` so a saved incoming message is enqueued before the webhook acknowledges it. Cloud Tasks sends an authenticated request to `/api/v1/tasks/whatsapp`; failed processing receives a non-2xx response and is retried. A dedicated invoker service account and signed OIDC token protect that route. The ARQ worker remains an optional Redis-backed alternative when `USE_ARQ=true` outside Cloud Run.

Cloud Run needs `CLOUD_TASKS_PROJECT`, `CLOUD_TASKS_LOCATION`, `CLOUD_TASKS_QUEUE`, `CLOUD_TASKS_TARGET_URL` (the service URL without a path), and `CLOUD_TASKS_INVOKER_SERVICE_ACCOUNT`. Grant the runtime service account `roles/cloudtasks.enqueuer` on the queue and `roles/iam.serviceAccountUser` on the invoker service account. The Cloud Tasks service agent also needs `roles/iam.serviceAccountUser` on the invoker service account to mint OIDC tokens. Grant the invoker service account `roles/run.invoker` on the Cloud Run service. Use a queue in the same region, initially with one concurrent dispatch to preserve the demo conversation flow. Configure a Cloud Run request timeout at least as long as the task dispatch deadline.

Cloud Tasks provides at-least-once delivery. AYUVAN atomically claims each incoming message so duplicate task deliveries do not process it concurrently. A crash between sending a WhatsApp message and recording the provider response can still result in a duplicate reply on retry; a transactional outbound outbox is needed before treating this as exactly-once delivery.

## Guided intake and clinician-review boundary

### Draft symptom priority engine

The backend now records an inspectable draft `P0`–`P2` priority and a separate
`need_more_information` status after symptom intake. It asks for duration when
missing, seeks explicit confirmation before treating a later report as continuous,
and records a resolved episode separately from a new recurrence. An old similar
episode alone cannot establish persistence. A two-week *confirmed* cough can
raise a draft consultation signal based on India's NTEP criteria. Emergency
signals still override routine questioning; the LLM only extracts reported facts.

These labels are **software prototype states, not validated clinical triage**.
P3/P4 disposition mapping, special populations, multilingual safety screening,
exact consultation timeframes, and pathway approval remain necessary before
real-patient deployment. Every persisted review includes the rule version,
trigger codes, missing fields, relevant episode IDs and dimension values.

For standard WhatsApp messages, AYUVAN uses compact button/list questions and asks only the next missing field. The starter pathways cover headache/neurological, chest, respiratory, fever, abdominal/urinary/injury/general concerns; all currently fall back to the controlled core questions where a specialist pack has not been clinically approved.

Set `WHATSAPP_SYMPTOM_INTAKE_FLOW_ID` only after you create and publish an identically structured Flow in Meta. That Flow can collect several fields in one submission. Its screen should use only these stable IDs: `onset`, `duration`, `frequency`, `severity`, `progression`, `functional_impact`, `headache_warning_signs`, `chest_current_state`, `breathing_status`, and `associated_symptoms`. AYUVAN validates and stores only those returned fields; without the setting, it automatically uses buttons/lists.

The current review engine is intentionally a **draft clinical-content boundary**, not a diagnostic or disease-prediction system. It can recommend a timely clinician appointment and show the patient-reported reasons. Before real-patient use, a qualified clinician must approve each pathway, trigger, option, timing, and wording.

## Local setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
```

Populate `.env` only on your machine. It is ignored by Git. Use an encoded connection string if a PostgreSQL password contains reserved URL characters: `@` becomes `%40`.

Required values for a live Meta webhook:

```dotenv
DATABASE_URL=postgresql+psycopg://...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_ACCESS_TOKEN=...
META_APP_SECRET=...
WEBHOOK_VERIFY_TOKEN=<long-random-secret>
WHATSAPP_TEST_RECIPIENT=<digits-only-whatsapp-test-recipient>
TEST_USER_PHONE=<same-digits-only-number>
ALLOW_TEST_USER_AUTO_PROVISION=true
GEMINI_API_KEY=...
```

`ALLOW_TEST_USER_AUTO_PROVISION` is specifically for one configured test recipient. Keep it `false` for any public deployment; real users must be linked through an authenticated, consented onboarding flow.

Apply the schema and launch:

```bash
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
```

OpenAPI is at `http://127.0.0.1:8000/docs`; health check is at `http://127.0.0.1:8000/api/v1/health`.

## Meta test-number setup

1. In Meta for Developers, create/select an app with the WhatsApp product and use the developer-provided test phone number.
2. Add and verify your personal WhatsApp number as a test recipient.
3. Copy the test phone number ID and temporary access token to `.env`.
4. In **App settings → Basic**, copy the app secret into `META_APP_SECRET`.
5. Generate a random `WEBHOOK_VERIFY_TOKEN`; it is an AYUVAN secret, not a Meta-issued token.
6. Expose the local application through an HTTPS tunnel, for example:

   ```bash
   ngrok http 8000
   ```

7. In Meta **WhatsApp → Configuration**, set the callback URL to:

   ```text
   https://YOUR-TUNNEL-DOMAIN/api/v1/webhooks/whatsapp
   ```

   Enter the same verification token, then subscribe to `messages`.
8. Start a WhatsApp conversation from the verified personal number to the test number. Within the customer-service window, AYUVAN can return ordinary and interactive messages.

Never log raw webhooks or expose `.env`, database dumps, media files, or patient records in a tunnel dashboard.

### When a message gets no reply

A healthy `/health` endpoint or a verified callback does not prove outbound messaging works.
Check the public tunnel, signed webhook reception, incoming `Message.processing_status`, and
the WhatsApp access token separately. A Meta error `190` / subcode `463` means the access token
has expired; replace `WHATSAPP_ACCESS_TOKEN` and restart the API (and ARQ worker, if enabled).
Keep `WEBHOOK_VERIFY_TOKEN` unchanged. Failed outbound sends retain sanitized provider codes
in the incoming message's `metadata_json.processing_error` for investigation.

For the current macOS testing session, a Cloudflare quick tunnel is managed outside the terminal
by launchd under `com.ayuvan.testing-tunnel`. Inspect it with
`launchctl list com.ayuvan.testing-tunnel` and stop it after testing with
`launchctl remove com.ayuvan.testing-tunnel`. Its URL is still temporary and can change after a
restart; this is not permanent hosting or a login-start service. The laptop and API must remain
running, and a changed URL must be registered as Meta's callback again.

## Test flow

Use fictional data only:

1. Send: `I have a headache for five days`.
2. AYUVAN extracts the stated symptom and duration, then asks a compact warning-sign screen using a WhatsApp list.
3. Choose `No warning signs`, then select severity, whether it is improving/same/worse, and its effect on usual activities.
4. AYUVAN records a provenance-linked event for each response and closes with a scannable record, next step, and—when a draft review signal is met—the specific non-diagnostic reasons to arrange a clinician visit. It does not diagnose or prescribe.

The patient context builder makes the active episode and potentially relevant prior episodes available to extraction without claiming they have the same cause or merging them automatically. A message beginning with a new symptom report can interrupt an older free-text question, so it starts a new concern instead of being stored as the old answer.

## Tests

```bash
.venv/bin/pytest -q
```

Tests use an in-memory SQLite database and synthetic records; they do not call Meta, Gemini, Redis, or Supabase.

## Mobile-app readiness

The WhatsApp adapter writes through the same patient, episode, message, record, and care entities a mobile API will use. A future authenticated mobile route should call the domain services directly; it should not duplicate health-history logic or maintain a second conversation database.
