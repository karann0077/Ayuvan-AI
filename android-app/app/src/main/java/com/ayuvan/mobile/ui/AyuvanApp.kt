@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.ayuvan.mobile.ui

import android.content.Intent
import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.pdf.PdfRenderer
import android.net.Uri
import android.os.Build
import android.os.ParcelFileDescriptor
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.BackHandler
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material.icons.filled.WarningAmber
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.FilledIconButton
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.IconButtonDefaults
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.google.android.gms.maps.model.LatLng
import com.ayuvan.mobile.R
import com.ayuvan.mobile.data.MobileApi
import com.ayuvan.mobile.data.ReminderScheduler
import kotlinx.coroutines.launch
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import androidx.compose.runtime.rememberCoroutineScope

@Composable
fun AyuvanApp() {
    val context = LocalContext.current
    val api = remember { MobileApi(context.applicationContext) }
    var sessionChecked by remember { mutableStateOf(false) }
    var patients by remember { mutableStateOf(JSONArray()) }
    var selectedPatientId by rememberSaveable { mutableStateOf("") }
    var stepName by rememberSaveable { mutableStateOf(OnboardingStep.WELCOME.name) }
    var finishedOnboarding by remember { mutableStateOf(false) }
    var tabName by rememberSaveable { mutableStateOf(MainTab.HOME.name) }
    var recordsEntry by rememberSaveable { mutableStateOf("Timeline") }
    var showChat by rememberSaveable { mutableStateOf(false) }
    var chatSeed by rememberSaveable { mutableStateOf("") }
    val selectedPatient = patients.rows().firstOrNull { it.optString("id") == selectedPatientId }
        ?.optString("display_name") ?: "My Profile"

    val onboardingStep = OnboardingStep.valueOf(stepName)
    val selectedTab = MainTab.valueOf(tabName)
    BackHandler(enabled = showChat || selectedTab == MainTab.DISCOVER || selectedTab == MainTab.PROFILE) {
        if (showChat) showChat = false else tabName = MainTab.HOME.name
    }

    suspend fun refreshAccount() {
        val account = api.me()
        patients = account.optJSONArray("patients") ?: JSONArray()
        if ((0 until patients.length()).none { patients.optJSONObject(it)?.optString("id") == selectedPatientId }) {
            selectedPatientId = patients.optJSONObject(0)?.optString("id") ?: ""
        }
        finishedOnboarding = true
    }

    LaunchedEffect(Unit) {
        if (api.hasSession()) runCatching { refreshAccount() }.onFailure { api.clearSession() }
        sessionChecked = true
    }

    Surface(modifier = Modifier.fillMaxSize(), color = AyuvanColors.Page) {
        if (!sessionChecked) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        } else if (!finishedOnboarding) {
            OnboardingFlow(
                step = onboardingStep,
                onStepChange = { stepName = it.name },
                api = api,
                onComplete = { account ->
                    patients = account.optJSONArray("patients") ?: JSONArray().put(account.optJSONObject("patient"))
                    selectedPatientId = patients.optJSONObject(0)?.optString("id") ?: ""
                    finishedOnboarding = true
                },
            )
        } else if (showChat) {
            ConnectedChatScreen(
                patientName = selectedPatient,
                patientId = selectedPatientId,
                api = api,
                initialMessage = chatSeed,
                onInitialConsumed = { chatSeed = "" },
                onBack = { showChat = false },
            )
        } else {
            MainShell(
                api = api,
                patientId = selectedPatientId,
                patients = patients,
                selectedTab = selectedTab,
                recordsEntry = recordsEntry,
                selectedPatient = selectedPatient,
                onPatientChange = { id -> selectedPatientId = id },
                onPatientsRefresh = { refreshed -> patients = refreshed },
                onSignOut = {
                    ReminderScheduler.cancelAll(context)
                    api.clearSession()
                    finishedOnboarding = false
                    stepName = OnboardingStep.WELCOME.name
                },
                onTabChange = { tabName = it.name },
                onOpenChat = { text -> chatSeed = text; showChat = true },
                onOpenDocuments = { recordsEntry = "Documents"; tabName = MainTab.MY_HEALTH.name },
            )
        }
    }
}

@Composable
private fun OnboardingFlow(
    step: OnboardingStep,
    onStepChange: (OnboardingStep) -> Unit,
    api: MobileApi,
    onComplete: (JSONObject) -> Unit,
) {
    when (step) {
        OnboardingStep.WELCOME -> WelcomeScreen(
            onStart = { onStepChange(OnboardingStep.INTRO) },
            onExistingAccount = { onStepChange(OnboardingStep.PHONE) },
        )
        OnboardingStep.INTRO -> IntroductionScreen(onNext = { onStepChange(OnboardingStep.PHONE) })
        else -> PhoneScreen(api = api, onAuthenticated = onComplete)
    }
}

@Composable
private fun OnboardingBackground(content: @Composable () -> Unit) {
    Box(modifier = Modifier.fillMaxSize()) {
        Image(
            painter = painterResource(R.drawable.bg_onboarding_misty_hills),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop,
            alpha = 0.88f,
        )
        content()
    }
}

@Composable
private fun WelcomeScreen(onStart: () -> Unit, onExistingAccount: () -> Unit) {
    OnboardingBackground {
        Column(
            modifier = Modifier.fillMaxSize().padding(horizontal = 28.dp, vertical = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Spacer(Modifier.height(30.dp))
            Image(
                painter = painterResource(R.drawable.ayuvan_logo_horizontal),
                contentDescription = "AYUVAN",
                modifier = Modifier.width(156.dp).height(48.dp),
                contentScale = ContentScale.Fit,
            )
            Spacer(Modifier.weight(0.42f))
            Image(
                painter = painterResource(R.drawable.welcome_hero),
                contentDescription = null,
                modifier = Modifier.fillMaxWidth().heightIn(max = 290.dp),
                contentScale = ContentScale.Fit,
            )
            Text("Your health, all in one place.", style = MaterialTheme.typography.displaySmall, textAlign = TextAlign.Center)
            Spacer(Modifier.height(12.dp))
            Text(
                "Understand your health, organise medical information and keep your next steps within reach.",
                style = MaterialTheme.typography.bodyLarge,
                color = AyuvanColors.SecondaryText,
                textAlign = TextAlign.Center,
            )
            Spacer(Modifier.weight(0.5f))
            PrimaryButton("Get started", onStart)
            TextButton(onClick = onExistingAccount) { Text("I already have an account") }
        }
    }
}

@Composable
private fun IntroductionScreen(onNext: () -> Unit) {
    OnboardingBackground {
        Column(
            modifier = Modifier.fillMaxSize().padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            BrandMark()
            Spacer(Modifier.height(28.dp))
            Image(
                painter = painterResource(R.drawable.onboarding_health_guidance),
                contentDescription = null,
                modifier = Modifier.size(220.dp),
            )
            Text("Complete health in one place", style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center)
            Spacer(Modifier.height(22.dp))
            listOf(
                "Track your health and medical records",
                "Get AI-assisted health guidance",
                "Follow your care plan with reminders",
                "Find nearby healthcare options",
            ).forEach { item -> BenefitRow(item) }
            Spacer(Modifier.weight(1f))
            Text("●  ●  ●  ●", color = AyuvanColors.Brand500, letterSpacing = 4.sp)
            Spacer(Modifier.height(18.dp))
            PrimaryButton("Continue", onNext)
        }
    }
}

@Composable
private fun PhoneScreen(api: MobileApi, onAuthenticated: (JSONObject) -> Unit) {
    var phone by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var name by rememberSaveable { mutableStateOf("") }
    var birthDate by rememberSaveable { mutableStateOf("") }
    var sex by rememberSaveable { mutableStateOf("") }
    var language by rememberSaveable { mutableStateOf("en") }
    var consent by rememberSaveable { mutableStateOf(false) }
    var aiConsent by rememberSaveable { mutableStateOf(false) }
    var registering by rememberSaveable { mutableStateOf(false) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    OnboardingBackground {
        Column(
            modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            BrandMark()
            Spacer(Modifier.height(28.dp))
            Text(if (registering) "Create your account" else "Sign in to continue", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(8.dp))
            Text("Use your mobile number and password.", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText, textAlign = TextAlign.Center)
            Spacer(Modifier.height(22.dp))
            OutlinedTextField(
                value = phone,
                onValueChange = { phone = it.filter(Char::isDigit).take(10) },
                modifier = Modifier.fillMaxWidth(),
                leadingIcon = { Icon(Icons.Default.Phone, null, tint = AyuvanColors.Brand700) },
                prefix = { Text("+91  ") },
                label = { Text("Mobile number") },
                placeholder = { Text("Enter your mobile number") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                singleLine = true,
            )
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(value = password, onValueChange = { password = it },
                modifier = Modifier.fillMaxWidth(), label = { Text("Password") },
                visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password), singleLine = true)
            if (registering) {
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(value = name, onValueChange = { name = it.take(160) },
                    modifier = Modifier.fillMaxWidth(), label = { Text("Full name") }, singleLine = true)
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(value = birthDate, onValueChange = { birthDate = it.take(10) },
                    modifier = Modifier.fillMaxWidth(), label = { Text("Date of birth (optional, YYYY-MM-DD)") }, singleLine = true)
                Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("Woman" to "woman", "Man" to "man", "Other" to "other",
                        "Prefer not to say" to "prefer_not_to_say").forEach { (label, code) ->
                        AssistChip(onClick = { sex = code }, label = { Text(label) },
                            leadingIcon = if (sex == code) ({ Icon(Icons.Default.Check, null) }) else null)
                    }
                }
                Spacer(Modifier.height(14.dp))
                Text("Preferred language", modifier = Modifier.fillMaxWidth(), style = MaterialTheme.typography.labelLarge)
                Row(modifier = Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("English" to "en", "हिंदी" to "hi", "मराठी" to "mr", "தமிழ்" to "ta").forEach { (label, code) ->
                        AssistChip(onClick = { language = code }, label = { Text(label) },
                            leadingIcon = if (language == code) ({ Icon(Icons.Default.Check, null) }) else null)
                    }
                }
                Row(modifier = Modifier.fillMaxWidth().clickable { consent = !consent }, verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = consent, onCheckedChange = { consent = it })
                    Text("I agree to the Terms, Privacy Policy and processing my health data.", style = MaterialTheme.typography.bodyMedium)
                }
                Row(modifier = Modifier.fillMaxWidth().clickable { aiConsent = !aiConsent }, verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = aiConsent, onCheckedChange = { aiConsent = it })
                    Text("Use AI assistance for symptom chat and document extraction.", style = MaterialTheme.typography.bodyMedium)
                }
            }
            if (error != null) Text(error!!, color = AyuvanColors.Danger, modifier = Modifier.padding(top = 10.dp))
            Spacer(Modifier.height(24.dp))
            PrimaryButton(if (registering) "Create account" else "Sign in", enabled = !busy && phone.length == 10 && password.length >= (if (registering) 10 else 1) && (!registering || (name.trim().length >= 2 && consent)), onClick = {
                scope.launch {
                    busy = true; error = null
                    try {
                        val account = if (registering) api.register(phone, password, name.trim(), language,
                            consent, aiConsent, birthDate.ifBlank { null }, sex.ifBlank { null })
                            else api.login(phone, password)
                        onAuthenticated(account)
                    } catch (e: Exception) { error = e.message ?: "Could not connect" }
                    busy = false
                }
            })
            TextButton(onClick = { registering = !registering; error = null }) {
                Text(if (registering) "Already have an account? Sign in" else "New to AYUVAN? Create an account")
            }
        }
    }
}

@Composable
private fun LanguageScreen(onNext: () -> Unit) {
    var choice by rememberSaveable { mutableStateOf("English") }
    OnboardingBackground {
        Column(modifier = Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            BrandMark()
            Spacer(Modifier.height(42.dp))
            Text("Which language feels most comfortable?", style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center)
            Spacer(Modifier.height(8.dp))
            Text("You can change this anytime in Preferences.", color = AyuvanColors.SecondaryText, textAlign = TextAlign.Center)
            Spacer(Modifier.height(28.dp))
            listOf("English", "हिंदी", "मराठी", "தமிழ்").forEach { language ->
                SelectableRow(text = language, selected = language == choice, onClick = { choice = language })
                Spacer(Modifier.height(10.dp))
            }
            Spacer(Modifier.weight(1f))
            PrimaryButton("Continue", onNext)
        }
    }
}

@Composable
private fun ConsentScreen(onNext: () -> Unit) {
    var consent by rememberSaveable { mutableStateOf(false) }
    OnboardingBackground {
        Column(modifier = Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            BrandMark()
            Spacer(Modifier.height(36.dp))
            IconBadge(icon = Icons.Default.Check, contentDescription = null, large = true)
            Spacer(Modifier.height(18.dp))
            Text("Your privacy, our priority", style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center)
            Spacer(Modifier.height(12.dp))
            Text("Your health information is used to support the features you choose. You stay in control.", textAlign = TextAlign.Center, color = AyuvanColors.SecondaryText)
            Spacer(Modifier.height(24.dp))
            listOf("Private account and patient profiles", "Clear choices for AI-assisted features", "Manage or withdraw optional permissions").forEach { BenefitRow(it) }
            Spacer(Modifier.height(18.dp))
            Row(modifier = Modifier.fillMaxWidth().clickable { consent = !consent }, verticalAlignment = Alignment.CenterVertically) {
                SelectionDot(selected = consent)
                Spacer(Modifier.width(10.dp))
                Text("I agree to the Terms of Service and Privacy Policy", style = MaterialTheme.typography.bodyMedium)
            }
            Spacer(Modifier.weight(1f))
            PrimaryButton("Continue", enabled = consent, onClick = onNext)
        }
    }
}

@Composable
private fun ProfileSetupScreen(onNext: () -> Unit) {
    var name by rememberSaveable { mutableStateOf("") }
    var birthDate by rememberSaveable { mutableStateOf("") }
    OnboardingBackground {
        Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            BrandMark()
            Spacer(Modifier.height(28.dp))
            Text("Let's create your health profile", style = MaterialTheme.typography.headlineMedium, textAlign = TextAlign.Center)
            Text("Share the basics you are comfortable adding today.", color = AyuvanColors.SecondaryText, textAlign = TextAlign.Center)
            Spacer(Modifier.height(24.dp))
            OutlinedTextField(value = name, onValueChange = { name = it }, modifier = Modifier.fillMaxWidth(), label = { Text("Full name") }, placeholder = { Text("Enter your name") }, singleLine = true)
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(value = birthDate, onValueChange = { birthDate = it }, modifier = Modifier.fillMaxWidth(), label = { Text("Date of birth") }, placeholder = { Text("DD / MM / YYYY") }, singleLine = true)
            Spacer(Modifier.height(18.dp))
            Text("Gender", modifier = Modifier.fillMaxWidth(), style = MaterialTheme.typography.labelLarge)
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Woman", "Man", "Prefer not to say").forEach { label -> AssistChip(onClick = {}, label = { Text(label) }) }
            }
            Spacer(Modifier.height(28.dp))
            Text("Health background is optional and can be added from My Health later.", color = AyuvanColors.MutedText, style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(28.dp))
            PrimaryButton("Continue", enabled = name.isNotBlank(), onClick = onNext)
        }
    }
}

@Composable
private fun FamilyScreen(onNext: () -> Unit) {
    var selected by rememberSaveable { mutableStateOf("Myself") }
    OnboardingBackground {
        Column(modifier = Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            BrandMark()
            Spacer(Modifier.height(35.dp))
            Text("Add your family", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(8.dp))
            Text("Family profiles are optional and always have separate health information.", color = AyuvanColors.SecondaryText, textAlign = TextAlign.Center)
            Spacer(Modifier.height(24.dp))
            listOf("Myself", "Child", "Parent", "Spouse / Partner").forEach { item ->
                SelectableRow(text = item, selected = selected == item, onClick = { selected = item })
                Spacer(Modifier.height(10.dp))
            }
            Spacer(Modifier.weight(1f))
            PrimaryButton("Continue", onNext)
            TextButton(onClick = onNext) { Text("Skip for now") }
        }
    }
}

@Composable
private fun SetupCompleteScreen(onComplete: () -> Unit) {
    OnboardingBackground {
        Column(modifier = Modifier.fillMaxSize().padding(28.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Image(painter = painterResource(R.drawable.ayuvan_app_icon), contentDescription = null, modifier = Modifier.size(126.dp))
            Spacer(Modifier.height(26.dp))
            Text("You're all set.", style = MaterialTheme.typography.displaySmall)
            Spacer(Modifier.height(10.dp))
            Text("AYUVAN is ready to help you organise your health information and next steps.", textAlign = TextAlign.Center, color = AyuvanColors.SecondaryText)
            Spacer(Modifier.height(34.dp))
            PrimaryButton("Go to Home", onComplete)
        }
    }
}

@Composable
private fun MainShell(
    api: MobileApi,
    patientId: String,
    patients: JSONArray,
    selectedTab: MainTab,
    recordsEntry: String,
    selectedPatient: String,
    onPatientChange: (String) -> Unit,
    onPatientsRefresh: (JSONArray) -> Unit,
    onSignOut: () -> Unit,
    onTabChange: (MainTab) -> Unit,
    onOpenChat: (String) -> Unit,
    onOpenDocuments: () -> Unit,
) {
    Scaffold(
        containerColor = AyuvanColors.Page,
        bottomBar = { if (selectedTab in listOf(MainTab.HOME, MainTab.CARE_PLAN, MainTab.MY_HEALTH))
            MainNavigation(selectedTab, onTabChange) },
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize().padding(innerPadding)) {
            when (selectedTab) {
                MainTab.HOME -> ConnectedHomeScreen(api, patientId, selectedPatient, onOpenChat, onOpenDocuments, onTabChange)
                MainTab.MY_HEALTH -> ConnectedHealthScreen(api, patientId, patients, onPatientChange, onPatientsRefresh,
                    initialSection = recordsEntry, onProfile = { onTabChange(MainTab.PROFILE) })
                MainTab.CARE_PLAN -> ConnectedCareScreen(api, patientId)
                MainTab.DISCOVER -> ConnectedDiscoverScreen(api, onBack = { onTabChange(MainTab.HOME) })
                MainTab.PROFILE -> ConnectedProfileScreen(api, patientId, patients, onPatientChange, onPatientsRefresh, onSignOut,
                    onBack = { onTabChange(MainTab.HOME) })
            }
        }
    }
}

@Composable
private fun MainNavigation(selected: MainTab, onSelect: (MainTab) -> Unit) {
    NavigationBar(containerColor = Color.White, tonalElevation = 2.dp) {
        listOf(MainTab.HOME, MainTab.CARE_PLAN, MainTab.MY_HEALTH).forEach { tab ->
            NavigationBarItem(
                selected = tab == selected,
                onClick = { onSelect(tab) },
                icon = { AssetIcon(tabIcon(tab), tab.label, Modifier.size(25.dp)) },
                label = { Text(tab.label, maxLines = 1, fontSize = 12.sp) },
            )
        }
    }
}

private fun tabIcon(tab: MainTab) = when (tab) {
    MainTab.HOME -> R.drawable.handoff_home
    MainTab.MY_HEALTH -> R.drawable.handoff_folder
    MainTab.CARE_PLAN -> R.drawable.handoff_calendar
    MainTab.DISCOVER -> R.drawable.handoff_map_pin
    MainTab.PROFILE -> R.drawable.icon_profile
}

@Composable
private fun HomeScreen(patientName: String, onOpenChat: () -> Unit, onTabChange: (MainTab) -> Unit) {
    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Box(modifier = Modifier.fillMaxWidth().height(228.dp)) {
            Image(painter = painterResource(R.drawable.bg_header_misty_hills), contentDescription = null, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            Column(modifier = Modifier.fillMaxSize().padding(horizontal = 20.dp, vertical = 16.dp)) {
                AppHeader()
                Spacer(Modifier.height(24.dp))
                Text("Good morning,", style = MaterialTheme.typography.headlineMedium)
                Text(patientName, style = MaterialTheme.typography.headlineMedium)
                Text("Your personal health companion", style = MaterialTheme.typography.bodyLarge, color = AyuvanColors.SecondaryText)
            }
        }
        Column(modifier = Modifier.padding(horizontal = 20.dp).padding(bottom = 30.dp)) {
            TalkToAyuvanCard(onOpenChat)
            Spacer(Modifier.height(20.dp))
            QuickActionGrid(onTabChange)
            Spacer(Modifier.height(28.dp))
            SectionTitle("Your Health at a Glance", action = "View all")
            CarePlanProgressCard()
            Spacer(Modifier.height(26.dp))
            SectionTitle("Active health concerns")
            ActiveConcernCard(onOpenChat)
            Spacer(Modifier.height(26.dp))
            SectionTitle("Upcoming reminders", action = "View all")
            ReminderCard()
        }
    }
}

@Composable
private fun AppHeader(onNotifications: () -> Unit = {}, showNotificationButton: Boolean = false,
                      hasReminder: Boolean = false, onProfile: (() -> Unit)? = null) {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Image(painterResource(R.drawable.handoff_leaf), null, Modifier.size(28.dp))
        Spacer(Modifier.width(6.dp))
        Text("AYUVAN", color = AyuvanColors.Brand700, style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold)
        Spacer(Modifier.weight(1f))
        if (showNotificationButton) Box(contentAlignment = Alignment.TopEnd) {
            IconButton(onClick = onNotifications) { AssetIcon(R.drawable.icon_notifications, "Open care reminders", Modifier.size(25.dp)) }
            if (hasReminder) Box(modifier = Modifier.padding(top = 8.dp, end = 8.dp).size(8.dp)
                .background(AyuvanColors.Brand600, CircleShape))
        }
        Spacer(Modifier.width(5.dp))
        IconButton(onClick = { onProfile?.invoke() }, enabled = onProfile != null) {
            Icon(Icons.Default.Person, "Open profile", tint = AyuvanColors.Brand700)
        }
    }
}

@Composable
private fun TalkToAyuvanCard(onClick: () -> Unit) {
    ElevatedCard(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFFF6EEFF)),
        elevation = CardDefaults.elevatedCardElevation(defaultElevation = 4.dp),
        shape = RoundedCornerShape(24.dp),
    ) {
        Row(modifier = Modifier.padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
            Image(painter = painterResource(R.drawable.assistant_orb), contentDescription = null, modifier = Modifier.size(66.dp))
            Spacer(Modifier.width(14.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("Talk to AYUVAN", style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(4.dp))
                Text("Share a concern, upload a report or ask a health-related question.", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
            }
            IconBadge(iconRes = R.drawable.icon_assistant_sparkles, contentDescription = null)
        }
    }
}

@Composable
private fun QuickActionGrid(onTabChange: (MainTab) -> Unit) {
    val actions = listOf(
        Triple("Upload\nReport", R.drawable.icon_file_medical, MainTab.MY_HEALTH),
        Triple("Manage\nMedicines", R.drawable.icon_pill, MainTab.MY_HEALTH),
        Triple("My Care\nPlan", R.drawable.icon_care_plan, MainTab.CARE_PLAN),
        Triple("Find\nHealthcare", R.drawable.icon_location_pin, MainTab.DISCOVER),
    )
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        actions.forEach { (label, icon, tab) ->
            Card(
                modifier = Modifier.weight(1f).height(126.dp).clickable { onTabChange(tab) },
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = Color.White),
                border = BorderStroke(1.dp, AyuvanColors.Border),
            ) {
                Column(modifier = Modifier.fillMaxSize().padding(12.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                    AssetIcon(icon, null, Modifier.size(31.dp))
                    Spacer(Modifier.height(9.dp))
                    Text(label, style = MaterialTheme.typography.labelLarge, textAlign = TextAlign.Center, lineHeight = 17.sp)
                }
            }
        }
    }
}

@Composable
private fun CarePlanProgressCard() {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Row(modifier = Modifier.padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(modifier = Modifier.size(64.dp), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(progress = { 0.5f }, modifier = Modifier.fillMaxSize(), color = AyuvanColors.Brand600, trackColor = AyuvanColors.Brand100, strokeWidth = 7.dp)
                AssetIcon(R.drawable.icon_care_plan, null, Modifier.size(29.dp))
            }
            Spacer(Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("Care plan progress", style = MaterialTheme.typography.titleMedium)
                Text("${DemoAyuvanData.careTasksDone} of ${DemoAyuvanData.careTasksTotal} tasks completed", color = AyuvanColors.SecondaryText)
                Spacer(Modifier.height(8.dp))
                LinearProgressIndicator(progress = { 0.5f }, modifier = Modifier.fillMaxWidth().height(7.dp).clip(CircleShape), color = AyuvanColors.Success, trackColor = AyuvanColors.Brand100)
            }
        }
    }
}

@Composable
private fun ActiveConcernCard(onClick: () -> Unit) {
    BasicRowCard(onClick = onClick, leadingIcon = R.drawable.icon_heart_pulse, title = DemoAyuvanData.activeConcernTitle, subtitle = DemoAyuvanData.activeConcernSubtitle, trailing = {
        StatusPill("In progress", AyuvanColors.Brand100, AyuvanColors.Brand700)
    })
}

@Composable
private fun ReminderCard() {
    BasicRowCard(onClick = {}, leadingIcon = R.drawable.icon_care_plan, title = "Follow-up reminder", subtitle = "Choose a date when you are ready", trailing = {
        Icon(Icons.Default.Check, null, tint = AyuvanColors.Success)
    })
}

@Composable
private fun MyHealthScreen(patientName: String, onPatientChange: (String) -> Unit) {
    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Box(modifier = Modifier.fillMaxWidth().height(196.dp)) {
            Image(painter = painterResource(R.drawable.bg_header_misty_hills), contentDescription = null, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            Column(modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp)) {
                AppHeader()
                Spacer(Modifier.height(22.dp))
                Text("My Health", style = MaterialTheme.typography.displaySmall)
                Text("Your health information, all in one place", style = MaterialTheme.typography.bodyLarge, color = AyuvanColors.SecondaryText)
            }
        }
        Column(modifier = Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp)) {
            PatientSwitcher(patientName, onPatientChange)
            Spacer(Modifier.height(18.dp))
            HealthShortcutGrid()
            Spacer(Modifier.height(28.dp))
            SectionTitle("Health Timeline", "View all")
            TimelineCard()
            Spacer(Modifier.height(26.dp))
            SectionTitle("Medical Records", "View all")
            RecordsRow()
            Spacer(Modifier.height(24.dp))
            HealthSummaryCard()
        }
    }
}

@Composable
private fun PatientSwitcher(current: String, onPatientChange: (String) -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    Column {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            OutlinedButton(onClick = { expanded = !expanded }, modifier = Modifier.weight(1f), shape = RoundedCornerShape(22.dp), border = BorderStroke(1.dp, AyuvanColors.Brand200)) {
                Icon(Icons.Default.Person, null, tint = AyuvanColors.Brand700)
                Spacer(Modifier.width(8.dp))
                Text(current, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.weight(1f), textAlign = TextAlign.Start)
                Icon(Icons.Default.ArrowDropDown, null, tint = AyuvanColors.Brand700)
            }
            OutlinedButton(onClick = {}, shape = RoundedCornerShape(22.dp), contentPadding = ButtonDefaults.ContentPadding) {
                Icon(Icons.Default.Add, null)
                Spacer(Modifier.width(4.dp))
                Text("Family")
            }
        }
        if (expanded) {
            Card(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
                listOf("My Profile", "Family profile").forEach { name ->
                    Text(name, modifier = Modifier.fillMaxWidth().clickable { onPatientChange(name); expanded = false }.padding(16.dp), style = MaterialTheme.typography.bodyLarge)
                }
            }
        }
    }
}

@Composable
private fun HealthShortcutGrid() {
    val actions = listOf(
        "Health\nTimeline" to R.drawable.icon_timeline,
        "Medical\nRecords" to R.drawable.icon_file_medical,
        "Medicines" to R.drawable.icon_pill,
        "Conditions &\nAllergies" to R.drawable.icon_shield_check,
    )
    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        actions.forEach { (title, icon) ->
            Card(modifier = Modifier.weight(1f).height(126.dp), shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
                Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
                    AssetIcon(icon, null, Modifier.size(34.dp))
                    Spacer(Modifier.height(9.dp))
                    Text(title, style = MaterialTheme.typography.labelLarge, textAlign = TextAlign.Center, lineHeight = 17.sp)
                }
            }
        }
    }
}

@Composable
private fun TimelineCard() {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Column {
            TimelineRow("Symptom concern", "Ongoing · updated recently", "In progress", AyuvanColors.Brand100, AyuvanColors.Brand700, R.drawable.icon_heart_pulse)
            HorizontalDivider(color = AyuvanColors.Border)
            TimelineRow("Health history", "No clinical conclusion recorded", "Needs review", AyuvanColors.WarningBg, AyuvanColors.Warning, R.drawable.icon_timeline)
            HorizontalDivider(color = AyuvanColors.Border)
            TimelineRow("Documents", "Add a report when you're ready", null, Color.Transparent, Color.Transparent, R.drawable.icon_folder)
        }
    }
}

@Composable
private fun TimelineRow(title: String, subtitle: String, status: String?, statusBackground: Color, statusColor: Color, icon: Int) {
    Row(modifier = Modifier.fillMaxWidth().padding(15.dp), verticalAlignment = Alignment.CenterVertically) {
        IconBadge(iconRes = icon, contentDescription = null)
        Spacer(Modifier.width(11.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
        }
        if (status != null) StatusPill(status, statusBackground, statusColor)
    }
}

@Composable
private fun RecordsRow() {
    Row(modifier = Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        listOf("Lab report" to R.drawable.icon_file_medical, "Prescription" to R.drawable.icon_pill, "Upload record" to R.drawable.icon_upload).forEach { (title, icon) ->
            Card(modifier = Modifier.width(134.dp).height(132.dp), shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.SpaceBetween) {
                    AssetIcon(icon, null, Modifier.size(34.dp))
                    Text(title, style = MaterialTheme.typography.titleMedium)
                    Text(if (title == "Upload record") "PDF or image" else "No document data", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.MutedText)
                }
            }
        }
    }
}

@Composable
private fun HealthSummaryCard() {
    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color(0xFFF8F3FF)), shape = RoundedCornerShape(22.dp), border = BorderStroke(1.dp, AyuvanColors.Brand200)) {
        Row(modifier = Modifier.padding(18.dp), verticalAlignment = Alignment.CenterVertically) {
            Image(painter = painterResource(R.drawable.feature_records), contentDescription = null, modifier = Modifier.size(62.dp))
            Spacer(Modifier.width(10.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("Get a Health Summary", style = MaterialTheme.typography.titleMedium)
                Text("A reviewable draft based only on records you select.", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
            }
            FilledTonalButton(onClick = {}) { Text("Generate") }
        }
    }
}

@Composable
private fun CarePlanScreen() {
    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(16.dp))
        AppHeader()
        Spacer(Modifier.height(25.dp))
        Text("Care Plan", style = MaterialTheme.typography.displaySmall)
        Spacer(Modifier.height(8.dp))
        Text("Keep clinician-recommended tasks and reminders organised here.", color = AyuvanColors.SecondaryText, style = MaterialTheme.typography.bodyLarge)
        Spacer(Modifier.height(28.dp))
        EmptyInformationCard(
            icon = R.drawable.icon_care_plan,
            title = "No active care plan yet",
            body = "When a care plan is added from an authorised source, its tasks and reminders will appear here.",
        )
    }
}

@Composable
private fun DiscoverScreen() {
    var query by rememberSaveable { mutableStateOf("") }
    var category by rememberSaveable { mutableStateOf("Doctors") }
    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Box(modifier = Modifier.fillMaxWidth().height(192.dp)) {
            Image(painter = painterResource(R.drawable.bg_header_misty_hills), contentDescription = null, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            Column(modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp)) {
                AppHeader()
                Spacer(Modifier.height(22.dp))
                Text("Discover Healthcare", style = MaterialTheme.typography.headlineMedium)
                Text("Find doctors, hospitals, clinics and diagnostics near you.", color = AyuvanColors.SecondaryText)
            }
        }
        Column(modifier = Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp)) {
            OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth(),
                leadingIcon = { AssetIcon(R.drawable.icon_search, null, Modifier.size(21.dp)) },
                placeholder = { Text("Search doctors, hospitals, tests…") },
                singleLine = true,
                shape = RoundedCornerShape(18.dp),
            )
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Doctors" to R.drawable.icon_stethoscope, "Hospitals" to R.drawable.icon_hospital, "Diagnostics" to R.drawable.icon_file_medical, "Clinics" to R.drawable.icon_clinic).forEach { (label, icon) ->
                    val selected = label == category
                    Card(modifier = Modifier.weight(1f).height(82.dp).clickable { category = label }, shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = if (selected) AyuvanColors.Brand100 else Color.White), border = BorderStroke(1.dp, if (selected) AyuvanColors.Brand500 else AyuvanColors.Border)) {
                        Column(modifier = Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                            AssetIcon(icon, null, Modifier.size(25.dp))
                            Text(label, fontSize = 11.sp, fontWeight = FontWeight.SemiBold, textAlign = TextAlign.Center)
                        }
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
            Card(modifier = Modifier.fillMaxWidth().height(188.dp), shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Image(painter = painterResource(R.drawable.feature_map), contentDescription = "Map preview", modifier = Modifier.size(118.dp), alpha = 0.9f)
                    StatusPill("Choose a location to search", AyuvanColors.Brand100, AyuvanColors.Brand700, modifier = Modifier.align(Alignment.BottomCenter).padding(14.dp))
                }
            }
            Spacer(Modifier.height(25.dp))
            SectionTitle("Nearby options")
            EmptyInformationCard(icon = R.drawable.icon_location_pin, title = "Search by area", body = "Location access is optional. Choose an area to load source-backed healthcare options.")
        }
    }
}

@Composable
private fun ProfileScreen(patientName: String, onPatientChange: (String) -> Unit) {
    Column(modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(16.dp))
        AppHeader()
        Spacer(Modifier.height(25.dp))
        Text("Profile", style = MaterialTheme.typography.displaySmall)
        Text("Manage your account, family, preferences and privacy.", color = AyuvanColors.SecondaryText)
        Spacer(Modifier.height(18.dp))
        AccountCard()
        Spacer(Modifier.height(20.dp))
        Text("My Profiles", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(10.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            ProfileChip(patientName, true) { onPatientChange("My Profile") }
            ProfileChip("Family profile", false) { onPatientChange("Family profile") }
            ProfileChip("Add profile", false) {}
        }
        Spacer(Modifier.height(24.dp))
        ProfileSettingsList()
        Spacer(Modifier.height(18.dp))
        OutlinedButton(onClick = {}, modifier = Modifier.fillMaxWidth(), border = BorderStroke(1.dp, AyuvanColors.Danger)) { Text("Sign out", color = AyuvanColors.Danger) }
        Spacer(Modifier.height(28.dp))
    }
}

@Composable
private fun AccountCard() {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Image(painter = painterResource(R.drawable.avatar_default), contentDescription = "Account avatar", modifier = Modifier.size(62.dp).clip(CircleShape))
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text("Your account", style = MaterialTheme.typography.titleMedium)
                Text("Contact details appear after secure sign-in", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
            }
            OutlinedButton(onClick = {}) { Text("Edit") }
        }
    }
}

@Composable
private fun ProfileChip(label: String, selected: Boolean, onClick: () -> Unit) {
    Card(modifier = Modifier.width(118.dp).height(92.dp).clickable(onClick = onClick), shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = if (selected) AyuvanColors.Brand100 else Color.White), border = BorderStroke(1.dp, if (selected) AyuvanColors.Brand500 else AyuvanColors.Border)) {
        Column(modifier = Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
            Icon(Icons.Default.Person, null, tint = AyuvanColors.Brand700)
            Spacer(Modifier.height(6.dp))
            Text(label, style = MaterialTheme.typography.labelLarge, textAlign = TextAlign.Center, maxLines = 2, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
private fun ProfileSettingsList() {
    val rows = listOf(
        Triple("Personal Information", "Name, date of birth and contact details", R.drawable.icon_profile),
        Triple("Health Information", "Conditions, allergies and medicines", R.drawable.icon_heart_pulse),
        Triple("App Preferences", "Language, notifications and appearance", R.drawable.icon_settings),
        Triple("Connected Accounts", "WhatsApp and supported integrations", R.drawable.icon_link),
        Triple("Privacy & Security", "Consent, data access and account safety", R.drawable.icon_shield_check),
        Triple("Help & Support", "FAQs, feedback and technical help", R.drawable.icon_headset),
    )
    Card(shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Column {
            rows.forEachIndexed { index, (title, subtitle, icon) ->
                Row(modifier = Modifier.fillMaxWidth().clickable {}.padding(15.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconBadge(iconRes = icon, contentDescription = null)
                    Spacer(Modifier.width(12.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(title, style = MaterialTheme.typography.titleMedium)
                        Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
                    }
                    Icon(Icons.AutoMirrored.Filled.ArrowForward, null, tint = AyuvanColors.Brand700)
                }
                if (index != rows.lastIndex) HorizontalDivider(color = AyuvanColors.Border)
            }
        }
    }
}

@Composable
private fun ChatScreen(patientName: String, onBack: () -> Unit) {
    val messages = remember {
        mutableStateListOf(
            ChatMessage("welcome", "Describe a health concern, share a report or ask a health-related question. I can help organise the information for your next step.", false),
        )
    }
    var composer by rememberSaveable { mutableStateOf("") }
    var selectedSeverity by rememberSaveable { mutableStateOf<String?>(null) }
    Scaffold(
        containerColor = AyuvanColors.Page,
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Image(painter = painterResource(R.drawable.assistant_orb), contentDescription = null, modifier = Modifier.size(38.dp))
                        Spacer(Modifier.width(9.dp))
                        Column {
                            Text("Talk to AYUVAN", style = MaterialTheme.typography.titleMedium)
                            Text("AI health assistant · $patientName", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
                        }
                    }
                },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") } },
                actions = { IconButton(onClick = {}) { Icon(Icons.Default.MoreVert, "Conversation options") } },
            )
        },
        bottomBar = {
            Column(modifier = Modifier.background(Color.White).padding(horizontal = 14.dp, vertical = 10.dp)) {
                Row(modifier = Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("Describe a symptom", "Upload a report", "Prepare for a visit").forEach { label ->
                        AssistChip(onClick = { composer = label }, label = { Text(label) })
                    }
                }
                Spacer(Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = {}) { Icon(Icons.Default.Add, "Add attachment", tint = AyuvanColors.Brand700) }
                    OutlinedTextField(
                        value = composer,
                        onValueChange = { composer = it },
                        modifier = Modifier.weight(1f),
                        placeholder = { Text("Type a message…") },
                        trailingIcon = { AssetIcon(R.drawable.icon_microphone, "Voice input", Modifier.size(22.dp)) },
                        shape = RoundedCornerShape(26.dp),
                        maxLines = 4,
                    )
                    Spacer(Modifier.width(8.dp))
                    FilledIconButton(
                        onClick = {
                            val clean = composer.trim()
                            if (clean.isNotEmpty()) {
                                messages += ChatMessage("user-${messages.size}", clean, true)
                                messages += ChatMessage("reply-${messages.size}", "Thanks for sharing that. I’ll ask only what is relevant and will keep your information clearly labelled as user-reported.", false)
                                composer = ""
                            }
                        },
                        enabled = composer.isNotBlank(),
                        colors = IconButtonDefaults.filledIconButtonColors(containerColor = AyuvanColors.Brand700),
                    ) { Icon(Icons.AutoMirrored.Filled.Send, "Send") }
                }
            }
        },
    ) { innerPadding ->
        LazyColumn(modifier = Modifier.fillMaxSize().padding(innerPadding).padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { Spacer(Modifier.height(8.dp)) }
            item { ChatSafetyNote() }
            items(messages, key = { it.id }) { message -> MessageBubble(message) }
            item {
                QuestionCard(selectedSeverity = selectedSeverity, onSelect = { selectedSeverity = it })
            }
            item { Spacer(Modifier.height(6.dp)) }
        }
    }
}

@Composable
private fun ChatSafetyNote() {
    Row(modifier = Modifier.fillMaxWidth().background(AyuvanColors.WarningBg, RoundedCornerShape(14.dp)).padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Default.WarningAmber, null, tint = AyuvanColors.Warning)
        Spacer(Modifier.width(8.dp))
        Text("AYUVAN provides AI-assisted health information, not a confirmed diagnosis or emergency service.", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.Warning)
    }
}

@Composable
private fun MessageBubble(message: ChatMessage) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = if (message.fromUser) Arrangement.End else Arrangement.Start) {
        Card(
            modifier = Modifier.widthIn(max = 310.dp),
            shape = RoundedCornerShape(if (message.fromUser) 20.dp else 18.dp),
            colors = CardDefaults.cardColors(containerColor = if (message.fromUser) AyuvanColors.Brand100 else Color.White),
            border = if (message.fromUser) null else BorderStroke(1.dp, AyuvanColors.Border),
        ) {
            Text(message.text, modifier = Modifier.padding(14.dp), style = MaterialTheme.typography.bodyLarge)
        }
    }
}

@Composable
private fun QuestionCard(selectedSeverity: String?, onSelect: (String) -> Unit) {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Brand200)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                AssetIcon(R.drawable.icon_heart_pulse, null, Modifier.size(24.dp))
                Spacer(Modifier.width(8.dp))
                Text("A few quick questions", style = MaterialTheme.typography.titleMedium)
                Spacer(Modifier.weight(1f))
                Text("1 of 3", color = AyuvanColors.MutedText, style = MaterialTheme.typography.bodyMedium)
            }
            Spacer(Modifier.height(14.dp))
            Text("How would you describe how this is affecting you?", style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(10.dp))
            listOf("Mild (manageable)", "Moderate (affects daily work)", "Severe (very intense)", "Not sure").forEach { option ->
                SelectableRow(option, option == selectedSeverity, onClick = { onSelect(option) })
                Spacer(Modifier.height(8.dp))
            }
            Button(onClick = {}, modifier = Modifier.align(Alignment.End), enabled = selectedSeverity != null) {
                Text("Continue")
                Spacer(Modifier.width(5.dp))
                Icon(Icons.AutoMirrored.Filled.ArrowForward, null)
            }
        }
    }
}

@Composable
private fun BasicRowCard(onClick: () -> Unit, leadingIcon: Int, title: String, subtitle: String, trailing: @Composable () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth().clickable(onClick = onClick), shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Row(modifier = Modifier.padding(15.dp), verticalAlignment = Alignment.CenterVertically) {
            IconBadge(iconRes = leadingIcon, contentDescription = null)
            Spacer(Modifier.width(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
            }
            trailing()
        }
    }
}

@Composable
private fun SectionTitle(title: String, action: String? = null) {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(title, style = MaterialTheme.typography.titleLarge)
        if (action != null) {
            Spacer(Modifier.weight(1f))
            TextButton(onClick = {}) { Text(action) }
        }
    }
    Spacer(Modifier.height(10.dp))
}

@Composable
private fun EmptyInformationCard(icon: Int, title: String, body: String) {
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(22.dp), colors = CardDefaults.cardColors(containerColor = Color.White), border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Column(modifier = Modifier.padding(22.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            IconBadge(iconRes = icon, contentDescription = null, large = true)
            Spacer(Modifier.height(12.dp))
            Text(title, style = MaterialTheme.typography.titleMedium, textAlign = TextAlign.Center)
            Spacer(Modifier.height(5.dp))
            Text(body, style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText, textAlign = TextAlign.Center)
        }
    }
}

@Composable
private fun BenefitRow(text: String) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(Icons.Default.Check, null, tint = AyuvanColors.Brand700, modifier = Modifier.size(20.dp))
        Spacer(Modifier.width(11.dp))
        Text(text, style = MaterialTheme.typography.bodyLarge)
    }
}

@Composable
private fun SelectableRow(text: String, selected: Boolean, onClick: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = if (selected) AyuvanColors.Brand100 else Color.White),
        border = BorderStroke(1.dp, if (selected) AyuvanColors.Brand500 else AyuvanColors.Border),
    ) {
        Row(modifier = Modifier.padding(horizontal = 15.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(text, modifier = Modifier.weight(1f), style = MaterialTheme.typography.bodyLarge)
            SelectionDot(selected)
        }
    }
}

@Composable
private fun SelectionDot(selected: Boolean) {
    Box(
        modifier = Modifier.size(20.dp).background(if (selected) AyuvanColors.Brand700 else Color.White, CircleShape).semantics { contentDescription = if (selected) "Selected" else "Not selected" },
        contentAlignment = Alignment.Center,
    ) {
        if (selected) Icon(Icons.Default.Check, null, tint = Color.White, modifier = Modifier.size(14.dp))
    }
}

@Composable
private fun PrimaryButton(label: String, onClick: () -> Unit, enabled: Boolean = true) {
    Button(onClick = onClick, enabled = enabled, modifier = Modifier.fillMaxWidth().height(54.dp), shape = RoundedCornerShape(18.dp), colors = ButtonDefaults.buttonColors(containerColor = AyuvanColors.Brand700)) {
        Text(label, style = MaterialTheme.typography.labelLarge)
        Spacer(Modifier.width(7.dp))
        Icon(Icons.AutoMirrored.Filled.ArrowForward, null, modifier = Modifier.size(18.dp))
    }
}

@Composable
private fun BrandMark() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Image(painterResource(R.drawable.handoff_leaf), null, Modifier.size(32.dp))
        Spacer(Modifier.width(6.dp))
        Text("AYUVAN", color = AyuvanColors.Brand700, style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun AssetIcon(resId: Int, contentDescription: String?, modifier: Modifier = Modifier) {
    Image(painter = painterResource(resId), contentDescription = contentDescription, modifier = modifier, contentScale = ContentScale.Fit)
}

@Composable
private fun IconBadge(icon: androidx.compose.ui.graphics.vector.ImageVector, contentDescription: String?, large: Boolean = false) {
    Box(modifier = Modifier.size(if (large) 58.dp else 46.dp).background(AyuvanColors.Brand100, CircleShape), contentAlignment = Alignment.Center) {
        Icon(icon, contentDescription, tint = AyuvanColors.Brand700, modifier = Modifier.size(if (large) 29.dp else 23.dp))
    }
}

@Composable
private fun IconBadge(iconRes: Int, contentDescription: String?, large: Boolean = false) {
    Box(modifier = Modifier.size(if (large) 58.dp else 46.dp).background(AyuvanColors.Brand100, CircleShape), contentAlignment = Alignment.Center) {
        AssetIcon(iconRes, contentDescription, Modifier.size(if (large) 31.dp else 25.dp))
    }
}

@Composable
private fun StatusPill(text: String, background: Color, color: Color, modifier: Modifier = Modifier) {
    Text(text, modifier = modifier.background(background, CircleShape).padding(horizontal = 11.dp, vertical = 6.dp), color = color, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
}

private fun JSONArray.rows(): List<JSONObject> = (0 until length()).mapNotNull { optJSONObject(it) }
private fun JSONObject.list(key: String): List<JSONObject> = optJSONArray(key)?.rows() ?: emptyList()

private fun formatHealthSummary(summary: JSONObject): String = buildString {
    appendLine("AYUVAN health summary")
    appendLine(summary.optJSONObject("patient")?.optString("display_name") ?: "Patient")
    appendLine("Generated ${summary.optString("generated_at").take(10)}")
    appendLine("Patient-reported information; not a confirmed diagnosis.")
    appendLine()
    appendLine("Active concerns")
    summary.list("active_concerns").takeIf { it.isNotEmpty() }?.forEach {
        appendLine("• ${it.optString("symptom")} — last reported ${it.optString("last_reported_at").take(10)}")
    } ?: appendLine("• None recorded")
    for ((key, label) in listOf("conditions" to "Conditions", "allergies" to "Allergies", "medications" to "Medicines")) {
        appendLine(); appendLine(label)
        summary.list(key).takeIf { it.isNotEmpty() }?.forEach { appendLine("• ${it.optString("name")}") }
            ?: appendLine("• None recorded")
    }
}

private data class DocumentPage(val bitmap: Bitmap, val pageCount: Int)

private suspend fun renderDocumentPage(context: android.content.Context, bytes: ByteArray,
                                       mime: String, page: Int): DocumentPage = withContext(Dispatchers.IO) {
    if (mime != "application/pdf") {
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
        var sample = 1
        while (bounds.outWidth / sample > 1600 || bounds.outHeight / sample > 1600) sample *= 2
        val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size,
            BitmapFactory.Options().apply { inSampleSize = sample })
            ?: throw IllegalArgumentException("Could not display this image")
        DocumentPage(bitmap, 1)
    } else {
        val temp = java.io.File.createTempFile("ayuvan-preview-", ".pdf", context.cacheDir)
        try {
            temp.writeBytes(bytes)
            ParcelFileDescriptor.open(temp, ParcelFileDescriptor.MODE_READ_ONLY).use { descriptor ->
                PdfRenderer(descriptor).use { renderer ->
                    val safePage = page.coerceIn(0, renderer.pageCount - 1)
                    renderer.openPage(safePage).use { pdfPage ->
                        val scale = minOf(1440f / pdfPage.width, 1440f / pdfPage.height, 2f)
                        val bitmap = Bitmap.createBitmap((pdfPage.width * scale).toInt().coerceAtLeast(1),
                            (pdfPage.height * scale).toInt().coerceAtLeast(1), Bitmap.Config.ARGB_8888)
                        bitmap.eraseColor(android.graphics.Color.WHITE)
                        pdfPage.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                        DocumentPage(bitmap, renderer.pageCount)
                    }
                }
            }
        } finally { temp.delete() }
    }
}

@Composable
private fun LoadError(message: String?) {
    if (message != null) Text(message, color = AyuvanColors.Danger,
        modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp))
}

@Composable
private fun ConnectedHomeScreen(api: MobileApi, patientId: String, patientName: String,
                                onOpenChat: (String) -> Unit, onOpenDocuments: () -> Unit,
                                onTabChange: (MainTab) -> Unit) {
    var health by remember(patientId) { mutableStateOf<JSONObject?>(null) }
    var care by remember(patientId) { mutableStateOf<JSONObject?>(null) }
    var error by remember(patientId) { mutableStateOf<String?>(null) }
    var draft by rememberSaveable(patientId) { mutableStateOf("") }
    var uploadBusy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val uploadLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null && !uploadBusy) scope.launch {
            uploadBusy = true; error = null
            try { api.upload(patientId, uri); onOpenDocuments() }
            catch (e: Exception) { error = e.message ?: "Upload failed. Please try again." }
            uploadBusy = false
        }
    }
    LaunchedEffect(patientId) {
        if (patientId.isNotBlank()) try {
            health = api.health(patientId); care = api.care(patientId)
        } catch (e: Exception) { error = e.message }
    }
    val episodes = health?.list("episodes")?.filter { it.optString("status") == "active" } ?: emptyList()
    val tasks = care?.list("tasks") ?: emptyList()
    val upcoming = tasks.filter { it.optString("status") == "pending" }.minByOrNull { it.optString("due_at") }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(12.dp))
        AppHeader(onNotifications = { onTabChange(MainTab.CARE_PLAN) }, showNotificationButton = upcoming != null,
            hasReminder = upcoming != null, onProfile = { onTabChange(MainTab.PROFILE) })
        Spacer(Modifier.height(24.dp))
        Box(Modifier.fillMaxWidth().height(154.dp).clip(RoundedCornerShape(20.dp))) {
            Image(painterResource(R.drawable.handoff_home_landscape), null,
                modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Crop)
            Text("How can we help\nyou today?", style = MaterialTheme.typography.headlineMedium,
                color = AyuvanColors.Text, fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(20.dp))
        }
        Spacer(Modifier.height(8.dp))
        Text("For $patientName · Tell us what is happening in your own words.",
            color = AyuvanColors.SecondaryText)
        Spacer(Modifier.height(20.dp))
        Card(colors = CardDefaults.cardColors(containerColor = Color.White),
            border = BorderStroke(1.dp, AyuvanColors.Border), shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(16.dp)) {
                OutlinedTextField(value = draft, onValueChange = { draft = it.take(4000) },
                    modifier = Modifier.fillMaxWidth(), minLines = 3, maxLines = 5,
                    placeholder = { Text("Describe how you feel or ask a health question…") },
                    label = { Text("Your message") })
                Spacer(Modifier.height(12.dp))
                Button(onClick = { val text = draft.trim(); draft = ""; onOpenChat(text) },
                    enabled = draft.isNotBlank(), modifier = Modifier.fillMaxWidth().height(52.dp)) {
                    Text("Send to AYUVAN"); Spacer(Modifier.width(8.dp)); Icon(Icons.AutoMirrored.Filled.Send, null)
                }
                TextButton(onClick = { onOpenChat("") }, modifier = Modifier.fillMaxWidth()) {
                    Text("Continue conversation")
                }
                TextButton(onClick = { uploadLauncher.launch(arrayOf("application/pdf", "image/jpeg", "image/png", "image/webp")) },
                    enabled = !uploadBusy, modifier = Modifier.fillMaxWidth()) {
                    Image(painterResource(R.drawable.handoff_paperclip), null, Modifier.size(22.dp))
                    Spacer(Modifier.width(8.dp))
                    Text(if (uploadBusy) "Uploading report…" else "Attach a prescription or report")
                }
            }
        }
        Spacer(Modifier.height(24.dp))
        LoadError(error)
        when {
            episodes.isNotEmpty() -> BasicRowCard(onClick = { onOpenChat("") },
                leadingIcon = R.drawable.icon_heart_pulse, title = "Continue your concern",
                subtitle = "${episodes.first().optString("symptom", "Health concern")} · ${episodes.first().optString("last_reported_at").take(10)}",
                trailing = { Icon(Icons.AutoMirrored.Filled.ArrowForward, null) })
            upcoming != null -> BasicRowCard(onClick = { onTabChange(MainTab.CARE_PLAN) },
                leadingIcon = R.drawable.icon_care_plan, title = "Next in your care",
                subtitle = upcoming.optString("description"),
                trailing = { Icon(Icons.AutoMirrored.Filled.ArrowForward, null) })
            else -> Text("A simple place to start. Share a concern and we’ll help you understand the next step.",
                color = AyuvanColors.SecondaryText, modifier = Modifier.padding(vertical = 12.dp))
        }
        Spacer(Modifier.height(16.dp))
        TextButton(onClick = { onTabChange(MainTab.DISCOVER) }) {
            Text("Find a healthcare facility  →")
        }
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun ConnectedChatScreen(api: MobileApi, patientId: String, patientName: String,
                                initialMessage: String, onInitialConsumed: () -> Unit, onBack: () -> Unit) {
    var chat by remember(patientId) { mutableStateOf<JSONObject?>(null) }
    var composer by rememberSaveable(patientId) { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var pendingText by remember(patientId) { mutableStateOf<String?>(null) }
    var pendingId by remember(patientId) { mutableStateOf<String?>(null) }
    var pendingReplyId by remember(patientId) { mutableStateOf<String?>(null) }
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    fun send(text: String, replyId: String? = null, retry: Boolean = false) {
        if (text.isBlank() || busy) return
        val outgoing = text.trim()
        val id = if (retry) pendingId ?: java.util.UUID.randomUUID().toString()
                 else java.util.UUID.randomUUID().toString()
        pendingText = outgoing; pendingId = id; pendingReplyId = replyId
        if (!retry && composer.trim() == outgoing) composer = ""
        busy = true
        scope.launch {
            error = null
            try {
                chat = api.send(patientId, outgoing, replyId, id)
                pendingText = null; pendingId = null; pendingReplyId = null
            } catch (e: Exception) {
                error = "Message status is uncertain. Check the conversation or retry safely. ${e.message ?: ""}"
                runCatching { chat = api.chat(patientId) }
                if (chat?.list("messages")?.any { it.optString("text") == outgoing &&
                            it.optString("direction") == "incoming" &&
                            it.optString("status") == "processed" } == true) {
                    pendingText = null; pendingId = null; pendingReplyId = null; error = null
                }
            }
            busy = false
        }
    }
    LaunchedEffect(patientId) {
        if (patientId.isNotBlank()) try {
            val loaded = api.chat(patientId)
            if (pendingText == null) chat = loaded
        } catch (e: Exception) { error = e.message }
    }
    LaunchedEffect(patientId, initialMessage) {
        if (patientId.isNotBlank() && initialMessage.isNotBlank()) {
            onInitialConsumed()
            send(initialMessage)
        }
    }
    val messages = chat?.list("messages") ?: emptyList()
    val question = chat?.optJSONObject("question")
    val options = question?.list("options") ?: emptyList()
    LaunchedEffect(messages.size, pendingText, busy, options.size) {
        if (listState.layoutInfo.totalItemsCount > 0)
            listState.animateScrollToItem(listState.layoutInfo.totalItemsCount - 1)
    }
    Scaffold(containerColor = AyuvanColors.Page,
        topBar = { TopAppBar(title = { Text("Talk to AYUVAN · $patientName", style = MaterialTheme.typography.titleMedium) },
            navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") } }) },
        bottomBar = { Row(modifier = Modifier.fillMaxWidth().background(Color.White).imePadding().padding(12.dp),
            verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(value = composer, onValueChange = { composer = it.take(4000) },
                modifier = Modifier.weight(1f), placeholder = { Text("Describe a health concern…") }, maxLines = 4)
            IconButton(onClick = { send(composer) }, enabled = !busy && composer.isNotBlank()) {
                Icon(Icons.AutoMirrored.Filled.Send, "Send message", tint = AyuvanColors.Brand700)
            }
        } }) { padding ->
        LazyColumn(state = listState, modifier = Modifier.fillMaxSize().padding(padding).padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)) {
            item { Spacer(Modifier.height(8.dp)); ChatSafetyNote(); LoadError(error) }
            if (messages.isEmpty()) item { MessageBubble(ChatMessage("welcome", "Tell me what is happening. I will ask only the details needed to understand your concern.", false)) }
            items(messages, key = { it.optString("id") }) { m ->
                MessageBubble(ChatMessage(m.optString("id"), m.optString("text"),
                    m.optString("direction") == "incoming"))
            }
            if (pendingText != null) item(key = "pending-message") {
                Column {
                    MessageBubble(ChatMessage("pending", pendingText!!, true))
                    Text(if (busy) "Sending · waiting for AYUVAN…" else "Could not confirm delivery",
                        color = AyuvanColors.SecondaryText, modifier = Modifier.padding(8.dp))
                    if (busy) CircularProgressIndicator(Modifier.size(20.dp), strokeWidth = 2.dp)
                    else TextButton(onClick = { send(pendingText!!, pendingReplyId, retry = true) }) {
                        Text("Retry this message")
                    }
                }
            }
            if (options.isNotEmpty()) item {
                Card(colors = CardDefaults.cardColors(containerColor = Color.White),
                    shape = RoundedCornerShape(20.dp)) {
                    Column(Modifier.padding(14.dp)) {
                        Text(question?.optString("text").orEmpty().ifBlank { "Choose an answer" },
                            style = MaterialTheme.typography.titleMedium)
                        options.forEach { option ->
                            OutlinedButton(onClick = { send(option.optString("label"), option.optString("id")) },
                                enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text(option.optString("label")) }
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(8.dp)) }
        }
    }
}

@Composable
private fun ConnectedHealthScreen(api: MobileApi, patientId: String, patients: JSONArray,
                                  onPatientChange: (String) -> Unit, onPatientsRefresh: (JSONArray) -> Unit,
                                  initialSection: String, onProfile: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var data by remember(patientId) { mutableStateOf<JSONObject?>(null) }
    var documents by remember(patientId) { mutableStateOf<JSONObject?>(null) }
    var error by remember(patientId) { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var expanded by remember { mutableStateOf(false) }
    var recordsSection by rememberSaveable(patientId) { mutableStateOf("Timeline") }
    LaunchedEffect(initialSection, patientId) { recordsSection = initialSection }
    var recordSearch by rememberSaveable(patientId) { mutableStateOf("") }
    var addKind by remember { mutableStateOf<String?>(null) }
    var editItemId by remember { mutableStateOf<String?>(null) }
    var addName by remember { mutableStateOf("") }
    var addDetails by remember { mutableStateOf("") }
    var familyDialog by remember { mutableStateOf(false) }
    var familyName by remember { mutableStateOf("") }
    var familyRelationship by remember { mutableStateOf("child") }
    var familyBirthDate by remember { mutableStateOf("") }
    var familySex by remember { mutableStateOf("") }
    var familyAuthorized by remember { mutableStateOf(false) }
    var correctionEpisode by remember { mutableStateOf<JSONObject?>(null) }
    var correction by remember { mutableStateOf("") }
    var summaryText by remember { mutableStateOf<String?>(null) }
    var reviewDocument by remember { mutableStateOf<JSONObject?>(null) }
    var deleteDocumentId by remember { mutableStateOf<String?>(null) }
    val selectedFacts = remember { mutableStateListOf<String>() }
    var downloadDocumentId by remember { mutableStateOf<String?>(null) }
    var previewBytes by remember { mutableStateOf<ByteArray?>(null) }
    var previewMime by remember { mutableStateOf("application/pdf") }
    var previewPage by remember { mutableStateOf(0) }
    var previewRendered by remember { mutableStateOf<DocumentPage?>(null) }
    var previewError by remember { mutableStateOf<String?>(null) }
    suspend fun refresh() { data = api.health(patientId); documents = api.documents(patientId) }
    LaunchedEffect(patientId) { if (patientId.isNotBlank()) try { refresh() } catch (e: Exception) { error = e.message } }
    fun action(block: suspend () -> Unit) {
        scope.launch { busy = true; error = null
            try { block(); refresh() } catch (e: Exception) { error = e.message }
            busy = false
        }
    }
    val uploadLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) action { api.upload(patientId, uri) }
    }
    val saveLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/octet-stream")) { uri ->
        val id = downloadDocumentId
        if (uri != null && id != null) action {
            val bytes = api.download(patientId, id)
            context.contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
        }
    }
    val current = patients.rows().firstOrNull { it.optString("id") == patientId }
    LaunchedEffect(previewBytes, previewPage) {
        val bytes = previewBytes ?: return@LaunchedEffect
        try { previewRendered = renderDocumentPage(context, bytes, previewMime, previewPage); previewError = null }
        catch (e: Exception) { previewError = e.message ?: "Preview unavailable" }
    }
    val episodes = data?.list("episodes") ?: emptyList()
    val docRows = documents?.list("documents") ?: emptyList()
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Column(Modifier.padding(20.dp)) {
            AppHeader(onProfile = onProfile)
            Spacer(Modifier.height(18.dp))
            Text("Your records", style = MaterialTheme.typography.headlineMedium)
            Text("A clear history for your next conversation with a clinician.",
                color = AyuvanColors.SecondaryText)
        }
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 32.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                OutlinedButton(onClick = { expanded = true }, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.Person, null); Spacer(Modifier.width(8.dp))
                    Text(current?.optString("display_name") ?: "My Profile", modifier = Modifier.weight(1f))
                    Icon(Icons.Default.ArrowDropDown, null)
                }
                DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                    patients.rows().forEach { patient -> DropdownMenuItem(
                        text = { Text(patient.optString("display_name")) },
                        onClick = { expanded = false; onPatientChange(patient.optString("id")) }) }
                }
                Spacer(Modifier.width(8.dp))
                TextButton(onClick = { familyDialog = true }) { Text("Add family") }
            }
            Spacer(Modifier.height(14.dp)); LoadError(error)
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Timeline", "Medical profile", "Documents").forEach { section ->
                    AssistChip(onClick = { recordsSection = section }, label = { Text(section) },
                        leadingIcon = if (recordsSection == section) ({ Icon(Icons.Default.Check, null) }) else null)
                }
            }
            Spacer(Modifier.height(16.dp))
            if (recordsSection == "Timeline") {
            OutlinedTextField(value = recordSearch, onValueChange = { recordSearch = it.take(80) },
                label = { Text("Search concerns") }, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(12.dp))
            Text("Health timeline", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(8.dp))
            if (episodes.isEmpty()) EmptyInformationCard(R.drawable.icon_timeline, "No symptoms recorded", "Your WhatsApp and app history appears here after verified linking.")
            else episodes.filter { recordSearch.isBlank() || it.optString("symptom").contains(recordSearch, true) ||
                it.optString("last_reported_at").contains(recordSearch, true) }.forEach { episode ->
                BasicRowCard(onClick = { correctionEpisode = episode }, leadingIcon = R.drawable.icon_heart_pulse,
                    title = episode.optString("symptom", "Concern"),
                    subtitle = "${episode.optString("status")} · ${episode.optString("last_reported_at").take(10)} · Tap to correct",
                    trailing = { Icon(Icons.AutoMirrored.Filled.ArrowForward, null) })
                Spacer(Modifier.height(8.dp))
            }
            }
            if (recordsSection == "Medical profile") {
            Spacer(Modifier.height(20.dp))
            listOf("conditions" to "Conditions", "allergies" to "Allergies", "medications" to "Medicines").forEach { (kind, title) ->
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                    TextButton(onClick = { addKind = kind; editItemId = null; addName = ""; addDetails = "" }) { Text("Add") }
                }
                val records = data?.list(kind) ?: emptyList()
                if (records.isEmpty()) Text("No $title recorded", color = AyuvanColors.MutedText,
                    modifier = Modifier.padding(bottom = 12.dp))
                else records.forEach { record ->
                    BasicRowCard(onClick = {
                        addKind = kind; editItemId = record.optString("id"); addName = record.optString("name")
                        addDetails = when (kind) { "medications" -> record.optString("dosage")
                            "allergies" -> record.optString("reaction"); else -> "" }
                    }, leadingIcon = if (kind == "medications") R.drawable.icon_pill else R.drawable.icon_heart_pulse,
                        title = record.optString("name"), subtitle = when (kind) { "medications" -> record.optString("dosage")
                            "allergies" -> record.optString("reaction"); else -> record.optString("verification_status", "Patient reported") },
                        trailing = { IconButton(onClick = { action { api.deleteHealthItem(patientId, kind, record.optString("id")) } }) {
                            Icon(Icons.Default.Close, "Remove") } })
                    Spacer(Modifier.height(7.dp))
                }
                Spacer(Modifier.height(8.dp))
            }
            Spacer(Modifier.height(12.dp))
            FilledTonalButton(onClick = { action { summaryText = formatHealthSummary(api.summary(patientId)) } },
                modifier = Modifier.fillMaxWidth()) { Text("Prepare health summary") }
            }
            if (recordsSection == "Documents") {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Medical Records", style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                TextButton(onClick = { uploadLauncher.launch(arrayOf("application/pdf", "image/jpeg", "image/png", "image/webp")) }) { Text("Upload") }
            }
            Text("PDF or image, up to 10 MB. Extracted facts enter your record only after review.",
                color = AyuvanColors.SecondaryText, style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(8.dp))
            if (docRows.isEmpty()) EmptyInformationCard(R.drawable.icon_folder, "No documents", "Upload a prescription or report to keep it in your private record.")
            else docRows.forEach { doc ->
                Card(modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp), colors = CardDefaults.cardColors(containerColor = Color.White),
                    shape = RoundedCornerShape(18.dp)) {
                    Column(Modifier.padding(14.dp)) {
                        Text(doc.optJSONObject("extraction")?.optJSONObject("result")?.optString("filename") ?: "Medical document",
                            style = MaterialTheme.typography.titleMedium)
                        Text("${doc.optString("created_at").take(10)} · ${doc.optString("processing_status")}", color = AyuvanColors.SecondaryText)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            TextButton(onClick = { scope.launch {
                                try { previewMime = doc.optString("content_type"); previewPage = 0
                                    previewRendered = null; previewBytes = api.download(patientId, doc.optString("id")) }
                                catch (e: Exception) { error = e.message }
                            } }) { Text("View") }
                            TextButton(onClick = { downloadDocumentId = doc.optString("id"); saveLauncher.launch("ayuvan-record") }) { Text("Save") }
                            TextButton(onClick = { deleteDocumentId = doc.optString("id") }) { Text("Delete", color = AyuvanColors.Danger) }
                            if (doc.optString("processing_status") == "uploaded") TextButton(onClick = {
                                action { api.extract(patientId, doc.optString("id")) }
                            }) { Text("Extract") }
                            val extracted = doc.optJSONObject("extraction")
                            if (extracted?.optString("verification_status") == "unverified" && doc.optString("processing_status") == "extracted")
                                TextButton(onClick = { selectedFacts.clear(); reviewDocument = doc }) { Text("Review draft") }
                        }
                    }
                }
            }
            }
        }
    }
    if (addKind != null) AlertDialog(onDismissRequest = { addKind = null },
        title = { Text(if (editItemId == null) "Add health information" else "Edit health information") },
        text = { Column {
            OutlinedTextField(value = addName, onValueChange = { addName = it.take(255) }, label = { Text("Name") })
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(value = addDetails, onValueChange = { addDetails = it.take(255) },
                label = { Text(if (addKind == "medications") "Dose (optional)" else "Details (optional)") })
        } }, confirmButton = { TextButton(onClick = {
            val kind = addKind!!; val itemId = editItemId; addKind = null
            action { if (itemId == null) api.addHealthItem(patientId, kind, addName.trim(), addDetails.ifBlank { null })
                else api.updateHealthItem(patientId, kind, itemId, addName.trim(), addDetails.ifBlank { null }) }
        }, enabled = addName.isNotBlank()) { Text("Save") } },
        dismissButton = { TextButton(onClick = { addKind = null }) { Text("Cancel") } })
    if (familyDialog) AlertDialog(onDismissRequest = { familyDialog = false },
        title = { Text("Add family profile") }, text = { Column(Modifier.verticalScroll(rememberScrollState())) {
            OutlinedTextField(value = familyName, onValueChange = { familyName = it.take(160) }, label = { Text("Name") })
            OutlinedTextField(value = familyBirthDate, onValueChange = { familyBirthDate = it.take(10) },
                label = { Text("Date of birth (optional, YYYY-MM-DD)") })
            Row(Modifier.horizontalScroll(rememberScrollState())) {
                listOf("child", "parent", "spouse", "other").forEach { item ->
                    AssistChip(onClick = { familyRelationship = item }, label = { Text(item) })
                }
            }
            Row(Modifier.horizontalScroll(rememberScrollState())) {
                listOf("woman", "man", "other", "prefer_not_to_say").forEach { item ->
                    AssistChip(onClick = { familySex = item }, label = { Text(item.replace('_', ' ')) },
                        leadingIcon = if (familySex == item) ({ Icon(Icons.Default.Check, null) }) else null)
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(checked = familyAuthorized, onCheckedChange = { familyAuthorized = it })
                Text("I am authorised to manage this person's health information.", style = MaterialTheme.typography.bodyMedium)
            }
        } }, confirmButton = { TextButton(onClick = {
            familyDialog = false
            action { val created = api.createFamily(familyName.trim(), familyRelationship,
                familyBirthDate.ifBlank { null }, familySex.ifBlank { null })
                onPatientsRefresh(api.me().optJSONArray("patients") ?: JSONArray())
                onPatientChange(created.optString("id")) }
        }, enabled = familyName.trim().length >= 2 && familyAuthorized) { Text("Create") } },
        dismissButton = { TextButton(onClick = { familyDialog = false }) { Text("Cancel") } })
    if (correctionEpisode != null) AlertDialog(onDismissRequest = { correctionEpisode = null },
        title = { Text("Correct reported symptom") }, text = { Column {
            Text("The original report stays in the timeline. Your correction is added as a new entry.")
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(value = correction, onValueChange = { correction = it.take(1000) },
                label = { Text("What should be corrected?") }, minLines = 3)
        } }, confirmButton = { TextButton(onClick = { val id = correctionEpisode!!.optString("id")
            val correctionText = correction.trim()
            correctionEpisode = null; action { api.correct(patientId, id, correctionText) }; correction = ""
        }, enabled = correction.trim().length >= 4) { Text("Save correction") } },
        dismissButton = { TextButton(onClick = { correctionEpisode = null }) { Text("Cancel") } })
    if (summaryText != null) AlertDialog(onDismissRequest = { summaryText = null },
        title = { Text("Health summary") }, text = { Text(summaryText!!, modifier = Modifier.verticalScroll(rememberScrollState())) },
        confirmButton = { TextButton(onClick = {
            context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"; putExtra(Intent.EXTRA_TEXT, summaryText)
            }, "Share health summary")); summaryText = null
        }) { Text("Share") } }, dismissButton = { TextButton(onClick = { summaryText = null }) { Text("Close") } })
    if (reviewDocument != null) {
        val doc = reviewDocument!!
        val result = doc.optJSONObject("extraction")?.optJSONObject("result") ?: JSONObject()
        AlertDialog(onDismissRequest = { reviewDocument = null }, title = { Text("Review extracted facts") },
            text = { Column(Modifier.verticalScroll(rememberScrollState())) {
                Text("AI may misread documents. Select only facts you have checked against the original.", color = AyuvanColors.Warning)
                Spacer(Modifier.height(8.dp))
                listOf("conditions", "medications", "allergies").forEach { kind ->
                    val values = result.optJSONArray(kind)
                    if (values != null) for (i in 0 until values.length()) {
                        val value = values.optString(i)
                        val key = "$kind:$value"
                        Row(verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth().clickable {
                                if (key in selectedFacts) selectedFacts.remove(key) else selectedFacts.add(key)
                            }) {
                            Checkbox(checked = key in selectedFacts, onCheckedChange = {
                                if (it) selectedFacts.add(key) else selectedFacts.remove(key)
                            })
                            Text("$kind: $value")
                        }
                    }
                }
            } }, confirmButton = { TextButton(onClick = {
                val id = doc.optString("id"); val chosen = selectedFacts.toList(); reviewDocument = null
                action { api.review(patientId, id, true,
                    chosen.filter { it.startsWith("conditions:") }.map { it.removePrefix("conditions:") },
                    chosen.filter { it.startsWith("medications:") }.map { it.removePrefix("medications:") },
                    chosen.filter { it.startsWith("allergies:") }.map { it.removePrefix("allergies:") }) }
            }) { Text("Confirm selected") } }, dismissButton = { TextButton(onClick = {
                val id = doc.optString("id"); reviewDocument = null
                action { api.review(patientId, id, false, emptyList(), emptyList(), emptyList()) }
            }) { Text("Reject draft") } })
    }
    if (deleteDocumentId != null) AlertDialog(onDismissRequest = { deleteDocumentId = null },
        title = { Text("Delete document?") },
        text = { Text("This removes the stored file and its extraction draft. Facts you already confirmed in your health record can be removed separately.") },
        confirmButton = { TextButton(onClick = { val id = deleteDocumentId!!; deleteDocumentId = null
            action { api.deleteDocument(patientId, id) }
        }) { Text("Delete", color = AyuvanColors.Danger) } },
        dismissButton = { TextButton(onClick = { deleteDocumentId = null }) { Text("Cancel") } })
    if (previewBytes != null) AlertDialog(onDismissRequest = { previewBytes = null; previewRendered = null },
        title = { Text("Medical document") },
        text = { Column(horizontalAlignment = Alignment.CenterHorizontally) {
            if (previewError != null) Text(previewError!!, color = AyuvanColors.Danger)
            val rendered = previewRendered
            if (rendered == null && previewError == null) CircularProgressIndicator()
            if (rendered != null) {
                Image(bitmap = rendered.bitmap.asImageBitmap(), contentDescription = "Document page",
                    modifier = Modifier.fillMaxWidth().heightIn(max = 460.dp), contentScale = ContentScale.Fit)
                if (rendered.pageCount > 1) Row(verticalAlignment = Alignment.CenterVertically) {
                    TextButton(onClick = { previewPage--; previewRendered = null }, enabled = previewPage > 0) { Text("Previous") }
                    Text("${previewPage + 1} / ${rendered.pageCount}")
                    TextButton(onClick = { previewPage++; previewRendered = null },
                        enabled = previewPage + 1 < rendered.pageCount) { Text("Next") }
                }
            }
        } }, confirmButton = { TextButton(onClick = { previewBytes = null; previewRendered = null }) { Text("Close") } })
}

@Composable
private fun ConnectedCareScreen(api: MobileApi, patientId: String) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var data by remember(patientId) { mutableStateOf<JSONObject?>(null) }
    var error by remember(patientId) { mutableStateOf<String?>(null) }
    var description by rememberSaveable(patientId) { mutableStateOf("") }
    var due by rememberSaveable(patientId) { mutableStateOf("") }
    var editingTaskId by remember(patientId) { mutableStateOf<String?>(null) }
    var showTaskEditor by remember { mutableStateOf(false) }
    var deleteTaskId by remember(patientId) { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    var notificationConsent by remember(patientId) { mutableStateOf(false) }
    val requestPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
    LaunchedEffect(patientId) {
        if (patientId.isNotBlank()) try {
            data = api.care(patientId)
            notificationConsent = api.consents(patientId).list("consents").any {
                it.optString("purpose") == "notifications" && it.optString("status") == "granted"
            }
            ReminderScheduler.reconcile(context, data?.list("tasks") ?: emptyList(), notificationConsent)
        } catch (e: Exception) { error = e.message }
    }
    fun refresh(block: suspend () -> Unit) { scope.launch {
        busy = true; error = null
        try { block(); data = api.care(patientId); ReminderScheduler.reconcile(context, data?.list("tasks") ?: emptyList(), notificationConsent) }
        catch (e: Exception) { error = e.message }
        busy = false
    } }
    val tasks = data?.list("tasks") ?: emptyList()
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(16.dp)); AppHeader(); Spacer(Modifier.height(22.dp))
        Text("My Care", style = MaterialTheme.typography.headlineMedium)
        Text("Today · Focus on what matters next.",
            color = AyuvanColors.SecondaryText)
        Spacer(Modifier.height(16.dp)); LoadError(error)
        Text("Your next actions", style = MaterialTheme.typography.titleLarge)
        if (tasks.isEmpty()) Text("No confirmed tasks yet. You can add a personal reminder below.",
            color = AyuvanColors.SecondaryText, modifier = Modifier.padding(vertical = 12.dp))
        Spacer(Modifier.height(12.dp))
        TextButton(onClick = { showTaskEditor = !showTaskEditor }) {
            Text(if (showTaskEditor) "Close reminder form" else "+ Add a personal reminder")
        }
        if (showTaskEditor || editingTaskId != null) {
        Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(16.dp)) {
                Text(if (editingTaskId == null) "Personal reminder" else "Edit reminder",
                    style = MaterialTheme.typography.titleLarge)
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = description, onValueChange = { description = it.take(1000) },
                    modifier = Modifier.fillMaxWidth(), label = { Text("What do you need to do?") })
                Spacer(Modifier.height(8.dp))
                OutlinedTextField(value = due, onValueChange = { due = it.take(16) },
                    modifier = Modifier.fillMaxWidth(), label = { Text("When (YYYY-MM-DD HH:MM, optional)") })
                Spacer(Modifier.height(10.dp))
                Button(onClick = {
                    val dueAt = try {
                        if (due.isBlank()) null else java.time.LocalDateTime.parse(due,
                            java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"))
                            .atZone(java.time.ZoneId.systemDefault()).toInstant().toString()
                    } catch (_: Exception) { error = "Use YYYY-MM-DD HH:MM for the reminder time"; return@Button }
                    val taskId = editingTaskId
                    val value = description.trim()
                    refresh {
                        if (taskId == null) api.addTask(patientId, value, dueAt)
                        else api.editTask(patientId, taskId, value, dueAt)
                        description = ""; due = ""; editingTaskId = null; showTaskEditor = false
                    }
                }, enabled = !busy && description.trim().length >= 2) {
                    Text(if (editingTaskId == null) "Save reminder" else "Save changes")
                }
            }
        }
        }
        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Notify me about due tasks", modifier = Modifier.weight(1f))
            Checkbox(checked = notificationConsent, onCheckedChange = { checked ->
                refresh { api.setConsent(patientId, "notifications", checked); notificationConsent = checked }
                if (checked && Build.VERSION.SDK_INT >= 33)
                    requestPermission.launch(android.Manifest.permission.POST_NOTIFICATIONS)
            })
        }
        Text("Notifications may arrive around the scheduled time; use your usual medicine alarm for time-critical doses.",
            color = AyuvanColors.MutedText, style = MaterialTheme.typography.bodyMedium)
        Spacer(Modifier.height(14.dp))
        tasks.forEach { task ->
            Card(Modifier.fillMaxWidth().padding(bottom = 8.dp), colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(18.dp)) {
                Column {
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    IconBadge(R.drawable.icon_care_plan, null)
                    Spacer(Modifier.width(12.dp))
                    Column(Modifier.weight(1f)) {
                        Text(task.optString("description"), style = MaterialTheme.typography.titleMedium)
                        Text("${task.optString("status")} · ${task.optString("due_at").take(16)} · ${task.optString("source")}",
                            color = AyuvanColors.SecondaryText)
                    }
                    Checkbox(checked = task.optString("status") == "completed",
                        onCheckedChange = { checked -> refresh { api.updateTask(patientId, task.optString("id"),
                            if (checked) "completed" else "pending") } })
                }
                if (task.optString("source") == "patient_created") Row(
                    Modifier.fillMaxWidth().padding(horizontal = 14.dp), horizontalArrangement = Arrangement.End) {
                    TextButton(onClick = {
                        editingTaskId = task.optString("id")
                        showTaskEditor = true
                        description = task.optString("description")
                        due = try {
                            java.time.Instant.parse(task.optString("due_at"))
                                .atZone(java.time.ZoneId.systemDefault())
                                .format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"))
                        } catch (_: Exception) { "" }
                    }) { Text("Edit") }
                    TextButton(onClick = { deleteTaskId = task.optString("id") }) {
                        Text("Delete", color = AyuvanColors.Danger)
                    }
                }
                }
            }
        }
        Spacer(Modifier.height(28.dp))
    }
    if (deleteTaskId != null) AlertDialog(onDismissRequest = { deleteTaskId = null },
        title = { Text("Delete reminder?") }, text = { Text("This removes the task and its scheduled notification.") },
        confirmButton = { TextButton(onClick = {
            val id = deleteTaskId!!; deleteTaskId = null
            refresh { api.deleteTask(patientId, id); ReminderScheduler.cancel(context, id) }
        }) { Text("Delete", color = AyuvanColors.Danger) } },
        dismissButton = { TextButton(onClick = { deleteTaskId = null }) { Text("Cancel") } })
}

@Composable
private fun ConnectedDiscoverScreen(api: MobileApi, onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var query by rememberSaveable { mutableStateOf("") }
    var area by rememberSaveable { mutableStateOf("") }
    var category by rememberSaveable { mutableStateOf("Doctors") }
    var results by remember { mutableStateOf<JSONObject?>(null) }
    var selectedPlace by remember { mutableStateOf<JSONObject?>(null) }
    var currentLocation by remember { mutableStateOf<LatLng?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val locationPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { granted ->
        if (granted.values.any { it }) scope.launch {
            busy = true; error = null
            try {
                val found = findCurrentArea(context)
                if (found == null) error = "Location is unavailable. Enter a city or neighbourhood instead."
                else {
                    currentLocation = LatLng(found.first.latitude, found.first.longitude)
                    if (found.second.isNotBlank()) area = found.second
                    else error = "We found your location. Enter a nearby city to search facilities."
                }
            } catch (_: SecurityException) { error = "Location permission is needed. You can search by city instead." }
            busy = false
        } else error = "Location permission was declined. You can search by city instead."
    }
    val places = results?.list("places") ?: emptyList()
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") }
                Text("Find care", style = MaterialTheme.typography.titleLarge)
            }
            Spacer(Modifier.height(18.dp))
            Text("Find healthcare near you", style = MaterialTheme.typography.headlineMedium)
            Text("Search by area or service.", color = AyuvanColors.SecondaryText)
            Spacer(Modifier.height(20.dp))
            OutlinedTextField(value = area, onValueChange = { area = it.take(100) },
                modifier = Modifier.fillMaxWidth(), label = { Text("City or neighbourhood") },
                placeholder = { Text("e.g. Andheri, Mumbai") })
            TextButton(onClick = {
                if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
                    ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED)
                    scope.launch {
                        busy = true; error = null
                        try {
                            val found = findCurrentArea(context)
                            if (found != null) {
                                currentLocation = LatLng(found.first.latitude, found.first.longitude)
                                if (found.second.isNotBlank()) area = found.second
                                else error = "Enter a nearby city to search facilities."
                            } else error = "Location unavailable. Search by city instead."
                        } catch (_: SecurityException) { error = "Location permission is needed." }
                        busy = false
                    }
                else locationPermission.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION))
            }) { Text("⌖  Use my current location") }
            OutlinedTextField(value = query, onValueChange = { query = it.take(100) },
                modifier = Modifier.fillMaxWidth(), label = { Text("Specialty or service (optional)") },
                placeholder = { Text("Dermatologist, X-ray…") })
            Spacer(Modifier.height(10.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("Doctors", "Hospitals", "Diagnostics", "Clinics").forEach { item ->
                    AssistChip(onClick = { category = item }, label = { Text(item) },
                        leadingIcon = if (category == item) ({ Icon(Icons.Default.Check, null) }) else null)
                }
            }
            Spacer(Modifier.height(12.dp))
            PrimaryButton(if (busy) "Searching…" else "Search facilities", enabled = !busy && area.trim().length >= 3, onClick = {
                scope.launch { busy = true; error = null
                    try { results = api.discover(query.trim(), category, area.trim()); selectedPlace = null }
                    catch (e: Exception) { error = e.message }; busy = false }
            })
            Spacer(Modifier.height(15.dp)); LoadError(error)
            Text("Map overview", style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(10.dp))
            Card(shape = RoundedCornerShape(20.dp), border = BorderStroke(1.dp, AyuvanColors.Border)) {
                CareMap(places, currentLocation, selectedPlace) { selectedPlace = it }
            }
            Text("Map and facility details from Google Maps", style = MaterialTheme.typography.bodySmall,
                color = AyuvanColors.SecondaryText, modifier = Modifier.padding(vertical = 8.dp))
            if (selectedPlace != null) {
                Text(selectedPlace!!.optString("name"), style = MaterialTheme.typography.titleMedium)
                Text(selectedPlace!!.optString("address"), color = AyuvanColors.SecondaryText)
                TextButton(onClick = {
                    val url = selectedPlace!!.optString("maps_url")
                    if (url.startsWith("https://")) context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                }) { Text("Directions in Google Maps  →") }
            }
            if (results != null) Text("Facilities", style = MaterialTheme.typography.titleLarge)
            if (results != null && places.isEmpty()) EmptyInformationCard(R.drawable.icon_location_pin,
                "No results found", "Try another area or specialty.")
            places.forEach { place ->
                Spacer(Modifier.height(8.dp))
                BasicRowCard(onClick = {
                    selectedPlace = place
                }, leadingIcon = R.drawable.icon_location_pin,
                    title = place.optString("name"), subtitle = place.optString("address"),
                    trailing = { Icon(Icons.AutoMirrored.Filled.ArrowForward, null) })
            }
            if (results == null) Text("Search by area to see live facility results.",
                color = AyuvanColors.SecondaryText)
        }
    }
}

@Composable
private fun ConnectedProfileScreen(api: MobileApi, patientId: String, patients: JSONArray,
                                   onPatientChange: (String) -> Unit, onPatientsRefresh: (JSONArray) -> Unit,
                                   onSignOut: () -> Unit, onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val requestNotificationPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
    var account by remember { mutableStateOf<JSONObject?>(null) }
    var consents by remember(patientId) { mutableStateOf<JSONObject?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var nameDialog by remember { mutableStateOf(false) }
    var newName by remember { mutableStateOf("") }
    var newBirthDate by remember { mutableStateOf("") }
    var newSex by remember { mutableStateOf("") }
    var linkDialog by remember { mutableStateOf(false) }
    var linkCode by remember { mutableStateOf("") }
    var deleteDialog by remember { mutableStateOf(false) }
    var changePasswordDialog by remember { mutableStateOf(false) }
    var currentPassword by remember { mutableStateOf("") }
    var nextPassword by remember { mutableStateOf("") }
    var whatsappDeleteDialog by remember { mutableStateOf(false) }
    var deletePassword by remember { mutableStateOf("") }
    var exportPayload by remember { mutableStateOf<String?>(null) }
    var busy by remember { mutableStateOf(false) }
    val exportLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        if (uri != null) try {
            context.contentResolver.openOutputStream(uri)?.use { it.write((exportPayload ?: "{}").toByteArray()) }
            message = "Export saved to your chosen location"
        } catch (e: Exception) { error = e.message }
    }
    LaunchedEffect(patientId) { try { account = api.me(); consents = api.consents(patientId) }
        catch (e: Exception) { error = e.message } }
    fun action(block: suspend () -> Unit) { scope.launch { busy = true; error = null; message = null
        try { block(); account = api.me()
            if (account?.optJSONArray("patients")?.rows()?.any { it.optString("id") == patientId } == true)
                consents = api.consents(patientId)
        }
        catch (e: Exception) { error = e.message }
        busy = false
    } }
    val current = patients.rows().firstOrNull { it.optString("id") == patientId }
    val consentRows = consents?.list("consents") ?: emptyList()
    fun granted(purpose: String) = consentRows.firstOrNull { it.optString("purpose") == purpose }
        ?.optString("status") == "granted"
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(12.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Back") }
            Text("Account", style = MaterialTheme.typography.titleLarge)
        }
        Spacer(Modifier.height(22.dp))
        Text("Profile", style = MaterialTheme.typography.displaySmall)
        Text("Manage your account, family, preferences and privacy.", color = AyuvanColors.SecondaryText)
        Spacer(Modifier.height(16.dp)); LoadError(error)
        if (message != null) Text(message!!, color = AyuvanColors.Success)
        Card(colors = CardDefaults.cardColors(containerColor = Color.White), shape = RoundedCornerShape(20.dp)) {
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Image(painterResource(R.drawable.avatar_default), null, Modifier.size(54.dp).clip(CircleShape))
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f)) {
                    Text(current?.optString("display_name") ?: "My Profile", style = MaterialTheme.typography.titleMedium)
                    Text(account?.optString("phone") ?: "", color = AyuvanColors.SecondaryText)
                }
                TextButton(onClick = {
                    newName = current?.optString("display_name") ?: ""
                    newBirthDate = current?.optString("date_of_birth")?.takeUnless { it == "null" } ?: ""
                    newSex = current?.optString("sex")?.takeUnless { it == "null" } ?: ""
                    nameDialog = true
                }) { Text("Edit") }
            }
        }
        Spacer(Modifier.height(20.dp))
        Text("My Profiles", style = MaterialTheme.typography.titleLarge)
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            patients.rows().forEach { p ->
                ProfileChip(p.optString("display_name"), p.optString("id") == patientId) {
                    onPatientChange(p.optString("id"))
                }
            }
        }
        Spacer(Modifier.height(20.dp))
        Text("Language", style = MaterialTheme.typography.titleLarge)
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("English" to "en", "हिंदी" to "hi", "मराठी" to "mr", "தமிழ்" to "ta").forEach { (label, code) ->
                AssistChip(onClick = { action { api.updateProfile(patientId, language = code)
                    onPatientsRefresh(api.me().optJSONArray("patients") ?: JSONArray()) } },
                    label = { Text(label) }, leadingIcon = if (current?.optString("preferred_language") == code)
                        ({ Icon(Icons.Default.Check, null) }) else null)
            }
        }
        Spacer(Modifier.height(20.dp))
        Text("Privacy choices", style = MaterialTheme.typography.titleLarge)
        listOf("health_processing" to "Health record processing", "ai_assistance" to "AI assistance",
            "notifications" to "Reminder notifications").forEach { (purpose, label) ->
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text(label, modifier = Modifier.weight(1f))
                Checkbox(checked = granted(purpose), onCheckedChange = { checked ->
                    action {
                        api.setConsent(patientId, purpose, checked)
                        if (purpose == "notifications") ReminderScheduler.reconcile(
                            context, api.care(patientId).list("tasks"), checked)
                    }
                    if (purpose == "notifications" && checked && Build.VERSION.SDK_INT >= 33)
                        requestNotificationPermission.launch(android.Manifest.permission.POST_NOTIFICATIONS)
                })
            }
        }
        Spacer(Modifier.height(12.dp))
        OutlinedButton(onClick = { action {
            val result = api.requestWhatsAppLink()
            if (result.optString("status") == "code_sent") {
                linkDialog = true
                message = "We sent a code to your WhatsApp number. Enter it here."
            } else {
                onPatientsRefresh(result.optJSONArray("patients") ?: JSONArray())
                message = "Your WhatsApp history and app health record are connected."
            }
        } }, modifier = Modifier.fillMaxWidth(), enabled = !busy) { Text("Link WhatsApp history") }
        Text("Linking requires a code sent to your WhatsApp. Your phone and password alone cannot expose an existing medical record.",
            style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText)
        if (patients.rows().any { it.optString("role") == "linked" }) TextButton(
            onClick = { whatsappDeleteDialog = true }, modifier = Modifier.fillMaxWidth()) {
            Text("Delete linked WhatsApp health history", color = AyuvanColors.Danger)
        }
        Spacer(Modifier.height(12.dp))
        OutlinedButton(onClick = { scope.launch { try {
            exportPayload = api.export().toString(2); exportLauncher.launch("ayuvan-data.json")
        } catch (e: Exception) { error = e.message } } }, modifier = Modifier.fillMaxWidth()) { Text("Download my data") }
        OutlinedButton(onClick = {
            context.startActivity(Intent(Intent.ACTION_VIEW,
                Uri.parse("https://karann0077.github.io/Ayuvan-AI/privacy/")))
        }, modifier = Modifier.fillMaxWidth()) { Text("Privacy policy") }
        OutlinedButton(onClick = {
            context.startActivity(Intent(Intent.ACTION_VIEW,
                Uri.parse("https://karann0077.github.io/Ayuvan-AI/terms/")))
        }, modifier = Modifier.fillMaxWidth()) { Text("Terms of service") }
        OutlinedButton(onClick = {
            context.startActivity(Intent(Intent.ACTION_SENDTO,
                Uri.parse("mailto:rajkaran3765@gmail.com?subject=AYUVAN%20app%20support")))
        }, modifier = Modifier.fillMaxWidth()) { Text("Help and support") }
        OutlinedButton(onClick = {
            context.startActivity(Intent(Intent.ACTION_VIEW,
                Uri.parse("https://karann0077.github.io/Ayuvan-AI/data-deletion/")))
        }, modifier = Modifier.fillMaxWidth()) { Text("Data deletion information") }
        Spacer(Modifier.height(12.dp))
        OutlinedButton(onClick = { scope.launch { try { api.logout() } catch (_: Exception) { api.clearSession() }
            onSignOut() } }, modifier = Modifier.fillMaxWidth()) { Text("Sign out") }
        OutlinedButton(onClick = { changePasswordDialog = true }, modifier = Modifier.fillMaxWidth()) {
            Text("Change password")
        }
        TextButton(onClick = { deleteDialog = true }, modifier = Modifier.fillMaxWidth()) {
            Text("Delete account and app-owned data", color = AyuvanColors.Danger)
        }
        Spacer(Modifier.height(26.dp))
    }
    if (nameDialog) AlertDialog(onDismissRequest = { nameDialog = false }, title = { Text("Edit profile") },
        text = { Column(Modifier.verticalScroll(rememberScrollState())) {
            OutlinedTextField(value = newName, onValueChange = { newName = it.take(160) }, label = { Text("Name") })
            OutlinedTextField(value = newBirthDate, onValueChange = { newBirthDate = it.take(10) },
                label = { Text("Date of birth (YYYY-MM-DD)") })
            Row(Modifier.horizontalScroll(rememberScrollState())) {
                listOf("woman", "man", "other", "prefer_not_to_say").forEach { item ->
                    AssistChip(onClick = { newSex = item }, label = { Text(item.replace('_', ' ')) },
                        leadingIcon = if (newSex == item) ({ Icon(Icons.Default.Check, null) }) else null)
                }
            }
        } },
        confirmButton = { TextButton(onClick = { nameDialog = false; action {
            api.updateProfile(patientId, name = newName.trim(), dateOfBirth = newBirthDate, sex = newSex)
            onPatientsRefresh(api.me().optJSONArray("patients") ?: JSONArray())
        } }, enabled = newName.trim().length >= 2) { Text("Save") } },
        dismissButton = { TextButton(onClick = { nameDialog = false }) { Text("Cancel") } })
    if (linkDialog) AlertDialog(onDismissRequest = { linkDialog = false }, title = { Text("Verify WhatsApp link") },
        text = { OutlinedTextField(value = linkCode, onValueChange = { linkCode = it.filter(Char::isDigit).take(6) },
            label = { Text("Six-digit code") }, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)) },
        confirmButton = { TextButton(onClick = { linkDialog = false; action {
            val linked = api.verifyWhatsAppLink(linkCode)
            val linkedPatients = linked.optJSONArray("patients") ?: JSONArray()
            onPatientsRefresh(linkedPatients)
            linkedPatients.rows().firstOrNull { it.optString("role") == "owner" && it.optString("relationship") == "self" }
                ?.optString("id")?.let(onPatientChange)
            message = "Your WhatsApp history and app health record are now combined."
        } }, enabled = linkCode.length == 6) { Text("Link") } },
        dismissButton = { TextButton(onClick = { linkDialog = false }) { Text("Cancel") } })
    if (deleteDialog) AlertDialog(onDismissRequest = { deleteDialog = false }, title = { Text("Delete account?") },
        text = { Column {
            Text(if (patients.rows().any { it.optString("role") == "linked" })
                "This deletes your app account and app-owned profiles. A separately linked WhatsApp record remains until you delete it separately."
                else "This permanently deletes your account and AYUVAN health data, including any WhatsApp history combined with it.")
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(value = deletePassword, onValueChange = { deletePassword = it },
                label = { Text("Confirm password") },
                visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation())
        } }, confirmButton = { TextButton(onClick = { deleteDialog = false; scope.launch {
            try { api.deleteAccount(deletePassword); api.clearSession(); onSignOut() }
            catch (e: Exception) { error = e.message }
        } }, enabled = deletePassword.isNotBlank()) { Text("Delete", color = AyuvanColors.Danger) } },
        dismissButton = { TextButton(onClick = { deleteDialog = false }) { Text("Cancel") } })
    if (whatsappDeleteDialog) AlertDialog(onDismissRequest = { whatsappDeleteDialog = false },
        title = { Text("Delete WhatsApp history?") }, text = { Column {
            Text("This permanently deletes the AYUVAN health record linked from this WhatsApp number. Confirm with your account password.")
            OutlinedTextField(value = deletePassword, onValueChange = { deletePassword = it },
                label = { Text("Password") },
                visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation())
        } }, confirmButton = { TextButton(onClick = { whatsappDeleteDialog = false; action {
            api.deleteLinkedWhatsAppData(deletePassword)
            val updated = api.me().optJSONArray("patients") ?: JSONArray()
            onPatientsRefresh(updated)
            onPatientChange(updated.optJSONObject(0)?.optString("id") ?: "")
            message = "Linked WhatsApp health history deleted"
        } }, enabled = deletePassword.isNotBlank()) { Text("Delete", color = AyuvanColors.Danger) } },
        dismissButton = { TextButton(onClick = { whatsappDeleteDialog = false }) { Text("Cancel") } })
    if (changePasswordDialog) AlertDialog(onDismissRequest = { changePasswordDialog = false },
        title = { Text("Change password") }, text = { Column {
            OutlinedTextField(value = currentPassword, onValueChange = { currentPassword = it },
                label = { Text("Current password") },
                visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation())
            OutlinedTextField(value = nextPassword, onValueChange = { nextPassword = it },
                label = { Text("New password (at least 10 characters)") },
                visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation())
        } }, confirmButton = { TextButton(onClick = {
            val oldValue = currentPassword
            val newValue = nextPassword
            changePasswordDialog = false
            action { api.changePassword(oldValue, newValue); message = "Password changed. Other sessions were signed out." }
            currentPassword = ""; nextPassword = ""
        }, enabled = currentPassword.isNotBlank() && nextPassword.length >= 10) { Text("Update") } },
        dismissButton = { TextButton(onClick = { changePasswordDialog = false }) { Text("Cancel") } })
}
