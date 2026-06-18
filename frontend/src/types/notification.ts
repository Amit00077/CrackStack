export interface Notification {
  id: string;
  user_id: string;
  type: "reminder" | "streak_warning" | "report_ready" | "system";
  title: string;
  message: string;
  is_read: boolean;
  channel: "in_app" | "email" | "push";
  sent_at: string | null;
  created_at: string;
}

export interface NotificationPreference {
  id?: string;
  user_id?: string;
  timezone: string;
  email_notifications: boolean;
  push_notifications: boolean;
  daily_reminder: boolean;
  reminder_time: string;
  weekly_report_enabled: boolean;
}

export interface NotificationPreferenceUpdate {
  timezone?: string;
  email_notifications?: boolean;
  push_notifications?: boolean;
  daily_reminder?: boolean;
  reminder_time?: string;
  weekly_report_enabled?: boolean;
}
