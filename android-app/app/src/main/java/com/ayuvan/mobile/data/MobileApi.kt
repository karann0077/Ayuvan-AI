package com.ayuvan.mobile.data

import android.content.Context
import android.net.Uri
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.ayuvan.mobile.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class ApiFailure(val statusCode: Int, message: String) : Exception(message)

class SessionVault(context: Context) {
    private val prefs = context.getSharedPreferences("ayuvan_session", Context.MODE_PRIVATE)
    private val alias = "ayuvan_mobile_token_v1"

    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(alias, null) as? SecretKey)?.let { return it }
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(KeyGenParameterSpec.Builder(alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256).build())
        return generator.generateKey()
    }

    fun save(token: String) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val packed = cipher.iv + cipher.doFinal(token.toByteArray(Charsets.UTF_8))
        prefs.edit().putString("access", Base64.encodeToString(packed, Base64.NO_WRAP)).apply()
    }

    fun load(): String? {
        val stored = prefs.getString("access", null) ?: return null
        return try {
            val packed = Base64.decode(stored, Base64.NO_WRAP)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, packed.copyOfRange(0, 12)))
            String(cipher.doFinal(packed.copyOfRange(12, packed.size)), Charsets.UTF_8)
        } catch (_: Exception) {
            clear()
            null
        }
    }

    fun clear() { prefs.edit().remove("access").apply() }
}

class MobileApi(private val context: Context) {
    private val vault = SessionVault(context)
    private var token: String? = vault.load()
    fun hasSession() = token != null
    fun clearSession() { token = null; vault.clear() }

    private suspend fun request(
        method: String, path: String, body: JSONObject? = null,
        upload: Pair<String, ByteArray>? = null, mime: String? = null,
        download: Boolean = false,
    ): ByteArray = withContext(Dispatchers.IO) {
        val connection = (URL(BuildConfig.API_BASE_URL.trimEnd('/') + "/api/v1/mobile" + path)
            .openConnection() as HttpURLConnection).apply {
            requestMethod = method
            connectTimeout = 12_000
            readTimeout = 65_000
            setRequestProperty("Accept", "application/json")
            token?.let { setRequestProperty("Authorization", "Bearer $it") }
            if (body != null || upload != null) doOutput = true
        }
        try {
            if (body != null) {
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
            if (upload != null) {
                val boundary = "Ayuvan${System.currentTimeMillis()}"
                connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=$boundary")
                connection.outputStream.use { out ->
                    val safeName = upload.first.replace(Regex("[^A-Za-z0-9._-]"), "_").take(100)
                    out.write("--$boundary\r\nContent-Disposition: form-data; name=\"file\"; filename=\"$safeName\"\r\nContent-Type: ${mime ?: "application/octet-stream"}\r\n\r\n".toByteArray())
                    out.write(upload.second)
                    out.write("\r\n--$boundary--\r\n".toByteArray())
                }
            }
            val status = connection.responseCode
            val bytes = (if (status in 200..299) connection.inputStream else connection.errorStream)
                ?.use { it.readBytes() } ?: ByteArray(0)
            if (status !in 200..299) {
                val detail = try { JSONObject(String(bytes)).optString("detail") } catch (_: Exception) { "Request failed" }
                if (status == 401 && (detail.startsWith("Session expired") || detail == "Sign in required" || detail == "Account unavailable")) clearSession()
                throw ApiFailure(status, detail.ifBlank { "Request failed ($status)" })
            }
            bytes
        } finally { connection.disconnect() }
    }

    private suspend fun json(method: String, path: String, body: JSONObject? = null) =
        JSONObject(String(request(method, path, body), Charsets.UTF_8))

    private fun segment(value: String) = URLEncoder.encode(value, "UTF-8")
    suspend fun register(phone: String, password: String, name: String, language: String,
                         consent: Boolean, aiConsent: Boolean, dateOfBirth: String? = null,
                         sex: String? = null): JSONObject {
        val payload = JSONObject().put("phone", phone)
            .put("password", password).put("name", name).put("preferred_language", language)
            .put("terms_accepted", consent).put("health_processing_consent", consent)
            .put("ai_assistance_consent", aiConsent)
        if (!dateOfBirth.isNullOrBlank()) payload.put("date_of_birth", dateOfBirth)
        if (!sex.isNullOrBlank()) payload.put("sex", sex)
        val response = json("POST", "/auth/register", payload)
        token = response.getString("access_token")
        vault.save(token!!)
        return response
    }
    suspend fun login(phone: String, password: String): JSONObject {
        val response = json("POST", "/auth/login", JSONObject().put("phone", phone).put("password", password))
        token = response.getString("access_token")
        vault.save(token!!)
        return response
    }
    suspend fun logout() { try { json("POST", "/auth/logout") } finally { clearSession() } }
    suspend fun changePassword(current: String, next: String) = json("POST", "/auth/change-password",
        JSONObject().put("current_password", current).put("new_password", next))
    suspend fun me() = json("GET", "/me")
    suspend fun health(patientId: String) = json("GET", "/patients/$patientId/health")
    suspend fun summary(patientId: String) = json("GET", "/patients/$patientId/summary")
    suspend fun chat(patientId: String) = json("GET", "/patients/$patientId/chat")
    suspend fun send(patientId: String, text: String, replyId: String? = null,
                     clientMessageId: String = java.util.UUID.randomUUID().toString()): JSONObject {
        val payload = JSONObject().put("text", text).put("client_message_id", clientMessageId)
        if (replyId != null) payload.put("reply_id", replyId)
        return json("POST", "/patients/$patientId/chat/messages", payload)
    }
    suspend fun correct(patientId: String, episodeId: String, correction: String) =
        json("POST", "/patients/$patientId/episodes/$episodeId/corrections", JSONObject().put("correction", correction))
    suspend fun addHealthItem(patientId: String, kind: String, name: String, details: String? = null) =
        json("POST", "/patients/$patientId/health-items/$kind", JSONObject().put("name", name).put("details", details))
    suspend fun updateHealthItem(patientId: String, kind: String, itemId: String, name: String, details: String? = null) =
        json("PATCH", "/patients/$patientId/health-items/$kind/$itemId", JSONObject().put("name", name).put("details", details))
    suspend fun deleteHealthItem(patientId: String, kind: String, itemId: String) =
        json("DELETE", "/patients/$patientId/health-items/$kind/$itemId")
    suspend fun care(patientId: String) = json("GET", "/patients/$patientId/care-tasks")
    suspend fun addTask(patientId: String, description: String, dueAt: String? = null) =
        json("POST", "/patients/$patientId/care-tasks", JSONObject().put("description", description).put("due_at", dueAt))
    suspend fun updateTask(patientId: String, taskId: String, status: String) =
        json("PATCH", "/patients/$patientId/care-tasks/$taskId", JSONObject().put("status", status))
    suspend fun editTask(patientId: String, taskId: String, description: String, dueAt: String?) =
        json("PATCH", "/patients/$patientId/care-tasks/$taskId",
            JSONObject().put("description", description).put("due_at", dueAt))
    suspend fun deleteTask(patientId: String, taskId: String) =
        json("DELETE", "/patients/$patientId/care-tasks/$taskId")
    suspend fun documents(patientId: String) = json("GET", "/patients/$patientId/documents")
    suspend fun upload(patientId: String, uri: Uri): JSONObject {
        val resolver = context.contentResolver
        val type = resolver.getType(uri) ?: "application/octet-stream"
        val bytes = withContext(Dispatchers.IO) { resolver.openInputStream(uri)?.use { it.readBytes() } }
            ?: throw ApiFailure(0, "Could not read selected file")
        if (bytes.size > 10 * 1024 * 1024) throw ApiFailure(413, "Choose a file under 10 MB")
        val filename = "medical-document.${when (type) { "application/pdf" -> "pdf"; "image/png" -> "png"; "image/webp" -> "webp"; else -> "jpg" }}"
        return JSONObject(String(request("POST", "/patients/$patientId/documents", upload = filename to bytes, mime = type)))
    }
    suspend fun extract(patientId: String, documentId: String) =
        json("POST", "/patients/$patientId/documents/$documentId/extract")
    suspend fun review(patientId: String, documentId: String, accepted: Boolean,
                       conditions: List<String>, medications: List<String>, allergies: List<String>) =
        json("POST", "/patients/$patientId/documents/$documentId/review", JSONObject()
            .put("accepted", accepted).put("conditions", org.json.JSONArray(conditions))
            .put("medications", org.json.JSONArray(medications)).put("allergies", org.json.JSONArray(allergies)))
    suspend fun download(patientId: String, documentId: String) =
        request("GET", "/patients/$patientId/documents/$documentId/download", download = true)
    suspend fun deleteDocument(patientId: String, documentId: String) =
        json("DELETE", "/patients/$patientId/documents/$documentId")
    suspend fun discover(query: String, category: String, area: String) = json("GET",
        "/discover?query=${segment(query)}&category=${segment(category)}&area=${segment(area)}")
    suspend fun createFamily(name: String, relationship: String, birthDate: String?, sex: String?) =
        json("POST", "/patients", JSONObject().put("name", name).put("relationship", relationship)
            .put("authorized_caregiver", true).also {
                if (!birthDate.isNullOrBlank()) it.put("date_of_birth", birthDate)
                if (!sex.isNullOrBlank()) it.put("sex", sex)
            })
    suspend fun updateProfile(patientId: String, name: String? = null, language: String? = null,
                              dateOfBirth: String? = null, sex: String? = null) =
        json("PATCH", "/patients/$patientId", JSONObject().also {
            if (name != null) it.put("display_name", name)
            if (language != null) it.put("preferred_language", language)
            if (dateOfBirth != null) it.put("date_of_birth", if (dateOfBirth.isBlank()) JSONObject.NULL else dateOfBirth)
            if (sex != null) it.put("sex", if (sex.isBlank()) JSONObject.NULL else sex)
        })
    suspend fun consents(patientId: String) = json("GET", "/patients/$patientId/consents")
    suspend fun setConsent(patientId: String, purpose: String, granted: Boolean) =
        json("POST", "/patients/$patientId/consents", JSONObject().put("purpose", purpose).put("granted", granted))
    suspend fun requestWhatsAppLink() = json("POST", "/whatsapp-link/request")
    suspend fun verifyWhatsAppLink(code: String) = json("POST", "/whatsapp-link/verify", JSONObject().put("code", code))
    suspend fun export() = json("GET", "/export")
    suspend fun deleteAccount(password: String) = json("POST", "/auth/delete", JSONObject().put("password", password))
    suspend fun deleteLinkedWhatsAppData(password: String) =
        json("POST", "/whatsapp-link/delete-data", JSONObject().put("password", password))
}
