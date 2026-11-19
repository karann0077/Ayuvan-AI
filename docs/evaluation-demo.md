# AYUVAN evaluation walkthrough

The demonstration account contains three **synthetic** profiles. None are real patients, clinicians, diagnoses or prescriptions. The emergency and routine outcomes are seeded examples for showing the interface; they are not evidence that the clinical engine has been validated.

## Install and sign in

1. Install the locally built `android-app/app/build/outputs/apk/debug/app-debug.apk` on the Android phone. Build artifacts are not committed to Git.
2. Open the ignored local file `.demo-evaluation-login.json` on the development laptop. Use its phone and password to sign in. Keep that file private. It is deliberately excluded from Git.
3. Open **Profile** to switch among the three `[DEMO]` profiles.

## Show the three stories

| Profile | Demonstration |
| --- | --- |
| `[DEMO] Urgent concern` | Open Home to see the urgent banner, then open the concern. The historical reports lead to a seeded emergency action screen with a 112 dialer and optional nearby emergency department search. Do not actually place a test emergency call. Records shows the dated symptom timeline. |
| `[DEMO] Routine concern` | Open Records to see a month of dated, improving mild reports. Open the conversation to show the normal, nonurgent example response. The care-navigation endpoint records no professional-care escalation for this synthetic scenario. |
| `[DEMO] Records and care` | Open Records to view the fictional PDF consultation note and its extraction record. Open My Care for a medicine reminder example, a follow-up consultation reminder and a completed past task. The follow-up is a reminder, not a booked appointment. |

The fake document contains no real drug name, dose or treatment instruction. Historical records are backdated. Pending reminders are scheduled for 21 November at 20:00 IST and 22 November at 10:00 IST when seeded on 20 November; use **My Care → Upcoming** to show them. Turn on **Notify me about due tasks** and grant Android notification permission if you want to test a local alert.

## Show the real WhatsApp and app link

The existing app account for the test recipient has a separate WhatsApp record. First send a fresh message to AYUVAN from that WhatsApp number. Then sign in to the app account, open **Profile → WhatsApp**, request a link code, wait for delivery status and enter the code. Only after successful verification will AYUVAN merge that WhatsApp patient's records into the app profile. Then **Records → Concern timeline** and **Conversation history** show both sources with channel labels. The synthetic demo account does not have a WhatsApp identity and cannot receive WhatsApp messages.

## Show nearby care

For the urgent demo, choose **Find nearby emergency care** after showing the 112 action. In **Find care**, tap **Use my current location**, grant location access, and select **Map**. Google Places returns current search results and the Android map renders pins. You can also enter a city and search manually. The map does not prove a doctor is available or that an appointment is booked; contact the facility to confirm. The approved backend action chooses emergency departments for emergency outcomes and a general physician as the starting point for nonemergency professional assessment. It does not use Gemini to invent a specialty or diagnosis.

## Recreate on another staging database

From the repository root, with `DATABASE_URL` pointing to the intended staging database:

```bash
.venv/bin/python -m scripts.seed_evaluation_demo --apply
```

The command refuses to alter an existing demo set and saves newly generated credentials in `.demo-evaluation-login.json` with mode `0600`. It never modifies existing patients or sends WhatsApp messages.

## Current boundaries

The Android APK builds and the live API paths were checked. No Android device or emulator was connected here, so the rendered screens and tap flow need a short on-device check before the evaluation. The handoff gaps recorded in `android-app/HANDOFF_AUDIT_AND_MAPPING.md` remain explicit; in particular there is no actual appointment booking, verified medication dosing schedule or clinician-approved specialist routing.
