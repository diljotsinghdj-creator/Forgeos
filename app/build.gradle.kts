plugins { id("com.android.application") }
android {
 namespace = "com.forgeos.app"
 compileSdk = 35
 defaultConfig { applicationId = "com.forgeos.app"; minSdk = 26; targetSdk = 35; versionCode = 3; versionName = "0.3.0" }
 compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
