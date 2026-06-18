import type { User, UserUpdate } from "../types/auth";
import type { NotificationPreference, NotificationPreferenceUpdate } from "../types/notification";
import { client } from "./client";

export const usersApi = {
  getMe: () =>
    client.get<User>("/users/me").then((r) => r.data),

  updateMe: (data: UserUpdate) =>
    client.patch<User>("/users/me", data).then((r) => r.data),

  getPreferences: () =>
    client.get<NotificationPreference>("/users/me/preferences").then((r) => r.data),

  updatePreferences: (data: NotificationPreferenceUpdate) =>
    client.put<NotificationPreference>("/users/me/preferences", data).then((r) => r.data),

  deleteAccount: () =>
    client.delete("/users/me").then((r) => r.data),

  exportData: () =>
    client.get<{ data: any }>("/users/me/export").then((r) => r.data),
};
