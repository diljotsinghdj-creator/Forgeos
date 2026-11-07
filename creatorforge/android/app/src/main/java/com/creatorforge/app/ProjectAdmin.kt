package com.creatorforge.app

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import com.creatorforge.app.model.CreatorProject

/** Rename / delete controls for a phone-side project. */
@Composable
fun ProjectAdmin(p: CreatorProject, projects: List<CreatorProject>, persist: (List<CreatorProject>) -> Unit) {
    var renaming by remember { mutableStateOf(false) }
    var confirmDelete by remember { mutableStateOf(false) }
    Row {
        TextButton({ renaming = true }) { Text("RENAME") }
        TextButton({ confirmDelete = true }) { Text("DELETE", color = Color(0xFFE57373)) }
    }
    if (renaming) {
        var title by remember { mutableStateOf(p.title) }
        AlertDialog(
            onDismissRequest = { renaming = false },
            title = { Text("Rename project") },
            text = { OutlinedTextField(title, { title = it }, Modifier.fillMaxWidth(), singleLine = true) },
            confirmButton = {
                Button({ persist(projects.map { if (it.id == p.id) it.copy(title = title.trim().take(80)) else it }); renaming = false },
                    enabled = title.isNotBlank()) { Text("SAVE") }
            },
            dismissButton = { TextButton({ renaming = false }) { Text("CANCEL") } }
        )
    }
    if (confirmDelete) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Delete '${p.title.take(40)}'?") },
            text = { Text("The project and its phone-made voice and title cards are removed. Exported videos you saved stay in your gallery.") },
            confirmButton = {
                Button({
                    p.scenes.forEach { s -> listOfNotNull(s.visualAssetPath, s.audioAssetPath).forEach { java.io.File(it).delete() } }
                    persist(projects.filter { it.id != p.id })
                    confirmDelete = false
                }) { Text("DELETE") }
            },
            dismissButton = { TextButton({ confirmDelete = false }) { Text("CANCEL") } }
        )
    }
}
