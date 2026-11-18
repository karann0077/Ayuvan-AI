package com.ayuvan.mobile.data

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.Worker
import androidx.work.WorkerParameters
import androidx.work.WorkManager
import com.ayuvan.mobile.MainActivity
import com.ayuvan.mobile.R
import org.json.JSONObject
import java.time.Instant
import java.util.concurrent.TimeUnit

object ReminderScheduler {
    fun cancel(context: Context, taskId: String) {
        WorkManager.getInstance(context).cancelUniqueWork("ayuvan-reminder-$taskId")
    }

    fun cancelAll(context: Context) {
        WorkManager.getInstance(context).cancelAllWorkByTag("ayuvan-reminder")
    }

    fun reconcile(context: Context, tasks: List<JSONObject>, enabled: Boolean) {
        val manager = WorkManager.getInstance(context)
        tasks.forEach { task ->
            val id = task.optString("id")
            if (id.isBlank()) return@forEach
            val workName = "ayuvan-reminder-$id"
            val due = try { Instant.parse(task.optString("due_at")) } catch (_: Exception) { null }
            if (!enabled || task.optString("status") != "pending" || due == null || !due.isAfter(Instant.now())) {
                manager.cancelUniqueWork(workName)
                return@forEach
            }
            val delay = due.toEpochMilli() - System.currentTimeMillis()
            val work = OneTimeWorkRequestBuilder<ReminderWorker>()
                .addTag("ayuvan-reminder")
                .setInitialDelay(delay, TimeUnit.MILLISECONDS)
                .setInputData(Data.Builder().putString("task_id", id).build())
                .build()
            manager.enqueueUniqueWork(workName, ExistingWorkPolicy.REPLACE, work)
        }
    }
}

class ReminderWorker(context: Context, params: WorkerParameters) : Worker(context, params) {
    override fun doWork(): Result {
        if (Build.VERSION.SDK_INT >= 33 && ContextCompat.checkSelfPermission(
                applicationContext, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            return Result.success()
        }
        val manager = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channelId = "ayuvan_care_reminders"
        if (Build.VERSION.SDK_INT >= 26) {
            manager.createNotificationChannel(NotificationChannel(channelId, "Care reminders",
                NotificationManager.IMPORTANCE_DEFAULT))
        }
        val intent = Intent(applicationContext, MainActivity::class.java)
        val pending = PendingIntent.getActivity(applicationContext, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification = NotificationCompat.Builder(applicationContext, channelId)
            .setSmallIcon(R.drawable.ayuvan_app_icon)
            .setContentTitle("AYUVAN reminder")
            .setContentText("You have a care task due. Open AYUVAN to review it.")
            .setContentIntent(pending)
            .setAutoCancel(true)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .build()
        NotificationManagerCompat.from(applicationContext).notify(inputData.getString("task_id").hashCode(), notification)
        return Result.success()
    }
}
