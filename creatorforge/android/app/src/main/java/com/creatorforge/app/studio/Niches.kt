package com.creatorforge.app.studio

/** Which communities, news searches and YouTube categories feed each niche. All free; YouTube needs a free key. */
data class Niche(
    val id: String, val name: String, val subreddits: List<String> = emptyList(), val newsQuery: String = "",
    val hnQuery: String? = null, val youtubeCategory: String = "", val youtubeQuery: String = "", val wikipedia: Boolean = false,
    val keywords: List<String> = emptyList()
)

object Niches {
    val all: List<Niche> = listOf(
        Niche("all", "Everything", listOf("popular"), "", "", "", "", true),
        Niche("tech", "Tech & Gadgets", listOf("technology", "gadgets", "Futurology"), "technology", "", "28", "tech news"),
        Niche("ai", "AI", listOf("artificial", "OpenAI", "singularity", "LocalLLaMA"), "artificial intelligence", "AI", "28", "artificial intelligence",
            keywords = listOf("ai", "artificial", "openai", "chatgpt", "gemini", "claude", "llm", "robot", "nvidia")),
        Niche("money", "Money & Finance", listOf("personalfinance", "investing", "stocks", "Economics"), "economy OR stock market OR inflation", null, "", "personal finance",
            keywords = listOf("stock", "market", "economy", "inflation", "bank", "tax", "price", "dollar", "pound")),
        Niche("business", "Business & Side Hustles", listOf("Entrepreneur", "sidehustle", "smallbusiness", "startups"), "business", "startup", "", "side hustle"),
        Niche("crypto", "Crypto", listOf("CryptoCurrency", "Bitcoin", "ethereum"), "crypto OR bitcoin", "crypto", "", "bitcoin",
            keywords = listOf("bitcoin", "crypto", "ethereum", "coin", "blockchain")),
        Niche("science", "Science & Space", listOf("science", "space", "Physics"), "science OR space OR NASA", "", "28", "science explained",
            keywords = listOf("nasa", "space", "planet", "science", "species", "comet", "asteroid", "moon", "mars")),
        Niche("history", "History", listOf("history", "AskHistorians", "ArtefactPorn", "HistoryPorn"), "history OR archaeology OR ancient", null, "27", "history documentary", true,
            keywords = listOf("history", "ancient", "war", "empire", "king", "queen", "battle", "century", "dynasty")),
        Niche("mystery", "Mystery & True Crime", listOf("UnresolvedMysteries", "TrueCrime", "RBI", "Paranormal"), "mystery OR unsolved OR investigation", null, "", "unsolved mystery", true,
            keywords = listOf("murder", "case", "missing", "killer", "mystery", "trial", "crime")),
        Niche("facts", "Facts & Curiosities", listOf("todayilearned", "interestingasfuck", "Damnthatsinteresting", "coolguides"), "", null, "27", "facts you didn't know"),
        Niche("motivation", "Motivation & Self-improvement", listOf("getdisciplined", "selfimprovement", "GetMotivated", "productivity"), "productivity OR motivation", null, "26", "motivation"),
        Niche("health", "Health & Fitness", listOf("Fitness", "nutrition", "loseit", "running"), "health OR fitness OR diet", null, "26", "fitness tips"),
        Niche("gaming", "Gaming", listOf("gaming", "Games", "pcgaming", "NintendoSwitch"), "video games", "game", "20", "gaming"),
        Niche("entertainment", "Movies, TV & Music", listOf("movies", "television", "Music", "popculturechat"), "film OR TV series OR album", null, "24", "trailer", true),
        Niche("sports", "Sports", listOf("sports", "soccer", "nba", "formula1"), "sport", null, "17", "highlights", true,
            keywords = listOf("fc", "football", "league", "cup", "championship", "grand prix", "nba", "nfl", "season", "fifa", "olympic")),
        Niche("custom", "My keyword"),
    )
    private val byId = all.associateBy { it.id }
    operator fun get(id: String): Niche = byId[id] ?: byId.getValue("all")
    fun exists(id: String) = id in byId
}

data class Region(val id: String, val name: String, val hl: String, val ceid: String, val wiki: String = "en.wikipedia")

object Regions {
    val all = listOf(
        Region("GB", "UK", "en-GB", "GB:en"), Region("US", "US", "en-US", "US:en"), Region("IN", "India", "en-IN", "IN:en"),
        Region("CA", "Canada", "en-CA", "CA:en"), Region("AU", "Australia", "en-AU", "AU:en"),
    )
    operator fun get(id: String): Region = all.firstOrNull { it.id == id } ?: all[0]
}

/** Director Mode looks, identical to the worker's, so prompts made on the phone match what the studio renders. */
object Styles {
    val presets: List<Triple<String, String, String>> = listOf(
        Triple("cinematic", "Cinematic film", "cinematic film still, anamorphic lens, dramatic volumetric lighting, film grain, teal and orange grade, shallow depth of field"),
        Triple("hyperreal", "Hyper-realistic", "hyper-realistic photograph, 8k detail, natural skin texture, real-world lighting, shot on a full-frame camera, 50mm lens, true-to-life colors"),
        Triple("documentary", "Documentary", "documentary photography, natural available light, candid, realistic textures, handheld feel, muted natural colors"),
        Triple("animated_3d", "3D animated", "high-end 3D animated feature film style, expressive stylized characters, soft global illumination, subsurface scattering, vibrant colors"),
        Triple("anime", "Anime", "anime key visual, cel shading, crisp line art, vivid colors, detailed painted background"),
        Triple("claymation", "Claymation", "stop-motion claymation style, handmade clay figures, visible fingerprints, miniature set, soft studio lighting"),
        Triple("watercolor", "Watercolor", "watercolor illustration, soft washes, paper texture, gentle hand-drawn lines"),
        Triple("comic", "Comic book", "comic book art, bold ink outlines, halftone shading, dynamic composition, saturated colors"),
    )
    fun prompt(id: String): String = presets.firstOrNull { it.first == id }?.third ?: id.ifBlank { presets[0].third }
    fun name(id: String): String = presets.firstOrNull { it.first == id }?.second ?: id

    val templates = listOf("shorts_cinematic" to "Cinematic Short (9:16)", "reels_punchy" to "Punchy Reel (9:16)",
        "square_social" to "Square (1:1)", "explainer" to "Explainer (16:9)", "youtube_longform" to "YouTube Documentary (16:9)")
    val sceneSeconds = mapOf("shorts_cinematic" to 5.0, "reels_punchy" to 3.5, "explainer" to 7.0, "youtube_longform" to 10.0, "square_social" to 4.5)

    const val NEGATIVE = "text, watermark, logo, caption, subtitles, letters, signature, blurry, low quality, jpeg artifacts, deformed, distorted face, extra fingers, extra limbs"
}
