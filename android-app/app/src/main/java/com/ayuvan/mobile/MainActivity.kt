package com.ayuvan.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.ayuvan.mobile.ui.AyuvanApp
import com.ayuvan.mobile.ui.AyuvanTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AyuvanTheme {
                AyuvanApp()
            }
        }
    }
}
