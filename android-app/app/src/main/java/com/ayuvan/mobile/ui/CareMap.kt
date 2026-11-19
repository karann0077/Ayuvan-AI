package com.ayuvan.mobile.ui

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.ayuvan.mobile.BuildConfig
import com.google.android.gms.maps.CameraUpdateFactory
import com.google.android.gms.maps.GoogleMap
import com.google.android.gms.maps.MapView
import com.google.android.gms.maps.model.LatLng
import com.google.android.gms.maps.model.LatLngBounds
import com.google.android.gms.maps.model.MarkerOptions
import org.json.JSONObject

/** Keep Google Places result pins on a Google map, with a usable result list below it. */
@Composable
fun CareMap(places: List<JSONObject>, userLocation: LatLng?, selectedPlace: JSONObject?,
            onSelect: (JSONObject) -> Unit) {
    if (!BuildConfig.MAPS_ENABLED) {
        Text("Map unavailable in this build. Facility results remain available below.")
        return
    }
    val context = LocalContext.current
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    val mapView = remember { MapView(context).apply { onCreate(null) } }
    var map by remember { mutableStateOf<GoogleMap?>(null) }
    DisposableEffect(mapView, lifecycle) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> mapView.onStart()
                Lifecycle.Event.ON_RESUME -> mapView.onResume()
                Lifecycle.Event.ON_PAUSE -> mapView.onPause()
                Lifecycle.Event.ON_STOP -> mapView.onStop()
                else -> Unit
            }
        }
        lifecycle.addObserver(observer)
        if (lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) mapView.onStart()
        if (lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) mapView.onResume()
        mapView.getMapAsync { map = it }
        onDispose {
            lifecycle.removeObserver(observer)
            mapView.onPause(); mapView.onStop(); mapView.onDestroy()
        }
    }
    LaunchedEffect(map, places, userLocation, selectedPlace) {
        val googleMap = map ?: return@LaunchedEffect
        googleMap.clear()
        val pins = places.mapNotNull { place ->
            val point = place.optJSONObject("location") ?: return@mapNotNull null
            if (!point.has("latitude") || !point.has("longitude")) return@mapNotNull null
            place to LatLng(point.optDouble("latitude"), point.optDouble("longitude"))
        }
        pins.forEach { (place, point) ->
            googleMap.addMarker(MarkerOptions().position(point).title(place.optString("name")))?.tag = place
        }
        googleMap.setOnMarkerClickListener { marker ->
            (marker.tag as? JSONObject)?.let(onSelect)
            false
        }
        userLocation?.let { googleMap.addMarker(MarkerOptions().position(it).title("Your approximate location")) }
        val selectedPoint = selectedPlace?.optJSONObject("location")?.let {
            if (it.has("latitude") && it.has("longitude")) LatLng(it.optDouble("latitude"), it.optDouble("longitude")) else null
        }
        val center = selectedPoint ?: pins.firstOrNull()?.second ?: userLocation ?: LatLng(20.5937, 78.9629)
        if (selectedPoint != null) googleMap.animateCamera(CameraUpdateFactory.newLatLngZoom(center, 14f))
        else if (pins.size > 1) mapView.post {
            val bounds = LatLngBounds.builder().apply { pins.forEach { include(it.second) } }.build()
            if (mapView.width > 0 && mapView.height > 0)
                googleMap.animateCamera(CameraUpdateFactory.newLatLngBounds(bounds, mapView.width, mapView.height, 56))
            else googleMap.moveCamera(CameraUpdateFactory.newLatLngZoom(center, 12f))
        }
        else googleMap.moveCamera(CameraUpdateFactory.newLatLngZoom(center, if (pins.isEmpty() && userLocation == null) 5f else 12f))
        googleMap.uiSettings.isZoomControlsEnabled = true
    }
    AndroidView(factory = { mapView }, modifier = Modifier.fillMaxWidth().height(300.dp))
}
