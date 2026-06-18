import { create } from "zustand";

import { notificationsApi } from "../api/notifications";
import type { Notification } from "../types/notification";

interface NotificationState {
  notifications: Notification[];
  unreadCount: number;
  isLoading: boolean;

  fetchNotifications: () => Promise<void>;
  fetchUnreadCount: () => Promise<void>;
  markAsRead: (id: string) => Promise<void>;
  markAllAsRead: () => Promise<void>;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  unreadCount: 0,
  isLoading: false,

  fetchNotifications: async () => {
    set({ isLoading: true });
    try {
      const notifications = await notificationsApi.getAll();
      set({ notifications, isLoading: false });
    } catch {
      set({ isLoading: false });
    }
  },

  fetchUnreadCount: async () => {
    try {
      const { count } = await notificationsApi.getUnreadCount();
      set({ unreadCount: count });
    } catch {
      // ignore
    }
  },

  markAsRead: async (id) => {
    await notificationsApi.markRead(id);
    const notifications = get().notifications.map((n) =>
      n.id === id ? { ...n, is_read: true } : n,
    );
    const unreadCount = Math.max(0, get().unreadCount - 1);
    set({ notifications, unreadCount });
  },

  markAllAsRead: async () => {
    await notificationsApi.markAllRead();
    const notifications = get().notifications.map((n) => ({
      ...n,
      is_read: true,
    }));
    set({ notifications, unreadCount: 0 });
  },
}));
