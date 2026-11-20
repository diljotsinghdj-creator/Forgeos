package com.creatorforge.app.production

import okhttp3.Request

/** Removes what a copy-paste can smuggle into a token or address: spaces, line breaks and invisible characters
 *  (zero-width space U+200B, joiners, word joiner, byte-order mark and other "format" characters). One of them in
 *  a token made every request fail with "Unexpected char 0x200b ... in Authorization value". */
fun cleanSecret(s: String): String = s.filterNot {
    it.isWhitespace() || Character.getType(it) == Character.FORMAT.toInt() || it == '​' || it == '﻿'
}

/** Holds the worker bearer token for this process (persisted encrypted in SecureTokenStore("worker")).
 *  Always cleaned, so a token saved before this fix (with a hidden character in it) works without re-entering it. */
object WorkerAuth {
    @Volatile private var value: String = ""
    var token: String
        get() = value
        set(v) { value = cleanSecret(v) }
}

fun Request.Builder.workerAuth(): Request.Builder =
    WorkerAuth.token.takeIf { it.isNotBlank() }?.let { header("Authorization", "Bearer $it") } ?: this
