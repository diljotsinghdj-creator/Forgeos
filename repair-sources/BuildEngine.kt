package com.forgeos.app.build

import android.content.Context
import com.forgeos.app.model.*
import java.io.File
import java.util.UUID
import java.util.concurrent.atomic.AtomicReference

class BuildEngine(private val context:Context, private val journal:BuildJournal) {
    private val active=AtomicReference<Process?>(null)
    fun cancel(){ active.getAndSet(null)?.destroyForcibly() }
    fun build(project:ForgeProject, onUpdate:(BuildJob)->Unit):BuildJob {
        val now=System.currentTimeMillis(); var job=BuildJob(UUID.randomUUID().toString(),project.id,"assembleDebug",JobState.QUEUED,now,now)
        fun emit(j:BuildJob){ job=j; journal.upsert(j); onUpdate(j) }
        val root=File(project.rootPath); val wrapper=File(root,"gradlew"); val home=context.filesDir
        val toolchain=ToolchainDetector.detect(home)
        if(!root.isDirectory) { emit(job.copy(state=JobState.FAILED,updatedAt=System.currentTimeMillis(),error="Project directory missing")); return job }
        if(!wrapper.exists() && !toolchain.gradle) { emit(job.copy(state=JobState.FAILED,updatedAt=System.currentTimeMillis(),error="No Gradle wrapper or managed Gradle toolchain installed.")); return job }
        val logDir=File(context.filesDir,"logs").apply{mkdirs()}; val log=File(logDir,"${job.id}.log")
        val command=if(wrapper.exists()) listOf("sh",wrapper.absolutePath,"--no-daemon","assembleDebug") else listOf(File(home,"toolchains/gradle/bin/gradle").absolutePath,"--no-daemon","assembleDebug")
        return try {
            emit(job.copy(state=JobState.RUNNING,updatedAt=System.currentTimeMillis(),logPath=log.absolutePath))
            val pb=ProcessBuilder(command).directory(root).redirectErrorStream(true).redirectOutput(ProcessBuilder.Redirect.appendTo(log))
            pb.environment()["GRADLE_USER_HOME"]=File(context.filesDir,"gradle-cache").absolutePath
            File(context.filesDir,"toolchains/android-sdk").takeIf{it.exists()}?.let { pb.environment()["ANDROID_HOME"]=it.absolutePath; pb.environment()["ANDROID_SDK_ROOT"]=it.absolutePath }
            val p=pb.start(); active.set(p); val code=p.waitFor(); active.compareAndSet(p,null)
            val apk=root.walkTopDown().firstOrNull{it.isFile && it.extension=="apk" && it.path.contains("outputs/apk")}
            if(code==0 && apk!=null && apk.length()>1024) emit(job.copy(state=JobState.SUCCEEDED,updatedAt=System.currentTimeMillis(),exitCode=0,logPath=log.absolutePath,apkPath=apk.absolutePath))
            else emit(job.copy(state=JobState.FAILED,updatedAt=System.currentTimeMillis(),exitCode=code,logPath=log.absolutePath,error="Gradle failed or no valid APK was produced."))
            job
        } catch(t:Throwable){ active.set(null); emit(job.copy(state=JobState.FAILED,updatedAt=System.currentTimeMillis(),logPath=log.absolutePath,error=t.message ?: t.javaClass.simpleName)); job }
    }
}