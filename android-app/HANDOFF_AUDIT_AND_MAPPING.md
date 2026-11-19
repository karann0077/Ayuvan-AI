# AYUVAN frontend handoff audit and screen mapping

The source is `/Users/DELL/Downloads/AYUVAN_Frontend_Design_Handoff_v1.0 2/`. The package has 316 manifest entries (all SHA-256 and sizes verified), plus its manifest and three macOS `.DS_Store` files. It includes 35 screen specs and prompts, 35 individual screen previews, three composite previews, 84 icon pairs (SVG/PNG), 11 illustration pairs, nine previous-screen references, three concept boards, seven JSON files, the interactive HTML/CSS/JS prototype, and 16 handoff documents. All 35 screens, icon and illustration contact sheets, old-screen references, and concept boards were inspected. All JSON and SVG files parse; both prototype JavaScript files pass `node --check`.

The visual authority is the individual screen previews and `docs/07_PAGE_BY_PAGE_SPECIFICATIONS.md`. Concept boards and example medical wording are not clinical authority. The app keeps the earlier product decision to use phone plus password instead of OTP. A later integration added cross-channel history, care navigation and coordinate-based facility search to the backend; it did not change the clinical engine.

| Handoff screens | Android implementation | Integration state |
| --- | --- | --- |
| S01–S03 startup, welcome, language | `AyuvanApp.kt` session bootstrap, welcome, language | Welcome and language redesigned; startup uses existing session check. Hinglish entry uses the English app interface until backend locale support exists. |
| S04–S05 account, consent | `PhoneScreen` | Phone/password registration and login, staged profile and consent. OTP in the handoff is superseded by the user's account requirement. |
| S06–S08 Home states | `ConnectedHomeScreen` | Branded landscape, one composer, attachment, voice dictation, one real concern/task card, three tabs. |
| S09–S12 concern and questions | `ConnectedChatScreen` | Live text intake, backend choices as full-width answer rows, send/wait/retry, typed alternative. The mobile API does not expose a structured fact-review step. |
| S13–S15 results and emergency | Backend outcome and care-navigation route | A typed emergency outcome opens a dedicated emergency action view with a 112 dialer. Timely assessment offers a general physician search; routine outcomes remain in the conversation. The UI does not infer urgency from free text. |
| S16 concern timeline | Records timeline and correction dialog | Real episodes, dates, patient correction; no fabricated continuity state. |
| S17–S18 Find Care | `ConnectedDiscoverScreen`, `CareMap` | City/PIN or consented coordinates drive live Google Places search; list, in-app map, detail and directions are connected. Call appears only if the provider returns a number. Place search cannot verify availability or book an appointment. |
| S19–S20 document upload/review | Records document route | Camera/file upload, original preview/download, extraction trigger, user review before facts enter record. Review remains a focused dialog because the API returns limited extracted fields. |
| S21 care-plan preview | No production route | Backend has no reviewed document-to-care-plan draft contract; no task is invented from OCR. |
| S22–S23 My Care | `ConnectedCareScreen` | Today/Upcoming/Completed, real task detail and completion, personal reminder edit/delete, notification consent. |
| S24 medicine schedule | No schedule route | Backend returns medicine records but no clinician-confirmed dose schedule; no dose buttons or times are guessed. |
| S25 barrier support | My Care task help | Reason selection and facility lookup; no unsupported financial or appointment promise. |
| S26–S29 Records | `ConnectedHealthScreen` | Search/filter timeline, health profile editing, document detail, user-approved summary sharing. Search and summary use only available record fields. |
| S30–S34 Profile/settings | `ConnectedProfileScreen` | Focused account, family, privacy, WhatsApp linking, notifications and help routes; existing authenticated actions retained. |
| S35 system states | Shared loading, empty and error UI | Calm empty states and visible request progress. Offline clinical result is never simulated. |

The Android debug build is verified with `gradle --offline --no-daemon assembleDebug`. Visual device screenshots still need a connected Android device or emulator, so pixel-for-pixel correspondence has not been proven. Clinical and privacy approvals described in the handoff remain separate release gates.
