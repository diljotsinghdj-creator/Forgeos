package com.creatorforge.app.production

import okhttp3.Request

/** Holds the worker bearer token for this process (persisted encrypted in SecureTokenStore("worker")). */
object WorkerAuth {
    @Volatile var token: String = ""
}

fun Request.Builder.workerAuth(): Request.Builder =
    WorkerAuth.token.takeIf { it.isNotBlank() }?.let { header("Authorization", "Bearer $it") } ?: this
