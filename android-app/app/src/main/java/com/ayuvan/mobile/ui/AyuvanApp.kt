@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.ayuvan.mobile.ui

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
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
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
import com.ayuvan.mobile.R

@Composable
fun AyuvanApp() {
    var stepName by rememberSaveable { mutableStateOf(OnboardingStep.WELCOME.name) }
    var finishedOnboarding by rememberSaveable { mutableStateOf(false) }
    var tabName by rememberSaveable { mutableStateOf(MainTab.HOME.name) }
    var showChat by rememberSaveable { mutableStateOf(false) }
    var selectedPatient by rememberSaveable { mutableStateOf("My Profile") }

    val onboardingStep = OnboardingStep.valueOf(stepName)
    val selectedTab = MainTab.valueOf(tabName)

    Surface(modifier = Modifier.fillMaxSize(), color = AyuvanColors.Page) {
        if (!finishedOnboarding) {
            OnboardingFlow(
                step = onboardingStep,
                onStepChange = { stepName = it.name },
                onComplete = { finishedOnboarding = true },
            )
        } else if (showChat) {
            ChatScreen(
                patientName = selectedPatient,
                onBack = { showChat = false },
            )
        } else {
            MainShell(
                selectedTab = selectedTab,
                selectedPatient = selectedPatient,
                onPatientChange = { selectedPatient = it },
                onTabChange = { tabName = it.name },
                onOpenChat = { showChat = true },
            )
        }
    }
}

@Composable
private fun OnboardingFlow(
    step: OnboardingStep,
    onStepChange: (OnboardingStep) -> Unit,
    onComplete: () -> Unit,
) {
    when (step) {
        OnboardingStep.WELCOME -> WelcomeScreen(
            onStart = { onStepChange(OnboardingStep.INTRO) },
            onExistingAccount = { onStepChange(OnboardingStep.PHONE) },
        )
        OnboardingStep.INTRO -> IntroductionScreen(onNext = { onStepChange(OnboardingStep.PHONE) })
        OnboardingStep.PHONE -> PhoneScreen(onNext = { onStepChange(OnboardingStep.LANGUAGE) })
        OnboardingStep.LANGUAGE -> LanguageScreen(onNext = { onStepChange(OnboardingStep.CONSENT) })
        OnboardingStep.CONSENT -> ConsentScreen(onNext = { onStepChange(OnboardingStep.PROFILE) })
        OnboardingStep.PROFILE -> ProfileSetupScreen(onNext = { onStepChange(OnboardingStep.FAMILY) })
        OnboardingStep.FAMILY -> FamilyScreen(onNext = { onStepChange(OnboardingStep.COMPLETE) })
        OnboardingStep.COMPLETE -> SetupCompleteScreen(onComplete = onComplete)
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
private fun PhoneScreen(onNext: () -> Unit) {
    var phone by rememberSaveable { mutableStateOf("") }
    OnboardingBackground {
        Column(
            modifier = Modifier.fillMaxSize().padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            BrandMark()
            Spacer(Modifier.height(44.dp))
            Text("Sign in to continue", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(8.dp))
            Text("We'll send a one-time password to verify your number.", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.SecondaryText, textAlign = TextAlign.Center)
            Spacer(Modifier.height(32.dp))
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
            Spacer(Modifier.height(10.dp))
            Text("A real OTP is sent only after this screen is connected to the AYUVAN authentication service.", style = MaterialTheme.typography.bodyMedium, color = AyuvanColors.MutedText)
            Spacer(Modifier.weight(1f))
            PrimaryButton("Send OTP", enabled = phone.length >= 10, onClick = onNext)
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
    selectedTab: MainTab,
    selectedPatient: String,
    onPatientChange: (String) -> Unit,
    onTabChange: (MainTab) -> Unit,
    onOpenChat: () -> Unit,
) {
    Scaffold(
        containerColor = AyuvanColors.Page,
        bottomBar = { MainNavigation(selectedTab, onTabChange) },
    ) { innerPadding ->
        Box(modifier = Modifier.fillMaxSize().padding(innerPadding)) {
            when (selectedTab) {
                MainTab.HOME -> HomeScreen(selectedPatient, onOpenChat, onTabChange)
                MainTab.MY_HEALTH -> MyHealthScreen(selectedPatient, onPatientChange)
                MainTab.CARE_PLAN -> CarePlanScreen()
                MainTab.DISCOVER -> DiscoverScreen()
                MainTab.PROFILE -> ProfileScreen(selectedPatient, onPatientChange)
            }
        }
    }
}

@Composable
private fun MainNavigation(selected: MainTab, onSelect: (MainTab) -> Unit) {
    NavigationBar(containerColor = Color.White, tonalElevation = 2.dp) {
        MainTab.entries.forEach { tab ->
            NavigationBarItem(
                selected = tab == selected,
                onClick = { onSelect(tab) },
                icon = { AssetIcon(tabIcon(tab), tab.label, Modifier.size(25.dp)) },
                label = { Text(tab.label, maxLines = 1, fontSize = 11.sp) },
            )
        }
    }
}

private fun tabIcon(tab: MainTab) = when (tab) {
    MainTab.HOME -> R.drawable.icon_home
    MainTab.MY_HEALTH -> R.drawable.icon_my_health
    MainTab.CARE_PLAN -> R.drawable.icon_care_plan
    MainTab.DISCOVER -> R.drawable.icon_discover
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
private fun AppHeader() {
    Row(modifier = Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Image(painter = painterResource(R.drawable.ayuvan_logo_horizontal), contentDescription = "AYUVAN", modifier = Modifier.width(128.dp).height(40.dp), contentScale = ContentScale.Fit)
        Spacer(Modifier.weight(1f))
        Box(contentAlignment = Alignment.TopEnd) {
            IconButton(onClick = {}) { AssetIcon(R.drawable.icon_notifications, "Notifications", Modifier.size(25.dp)) }
            Box(modifier = Modifier.padding(top = 8.dp, end = 8.dp).size(8.dp).background(AyuvanColors.Brand600, CircleShape))
        }
        Spacer(Modifier.width(5.dp))
        Image(painter = painterResource(R.drawable.avatar_default), contentDescription = "Profile", modifier = Modifier.size(38.dp).clip(CircleShape))
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
            IconBadge(iconRes = R.drawable.icon_microphone, contentDescription = "Start a voice message")
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
    Image(painter = painterResource(R.drawable.ayuvan_logo_horizontal), contentDescription = "AYUVAN", modifier = Modifier.width(142.dp).height(44.dp), contentScale = ContentScale.Fit)
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
