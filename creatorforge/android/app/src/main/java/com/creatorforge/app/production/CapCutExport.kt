package com.creatorforge.app.production

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.os.Build
import android.provider.MediaStore
import java.io.File
import java.util.zip.ZipInputStream

private val CAPCUT_PACKAGES = listOf("com.lemon.lvoverseas", "com.ss.android.ugc.trill.capcut", "com.lemon.lv")

fun isZip(f: File): Boolean = f.length() > 100 && f.inputStream().use { s -> val b = ByteArray(2); s.read(b) == 2 && b[0] == 'P'.code.toByte() && b[1] == 'K'.code.toByte() }

/**
 * Unpacks a CreatorForge export into the phone's gallery so CapCut (or any editor) can import it:
 * scene media -> Movies/Pictures "CreatorForge/<title>", voice-over and music -> Music "CreatorForge/<title>",
 * captions, timeline and publish kit -> Download "CreatorForge/<title>". Returns a short summary.
 */
fun unpackForEditors(context: Context, zip: File, title: String): String {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return "Saved ${zip.name} in app storage - use SHARE to move it (Android 10+ unpacks automatically)"
    val folder = "CreatorForge/" + title.replace(Regex("[^A-Za-z0-9 _-]"), "").trim().take(40).ifBlank { "Export" }
    var media = 0
    ZipInputStream(zip.inputStream()).use { zin ->
        while (true) {
            val e = zin.nextEntry ?: break
            if (e.isDirectory) continue
            val name = e.name.substringAfterLast('/')
            val ext = name.substringAfterLast('.', "").lowercase()
            if (e.name.startsWith("audio/scenes/")) continue // per-scene voice files stay in the zip
            val (collection, mime, root) = when (ext) {
                "mp4" -> Triple(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, "video/mp4", "Movies")
                "png" -> Triple(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, "image/png", "Pictures")
                "jpg", "jpeg" -> Triple(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, "image/jpeg", "Pictures")
                "wav" -> Triple(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, "audio/wav", "Music")
                "mp3" -> Triple(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, "audio/mpeg", "Music")
                "m4a", "aac" -> Triple(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, "audio/mp4", "Music")
                "ogg", "flac" -> Triple(MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, "audio/$ext", "Music")
                else -> Triple(MediaStore.Downloads.EXTERNAL_CONTENT_URI, "text/plain", "Download")
            }
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, name)
                put(MediaStore.MediaColumns.MIME_TYPE, mime)
                put(MediaStore.MediaColumns.RELATIVE_PATH, "$root/$folder")
            }
            val uri = context.contentResolver.insert(collection, values) ?: continue
            context.contentResolver.openOutputStream(uri)?.use { out -> zin.copyTo(out) }
            if (root != "Download") media++
        }
    }
    return "Unpacked $media files into your gallery under $folder (scenes in order 01, 02…; voice-over and music in Music; captions.srt and publish.txt in Downloads)."
}

/** Opens CapCut if it is installed. Returns false when it isn't. */
fun openCapCut(context: Context): Boolean {
    val pm = context.packageManager
    val launch = CAPCUT_PACKAGES.firstNotNullOfOrNull { pm.getLaunchIntentForPackage(it) } ?: return false
    context.startActivity(launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    return true
}
