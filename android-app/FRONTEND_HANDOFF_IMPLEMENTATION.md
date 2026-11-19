# AYUVAN Android frontend handoff

This implementation uses the supplied `AYUVAN_Frontend_Design_Handoff_v1.0 2` as a visual and navigation reference. The Android app remains Kotlin/Jetpack Compose and keeps its existing authenticated `/api/v1/mobile` calls. No backend schema or clinical logic was changed. See `HANDOFF_AUDIT_AND_MAPPING.md` for the screen-by-screen audit.

## Route migration

| Previous root | New location |
| --- | --- |
| Home | Home: one message composer and one real contextual action |
| Care Plan | My Care: tasks and optional personal reminder form |
| My Health | Records: timeline, medical profile, documents |
| Discover | Find care from Home; map and result list |
| Profile | Account from the Home or Records avatar |

The secondary Profile route now has focused Account, Settings, WhatsApp, Notifications, Privacy, and Help screens. The supplied leaf mark, landscape, icons, and illustrations replace the previous mixed icon styles.

Chat is a focused route without the bottom bar. A backend question with choices is shown as one large question with full-width answers and a typed alternative. Sending shows the user's message and an indeterminate waiting indicator immediately. The client keeps the same message ID for a safe retry after a network error, and chat scrolls to the latest content. It never fabricates an AI response while processing. Home can also upload a PDF or image through the existing API and then opens Records → Documents directly. Records can capture a new image with the camera.

Find care uses the existing backend's Google Places results. Results open in a list, with an in-app Google Maps SDK map available through the List/Map switch. The list works if location permission is declined. Precise coordinates remain on the device; only a city or area string is submitted for search. The app asks for location permission only when the user taps **Use my current location**. A selected facility opens a detail page; directions open in Google Maps.

The debug build's Maps SDK key is stored in ignored `maps.local.properties` and restricted to the app package and debug signing certificate. Other developers must supply their own restricted key in that file as `MAPS_API_KEY=...`. A release build needs a separate key restricted to its release certificate. Without a key, the facility list works and the map shows an unavailable message. Maps SDK and Places calls can incur Google Cloud charges.

The handoff's OTP flow was intentionally not adopted: AYUVAN currently uses phone and password, as requested for this project. Registration is now divided into credentials, profile, and consent screens. Screens that require missing backend contracts, such as medicine dose state, verified facility availability, and a structured clinical disposition, are not represented with invented data or clinical decisions.
