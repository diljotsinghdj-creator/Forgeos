package com.forgeos.app.build
import com.forgeos.app.model.ToolchainStatus
import java.io.File
object ToolchainDetector {
 fun detect(home:File):ToolchainStatus {
  fun executable(vararg paths:String)=paths.any{File(it).canExecute()}
  val java=executable("${System.getProperty("java.home")}/bin/java", "${home.path}/toolchains/jdk/bin/java")
  val gradle=File(home,"toolchains/gradle/bin/gradle").canExecute()
  val sdk=File(home,"toolchains/android-sdk/platform-tools").exists() && File(home,"toolchains/android-sdk/build-tools").exists()
  val adb=File(home,"toolchains/android-sdk/platform-tools/adb").canExecute()
  return ToolchainStatus(java,gradle,sdk,adb,"JDK=$java • Gradle=$gradle • Android SDK=$sdk • ADB=$adb")
 }
}