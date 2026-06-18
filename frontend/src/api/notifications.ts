import type { Notification, NotificationPreference, NotificationPreferenceUpdate } from "../types/notification";
import { client } from "./client";

export const notificationsApi = {
  getAll: () =>
    client.get<Notification[]>("/notifications").then((r) => r.data),

  getUnreadCount: () =>
    client.get<{ count: number }>("/notifications/unread-count").then((r) => r.data),

  markRead: (id: string) =>
    client.patch<Notification>(`/notifications/${id}/read`).then((r) => r.data),

  markAllRead: () =>
    client.patch("/notifications/read-all").then((r) => r.data),

  getPreferences: () =>
    client.get<NotificationPreference>("/users/me/preferences").then((r) => r.data),

  updatePreferences: (data: NotificationPreferenceUpdate) =>
    client.put<NotificationPreference>("/users/me/preferences", data).then((r) => r.data),
};
