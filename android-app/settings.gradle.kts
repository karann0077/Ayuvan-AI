pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        System.getenv("AYUVAN_MAVEN_PROXY")?.let { proxy ->
            maven {
                url = uri(proxy)
                isAllowInsecureProtocol = true
                content { includeGroup("com.google.android.gms") }
            }
        }
        google()
        mavenCentral()
    }
}

rootProject.name = "AyuvanAndroid"
include(":app")
