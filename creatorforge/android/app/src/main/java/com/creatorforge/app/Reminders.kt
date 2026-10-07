package com.creatorforge.app

import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneId

/** Posting reminders: a notification at the planned time that opens the Publish Calendar. */
object Reminders {
    private const val CHANNEL = "posting"

    private fun intent(context: Context, id: String, title: String) = PendingIntent.getBroadcast(context, id.hashCode(),
        Intent(context, ReminderReceiver::class.java).putExtra("id", id).putExtra("title", title),
        PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

    /** Returns false when the time is already in the past. */
    fun schedule(context: Context, id: String, title: String, day: String, time: String): Boolean {
        val at = runCatching {
            LocalDate.parse(day).atTime(LocalTime.parse(time.padStart(5, '0'))).atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
        }.getOrNull() ?: return false
        if (at < System.currentTimeMillis()) return false
        val am = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager
        am.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, at, intent(context, id, title))
        return true
    }

    fun cancel(context: Context, id: String) {
        (context.getSystemService(Context.ALARM_SERVICE) as AlarmManager).cancel(intent(context, id, ""))
    }

    fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
                .createNotificationChannel(NotificationChannel(CHANNEL, "Posting reminders", NotificationManager.IMPORTANCE_HIGH))
        }
    }

    fun show(context: Context, id: String, title: String) {
        ensureChannel(context)
        val open = PendingIntent.getActivity(context, id.hashCode(),
            Intent(context, MainActivity::class.java).putExtra("route", "calendar").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val n = NotificationCompat.Builder(context, CHANNEL).setSmallIcon(android.R.drawable.ic_menu_upload)
            .setContentTitle("Time to post").setContentText(title).setAutoCancel(true).setContentIntent(open)
            .setPriority(NotificationCompat.PRIORITY_HIGH).build()
        runCatching { (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).notify(id.hashCode(), n) }
    }
}

class ReminderReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        Reminders.show(context, intent.getStringExtra("id").orEmpty(), intent.getStringExtra("title").orEmpty())
    }
}
