# AYUVAN Stage 1 Backend

AYUVAN Stage 1 is a modular FastAPI backend for the WhatsApp-based health-concern intake flow. It stores a longitudinal, source-traceable patient record in PostgreSQL, processes Meta Cloud API webhooks, asks persistent interactive follow-up questions, and uses Gemini only for validated language extraction—not clinical decisions.

## What is implemented

- Meta webhook verification and `X-Hub-Signature-256` verification.
- Idempotent incoming WhatsApp message persistence and outgoing message-status updates.
- Text, button/list reply, document, audio, image, video, and location normalisation.
- Official Cloud API sender for text, buttons, and list messages.
- Durable conversation state, including the active health episode and pending question.
- Relational models for users, identities, consent, conversations, messages, health episodes, symptom events, conditions, allergies, medicines, documents, assessments, summaries, care plans/tasks, media, and audit logs.
- User-reported symptom provenance, verification status, confidence, and source-message references.
- Relevant-context builder that selects active and potentially related episodes rather than sending a lifetime record to the LLM.
- Gemini structured extraction validated by Pydantic, with a conservative local fallback for development outages.
- Deterministic starter safety gate that short-circuits a small, explicitly documented emergency-keyword set before LLM processing. It is **not clinical decision support** and must receive clinical review before patient use.
- Alembic migration, isolated tests, and OpenAPI documentation.

## Deliberate Stage 1 boundaries

Voice transcription, document OCR/retrieval, embeddings/pgvector, authentication for the future mobile app, full consent onboarding, and clinician-approved pathways are extension points, not complete features yet. Incoming media is identified and persisted as a source reference, but it is not downloaded or interpreted.

The webhook uses FastAPI background tasks for the local single-process test flow. The same task is dispatched to ARQ when `USE_ARQ=true` and is exposed in `app/worker.py`; configure Redis and run `arq app.worker.WorkerSettings` for durable production processing.

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

## Test flow

Use fictional data only:

1. Send: `I have a headache for five days`.
2. AYUVAN stores the incoming message, creates a `HealthEpisode`, and asks when it began.
3. Reply: `Five days ago`.
4. AYUVAN stores a new provenance-linked `SymptomEvent` and asks frequency using reply buttons.
5. Choose an option. AYUVAN maps the stable reply ID—not the visible label—to the pending question and saves it.

The patient context builder then makes the active episode and potentially relevant prior episodes available to the extraction flow without claiming they have the same cause or merging them automatically.

## Tests

```bash
.venv/bin/pytest -q
```

Tests use an in-memory SQLite database and synthetic records; they do not call Meta, Gemini, Redis, or Supabase.

## Mobile-app readiness

The WhatsApp adapter writes through the same patient, episode, message, record, and care entities a mobile API will use. A future authenticated mobile route should call the domain services directly; it should not duplicate health-history logic or maintain a second conversation database.
