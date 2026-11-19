# AYUVAN Android frontend handoff

This implementation uses the supplied `AYUVAN_Frontend_Design_Handoff_v1.0` as a visual and navigation reference. The Android app remains Kotlin/Jetpack Compose and keeps its existing authenticated `/api/v1/mobile` calls. No backend schema or clinical logic was changed.

## Route migration

| Previous root | New location |
| --- | --- |
| Home | Home: one message composer and one real contextual action |
| Care Plan | My Care: tasks and optional personal reminder form |
| My Health | Records: timeline, medical profile, documents |
| Discover | Find care from Home; map and result list |
| Profile | Account from the Home or Records avatar |

Chat is a focused route without the bottom bar. Sending shows the user's message and an indeterminate waiting indicator immediately. The client keeps the same message ID for a safe retry after a network error, and chat scrolls to the latest content. It never fabricates an AI response while processing. Home can also upload a PDF or image through the existing API and then opens Records → Documents directly.

Find care uses the existing backend's Google Places results. Those pins are shown on the Google Maps SDK map, and the list works if location permission is declined. Precise coordinates remain on the device; only a city or area string is submitted for search. The app asks for location permission only when the user taps **Use my current location**. Directions open in Google Maps.

The debug build's Maps SDK key is stored in ignored `maps.local.properties` and restricted to the app package and debug signing certificate. Other developers must supply their own restricted key in that file as `MAPS_API_KEY=...`. A release build needs a separate key restricted to its release certificate. Without a key, the facility list works and the map shows an unavailable message. Maps SDK and Places calls can incur Google Cloud charges.

The handoff's OTP flow was intentionally not adopted: AYUVAN currently uses phone and password, as requested for this project. Screens that require missing backend contracts, such as medicine dose state, verified facility availability, and clinician-approved guidance, remain outside this frontend update. The UI does not invent those data or clinical decisions.
