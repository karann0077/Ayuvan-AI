package com.ayuvan.mobile.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.ayuvan.mobile.R

@Composable
internal fun AyuIcon(res: Int, label: String?, modifier: Modifier = Modifier.size(24.dp)) {
    Image(painter = painterResource(res), contentDescription = label, modifier = modifier,
        contentScale = ContentScale.Fit)
}

@Composable
internal fun AyuBrandHeader(onProfile: () -> Unit, onNotifications: () -> Unit) {
    Row(Modifier.fillMaxWidth().height(58.dp).padding(horizontal = 20.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Image(painterResource(R.drawable.ayu_brand_mark), null, Modifier.size(34.dp))
        Spacer(Modifier.width(6.dp))
        Text("AYUVAN", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = AyuvanColors.Brand700,
            modifier = Modifier.weight(1f))
        IconButton(onClick = onNotifications, modifier = Modifier.size(48.dp)) {
            AyuIcon(R.drawable.ayu_bell, "Notifications")
        }
        IconButton(onClick = onProfile, modifier = Modifier.size(48.dp)) {
            AyuIcon(R.drawable.ayu_user, "Profile")
        }
    }
}

@Composable
internal fun AyuPageHeader(title: String, onBack: () -> Unit, onHelp: (() -> Unit)? = null) {
    Row(Modifier.fillMaxWidth().height(58.dp).padding(horizontal = 12.dp),
        verticalAlignment = Alignment.CenterVertically) {
        IconButton(onClick = onBack, modifier = Modifier.size(48.dp)) {
            AyuIcon(R.drawable.ayu_chevron_left, "Back")
        }
        Text(title, modifier = Modifier.weight(1f), textAlign = TextAlign.Center,
            color = AyuvanColors.Text, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
        if (onHelp != null) IconButton(onClick = onHelp, modifier = Modifier.size(48.dp)) {
            AyuIcon(R.drawable.ayu_help_circle, "Help")
        } else Spacer(Modifier.width(48.dp))
    }
}

@Composable
internal fun AyuTitle(title: String, subtitle: String? = null) {
    Column(Modifier.fillMaxWidth()) {
        Text(title, fontSize = 27.sp, lineHeight = 31.sp, fontWeight = FontWeight.Bold,
            color = AyuvanColors.Text)
        if (!subtitle.isNullOrBlank()) {
            Spacer(Modifier.height(6.dp))
            Text(subtitle, fontSize = 14.sp, lineHeight = 20.sp, color = AyuvanColors.SecondaryText)
        }
    }
}

@Composable
internal fun AyuCardRow(icon: Int, title: String, subtitle: String? = null, onClick: () -> Unit,
                        modifier: Modifier = Modifier, trailing: Boolean = true) {
    Card(modifier.fillMaxWidth().clickable(onClick = onClick), shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(42.dp).background(AyuvanColors.Brand100, RoundedCornerShape(12.dp)),
                contentAlignment = Alignment.Center) { AyuIcon(icon, null, Modifier.size(21.dp)) }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(title, fontSize = 15.sp, lineHeight = 19.sp, fontWeight = FontWeight.SemiBold,
                    color = AyuvanColors.Text)
                if (!subtitle.isNullOrBlank()) {
                    Spacer(Modifier.height(2.dp))
                    Text(subtitle, fontSize = 12.sp, lineHeight = 17.sp,
                        color = AyuvanColors.SecondaryText)
                }
            }
            if (trailing) {
                Spacer(Modifier.width(8.dp))
                AyuIcon(R.drawable.ayu_chevron_right, null, Modifier.size(20.dp))
            }
        }
    }
}

@Composable
internal fun AyuDetailRow(icon: Int, title: String, detail: String,
                          modifier: Modifier = Modifier) {
    Card(modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, AyuvanColors.Border)) {
        Row(Modifier.fillMaxWidth().padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            AyuIcon(icon, null, Modifier.size(23.dp))
            Spacer(Modifier.width(12.dp))
            Column {
                Text(title, fontSize = 14.sp, fontWeight = FontWeight.SemiBold,
                    color = AyuvanColors.Text)
                Spacer(Modifier.height(3.dp))
                Text(detail, fontSize = 12.sp, lineHeight = 17.sp,
                    color = AyuvanColors.SecondaryText)
            }
        }
    }
}

@Composable
internal fun AyuPrimaryButton(label: String, onClick: () -> Unit, enabled: Boolean = true,
                              modifier: Modifier = Modifier) {
    Button(onClick = onClick, enabled = enabled, modifier = modifier.fillMaxWidth().height(52.dp),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = AyuvanColors.Brand700)) {
        Text(label, fontSize = 15.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
internal fun AyuEmpty(illustration: Int, title: String, body: String, action: String? = null,
                      onAction: (() -> Unit)? = null) {
    Column(Modifier.fillMaxWidth().padding(vertical = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally) {
        Image(painterResource(illustration), null, Modifier.size(128.dp))
        Spacer(Modifier.height(12.dp))
        Text(title, fontSize = 17.sp, fontWeight = FontWeight.SemiBold, color = AyuvanColors.Text)
        Spacer(Modifier.height(4.dp))
        Text(body, fontSize = 13.sp, color = AyuvanColors.SecondaryText,
            textAlign = TextAlign.Center, lineHeight = 19.sp)
        if (action != null && onAction != null) {
            Spacer(Modifier.height(16.dp))
            AyuPrimaryButton(action, onAction)
        }
    }
}

@Composable
internal fun AyuSegment(labels: List<String>, selected: String, onSelect: (String) -> Unit) {
    Row(Modifier.fillMaxWidth().background(AyuvanColors.SurfaceSubtle, RoundedCornerShape(14.dp))
        .padding(4.dp), horizontalArrangement = Arrangement.spacedBy(3.dp)) {
        labels.forEach { label ->
            val active = label == selected
            Box(Modifier.weight(1f).height(42.dp)
                .background(if (active) Color.White else Color.Transparent, RoundedCornerShape(11.dp))
                .clickable { onSelect(label) }, contentAlignment = Alignment.Center) {
                Text(label, fontSize = 13.sp, maxLines = 1,
                    fontWeight = if (active) FontWeight.SemiBold else FontWeight.Normal,
                    color = if (active) AyuvanColors.Brand700 else AyuvanColors.SecondaryText)
            }
        }
    }
}
