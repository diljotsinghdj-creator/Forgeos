package com.creatorforge.app.production

import android.content.Context
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.creatorforge.app.security.SecureTokenStore
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning

private val Gold = Color(0xFFD4AF37)
private val Danger = Color(0xFFE57373)

/** Connect links (creatorforge://connect?url=…&token=…) arriving from a QR scan or from the phone's camera. */
object WorkerConnect {
    @Volatile var pending: String? = null

    /** Saves the worker address and token from a connect link or a plain URL. Returns a message for the user. */
    fun apply(context: Context, raw: String): String {
        val text = raw.trim()
        val (url, token) = if (text.startsWith("creatorforge://")) {
            val u = Uri.parse(text)
            (u.getQueryParameter("url").orEmpty()) to u.getQueryParameter("token").orEmpty()
        } else text to ""
        val clean = url.trim().trimEnd('/')
        if (!clean.startsWith("http://") && !clean.startsWith("https://")) return "That code isn't a CreatorForge worker link"
        context.getSharedPreferences("creatorforge_provider", 0).edit().putString("base_url", clean).apply()
        if (token.isNotBlank()) { SecureTokenStore(context).save("worker", token); WorkerAuth.token = token }
        return "Connected to $clean" + if (token.isNotBlank()) " (token saved)" else ""
    }
}

/** "SCAN QR" card shown at the top of the worker settings. */
@Composable
fun WorkerQuickConnect(onConnected: (String) -> Unit) {
    val context = LocalContext.current
    var message by remember { mutableStateOf<String?>(null) }
    Card { Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("CONNECT YOUR POD", color = Gold)
        Text("Start the pod, run the start command, then scan the QR code it prints. With a permanent RunPod address you only do this once.",
            color = Color.LightGray, fontSize = 12.sp)
        Button({
            val options = GmsBarcodeScannerOptions.Builder().setBarcodeFormats(Barcode.FORMAT_QR_CODE).build()
            GmsBarcodeScanning.getClient(context, options).startScan()
                .addOnSuccessListener { code ->
                    val msg = WorkerConnect.apply(context, code.rawValue.orEmpty())
                    message = msg
                    if (msg.startsWith("Connected")) onConnected(msg)
                }
                .addOnFailureListener { message = "Scanner unavailable: ${it.message ?: "update Google Play services"} - type the URL below instead" }
        }) { Text("📷 SCAN QR") }
        message?.let { Text(it, color = if (it.startsWith("Connected")) Gold else Danger, fontSize = 12.sp) }
    } }
}
