plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.ayuvan.mobile"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.ayuvan.mobile"
        minSdk = 26
        targetSdk = 36
        versionCode = 2
        versionName = "0.2.0"
        val apiBaseUrl = providers.gradleProperty("ayuvanApiBaseUrl")
            .orElse("https://ayuvan-api-516889485331.asia-south1.run.app").get()
        buildConfigField("String", "API_BASE_URL", "\"$apiBaseUrl\"")
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.material.icons)
    implementation("androidx.work:work-runtime-ktx:2.10.5")
    debugImplementation(libs.androidx.compose.ui.tooling)
}
