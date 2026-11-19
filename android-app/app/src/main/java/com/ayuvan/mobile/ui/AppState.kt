package com.ayuvan.mobile.ui

enum class MainTab(val label: String) {
    HOME("Home"),
    MY_HEALTH("Records"),
    CARE_PLAN("My Care"),
    DISCOVER("Discover"),
    PROFILE("Profile"),
}

enum class OnboardingStep {
    WELCOME,
    INTRO,
    PHONE,
    LANGUAGE,
    CONSENT,
    PROFILE,
    FAMILY,
    COMPLETE,
}

data class ChatMessage(
    val id: String,
    val text: String,
    val fromUser: Boolean,
    val kind: ChatMessageKind = ChatMessageKind.TEXT,
)

enum class ChatMessageKind { TEXT, QUESTION, SAFETY }

/**
 * Synthetic preview data is intentionally isolated from production data access.
 * Replace this object with authenticated repositories once the mobile API surface exists.
 */
object DemoAyuvanData {
    val activeConcernTitle = "Symptom concern"
    val activeConcernSubtitle = "Information gathering in progress"
    val careTasksDone = 2
    val careTasksTotal = 4
}
