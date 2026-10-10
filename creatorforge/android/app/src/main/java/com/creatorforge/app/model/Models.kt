package com.creatorforge.app.model

enum class ProjectType { SHORT_FORM, LONG_FORM }
enum class AspectRatio { VERTICAL_9_16, LANDSCAPE_16_9, SQUARE_1_1 }
enum class SceneStatus { PLANNED, GENERATING, READY, FAILED }

data class ContinuityBible(
    val characters: String = "", val locations: String = "", val visualStyle: String = "",
    val lighting: String = "", val cameraLanguage: String = "", val continuityRules: String = ""
) {
    fun promptContext() = """CHARACTERS: $characters
LOCATIONS: $locations
VISUAL STYLE: $visualStyle
LIGHTING: $lighting
CAMERA: $cameraLanguage
CONTINUITY: $continuityRules"""
}

data class Scene(
    val id: String, val order: Int, val title: String, val narration: String,
    val visualPrompt: String, val durationSeconds: Int, val status: SceneStatus = SceneStatus.PLANNED,
    val visualAssetPath: String? = null, val audioAssetPath: String? = null
)

data class CreatorProject(
    val id: String, val title: String, val type: ProjectType, val aspectRatio: AspectRatio,
    val prompt: String, val scenes: List<Scene> = emptyList(),
    val continuityBible: ContinuityBible = ContinuityBible()
)
