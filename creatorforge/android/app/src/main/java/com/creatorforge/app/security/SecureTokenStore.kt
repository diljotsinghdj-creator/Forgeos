package com.creatorforge.app.security

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureTokenStore(private val context: Context) {
    private val prefs = context.getSharedPreferences("creatorforge_secure", Context.MODE_PRIVATE)
    private fun alias(name:String)="creatorforge_${name}_key"
    private fun key(name:String): SecretKey {
        val a=alias(name); val ks=KeyStore.getInstance("AndroidKeyStore").apply{load(null)}
        (ks.getKey(a,null) as? SecretKey)?.let{return it}
        val g=KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore")
        g.init(KeyGenParameterSpec.Builder(a,KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        return g.generateKey()
    }
    fun save(name:String, value:String){ val c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.ENCRYPT_MODE,key(name));val enc=c.doFinal(value.toByteArray());prefs.edit().putString("${name}_token",Base64.encodeToString(enc,Base64.NO_WRAP)).putString("${name}_iv",Base64.encodeToString(c.iv,Base64.NO_WRAP)).apply() }
    fun load(name:String):String?=runCatching{val enc=prefs.getString("${name}_token",null)?:return null;val iv=prefs.getString("${name}_iv",null)?:return null;val c=Cipher.getInstance("AES/GCM/NoPadding");c.init(Cipher.DECRYPT_MODE,key(name),GCMParameterSpec(128,Base64.decode(iv,Base64.NO_WRAP)));String(c.doFinal(Base64.decode(enc,Base64.NO_WRAP)))}.getOrNull()
    fun clear(name:String)=prefs.edit().remove("${name}_token").remove("${name}_iv").apply()
    fun has(name:String)=!load(name).isNullOrBlank()
    // compatibility with v0.5 image token
    fun save(token:String)=save("image",token); fun load()=load("image"); fun clear()=clear("image"); fun hasToken()=has("image")
}
