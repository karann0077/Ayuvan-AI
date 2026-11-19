package com.ayuvan.mobile.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

object AyuvanColors {
    val Brand900 = Color(0xFF084A39)
    val Brand800 = Color(0xFF0A5542)
    val Brand700 = Color(0xFF0C5F4A)
    val Brand600 = Color(0xFF147A56)
    val Brand500 = Color(0xFF2C9872)
    val Brand200 = Color(0xFFBDE9CC)
    val Brand100 = Color(0xFFE8F6EE)
    val Brand50 = Color(0xFFF2F7F4)
    val Page = Color(0xFFF8FAF9)
    val Surface = Color(0xFFFFFFFF)
    val SurfaceSubtle = Color(0xFFF2F7F4)
    val Text = Color(0xFF18342F)
    val SecondaryText = Color(0xFF60756B)
    val MutedText = Color(0xFF7C8F85)
    val Border = Color(0xFFDCE8DF)
    val Success = Color(0xFF147A56)
    val SuccessBg = Color(0xFFE5F5EC)
    val Warning = Color(0xFF996112)
    val WarningBg = Color(0xFFFFF4DD)
    val Danger = Color(0xFFBD2C3D)
    val DangerBg = Color(0xFFFFF0F1)
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
