package com.ayuvan.mobile.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

object AyuvanColors {
    val Brand900 = Color(0xFF35145E)
    val Brand800 = Color(0xFF482078)
    val Brand700 = Color(0xFF5B2A91)
    val Brand600 = Color(0xFF7040AD)
    val Brand500 = Color(0xFF895CCB)
    val Brand200 = Color(0xFFE1D2F5)
    val Brand100 = Color(0xFFF0E8FA)
    val Brand50 = Color(0xFFF8F4FC)
    val Page = Color(0xFFFBF9FD)
    val Surface = Color(0xFFFFFFFF)
    val SurfaceSubtle = Color(0xFFFCFAFE)
    val Text = Color(0xFF191625)
    val SecondaryText = Color(0xFF514D60)
    val MutedText = Color(0xFF6D687B)
    val Border = Color(0xFFE8E1EF)
    val Success = Color(0xFF216B49)
    val SuccessBg = Color(0xFFE8F5ED)
    val Warning = Color(0xFF8A570B)
    val WarningBg = Color(0xFFFFF4DE)
    val Danger = Color(0xFFA92F40)
    val DangerBg = Color(0xFFFCEBED)
}

private val AyuvanScheme = lightColorScheme(
    primary = AyuvanColors.Brand700,
    onPrimary = Color.White,
    primaryContainer = AyuvanColors.Brand100,
    onPrimaryContainer = AyuvanColors.Brand900,
    secondary = AyuvanColors.Brand600,
    background = AyuvanColors.Page,
    onBackground = AyuvanColors.Text,
    surface = AyuvanColors.Surface,
    onSurface = AyuvanColors.Text,
    surfaceVariant = AyuvanColors.SurfaceSubtle,
    onSurfaceVariant = AyuvanColors.SecondaryText,
    outline = AyuvanColors.Border,
    error = AyuvanColors.Danger,
)

@Composable
fun AyuvanTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = AyuvanScheme,
        typography = AyuvanTypography,
        content = content,
    )
}
