package com.ayuvan.mobile.ui

import android.content.Context
import android.location.Geocoder
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Looper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import java.util.Locale
import kotlin.coroutines.resume

/** Called only after the user taps Use my location and grants OS permission. */
suspend fun findCurrentArea(context: Context): Pair<Location, String>? {
    val manager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    val provider = listOf(LocationManager.NETWORK_PROVIDER, LocationManager.GPS_PROVIDER)
        .firstOrNull { manager.isProviderEnabled(it) } ?: return null
    val location = withTimeoutOrNull(12_000) {
        suspendCancellableCoroutine<Location?> { continuation ->
            if (Build.VERSION.SDK_INT >= 30) {
                val cancellation = android.os.CancellationSignal()
                manager.getCurrentLocation(provider, cancellation, context.mainExecutor) {
                    if (continuation.isActive) continuation.resume(it)
                }
                continuation.invokeOnCancellation { cancellation.cancel() }
            } else {
                val listener = LocationListener { result ->
                    if (continuation.isActive) continuation.resume(result)
                }
                manager.requestSingleUpdate(provider, listener, Looper.getMainLooper())
                continuation.invokeOnCancellation { manager.removeUpdates(listener) }
            }
        }
    } ?: return null
    val area = withContext(Dispatchers.IO) {
        runCatching {
            @Suppress("DEPRECATION")
            val address = Geocoder(context, Locale.getDefault())
                .getFromLocation(location.latitude, location.longitude, 1)?.firstOrNull()
            listOfNotNull(address?.locality, address?.adminArea).distinct().joinToString(", ")
        }.getOrDefault("")
    }
    return location to area
}
