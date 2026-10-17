package com.creatorforge.app.orchestration

import com.creatorforge.app.generation.*
import com.creatorforge.app.model.*

sealed class SceneGenerationOutcome { data class Success(val scene:Scene):SceneGenerationOutcome(); data class Failure(val scene:Scene,val reason:String):SceneGenerationOutcome() }

class SceneGenerationCoordinator(private val image:ReplicateImageProvider, private val voice:VoiceProvider){
    suspend fun generate(project:CreatorProject, scene:Scene, imageToken:String, voiceToken:String?, voiceId:String?):SceneGenerationOutcome {
        val prompt=listOf(project.continuityBible.promptContext(),scene.visualPrompt).filter{it.isNotBlank()}.joinToString("\n\n")
        val visual=image.generate(imageToken,prompt,project.aspectRatio)
        if(visual is GenerationResult.Failure) return SceneGenerationOutcome.Failure(scene.copy(status=SceneStatus.FAILED),"Image: ${visual.message}")
        visual as GenerationResult.Success
        var audio:String?=scene.audioAssetPath
        if(!voiceToken.isNullOrBlank()&&!voiceId.isNullOrBlank()) when(val v=voice.generate(voiceToken,voiceId,scene.narration)){is GenerationResult.Success->audio=v.file.absolutePath;is GenerationResult.Failure->return SceneGenerationOutcome.Failure(scene.copy(status=SceneStatus.FAILED,visualAssetPath=visual.file.absolutePath),"Voice: ${v.message}")}
        return SceneGenerationOutcome.Success(scene.copy(status=SceneStatus.READY,visualAssetPath=visual.file.absolutePath,audioAssetPath=audio))
    }
    fun recover(scene:Scene):Scene = if(scene.status==SceneStatus.GENERATING) scene.copy(status=SceneStatus.FAILED) else scene
}
