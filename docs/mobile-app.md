# AYUVAN mobile implementation

## Runtime

- Android app: `android-app/`, Jetpack Compose, min SDK 26. The debug APK is `android-app/app/build/outputs/apk/debug/app-debug.apk`.
- API URL: `BuildConfig.API_BASE_URL`, configured by Gradle property `ayuvanApiBaseUrl`; the default points to the AYUVAN Cloud Run staging service. Do not put API keys or database credentials in the APK.
- Backend: `/api/v1/mobile` on the existing FastAPI service. `alembic upgrade head` applies the mobile identity and access migration.
- Session: random bearer token, SHA-256 hash in PostgreSQL, 30-day expiry, server-side revocation; Android stores the token with AES-GCM in Android Keystore.
- Password: Argon2id. Login locks a credential after five failed attempts for 15 minutes.
- Account boundary: registration creates a new profile. A WhatsApp patient is linked only after a six-digit code sent to the same WhatsApp number is verified. A family member has a separate patient profile. Every patient-scoped route checks `PatientAccess`.

## Features and data flow

| App area | Backend behavior |
| --- | --- |
| Account | Register, login, session restore, profile update, password change, family creation with caregiver attestation, logout, account deletion |
| Symptom chat | Mobile messages use the existing extraction, question, safety and review engine; mobile and WhatsApp conversations remain separate channels but share the selected patient's longitudinal record |
| My Health | Episodes and corrections, conditions, allergies, medicines, health summary and medical records |
| Documents | Private Google Cloud Storage upload/download; Gemini extraction is an unverified draft; only patient-selected facts are added to the record |
| Care Plan | Patient-created tasks can be added, edited, completed and deleted. Android WorkManager schedules one-time local notifications when consent and OS permission are granted |
| Discover | Backend-only Places API (New) Text Search, explicit area input, Google Maps attribution and links that open the map; 40 search attempts per account and 100 total attempts per rolling day, with a five-second per-account cooldown |
| Profile | Purpose-specific consent, verified WhatsApp link, complete JSON export, individual document deletion, linked WhatsApp record deletion and account-owned data deletion |

## Cloud configuration

`MEDICAL_DOCUMENTS_BUCKET` must name a private bucket with public access prevention and uniform bucket-level access. The Cloud Run runtime service account needs `roles/storage.objectUser` on that bucket. `GOOGLE_PLACES_API_KEY` must be a Secret Manager reference to a key restricted to `places.googleapis.com`; the runtime service account needs Secret Manager accessor. Google Places API requires a billing account and can incur charges. Configure a project-level quota and budget alert in Google Cloud for additional cost protection.

The existing `DATABASE_URL`, `GEMINI_API_KEY`, WhatsApp credentials and Cloud Tasks settings remain required for the respective features. Document and symptom AI actions require the patient's `ai_assistance` consent. Health-data writes require `health_processing` consent. Data export and deletion remain available after consent withdrawal.

## Build and checks

From the repository root:

```bash
.venv/bin/alembic upgrade head
.venv/bin/python -m pytest -q
cd android-app
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home \
ANDROID_HOME=/opt/homebrew/share/android-commandlinetools \
bash .local-gradle/gradle-9.6.0/bin/gradle --no-daemon assembleDebug
```

The local `.local-gradle/` directory is build tooling, excluded from Git and Cloud Run source uploads. The `android-app/gradle-9.6.0-bin.zip` copy is also excluded.

## Release boundary

This is a staging/demo integration. The symptom review pathways remain draft and require qualified clinical approval before patient-facing release. WorkManager reminders are one-time and inexact; they should not be relied on for time-critical medication dosing. Account registration intentionally does not claim that a phone number has been verified; WhatsApp history requires separate verification. Production use also needs operational monitoring, abuse controls, secure backup and deletion verification, and a clinician-reviewed safety release process.
