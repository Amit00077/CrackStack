import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { client } from "../api/client";
import { Button } from "../components/ui/Button";
import { Skeleton } from "../components/ui/Skeleton";
import type { Notification } from "../types/notification";

const typeConfig: Record<string, { icon: string; gradient: string; border: string; bg: string }> = {
  info: {
    icon: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
    gradient: "from-primary-500 to-primary-600",
    border: "border-primary-200",
    bg: "bg-primary-50",
  },
  success: {
    icon: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
    gradient: "from-emerald-500 to-emerald-600",
    border: "border-emerald-200",
    bg: "bg-emerald-50",
  },
  warning: {
    icon: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
    gradient: "from-amber-500 to-amber-600",
    border: "border-amber-200",
    bg: "bg-amber-50",
  },
  error: {
    icon: "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z",
    gradient: "from-rose-500 to-rose-600",
    border: "border-rose-200",
    bg: "bg-rose-50",
  },
};

function NotificationItem({
  notification,
  onMarkRead,
}: {
  notification: Notification;
  onMarkRead: (id: string) => void;
}) {
  const cfg = typeConfig[notification.type] || typeConfig.info;

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border p-5 transition-all duration-300 hover:shadow-elevated ${
        notification.is_read
          ? "border-surface-100 bg-white"
          : `${cfg.border} ${cfg.bg}`
      }`}
    >
      {!notification.is_read && (
        <div className={`absolute left-0 top-0 h-full w-1 bg-gradient-to-b ${cfg.gradient}`} />
      )}
      <div className="flex items-start gap-4">
        <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${cfg.gradient} text-white shadow-sm`}>
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={cfg.icon} />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p
                className={`text-sm font-bold ${
                  notification.is_read ? "text-surface-600" : "text-surface-900"
                }`}
              >
                {notification.title}
              </p>
              <p
                className={`mt-1 text-sm ${
                  notification.is_read ? "text-surface-400" : "text-surface-600"
                }`}
              >
                {notification.message}
              </p>
            </div>
            {!notification.is_read && (
              <button
                onClick={() => onMarkRead(notification.id)}
                className="flex-shrink-0 rounded-xl bg-white border border-primary-200 px-3 py-1.5 text-xs font-semibold text-primary-600 hover:bg-primary-50 hover:border-primary-300 transition-all duration-200 shadow-sm"
              >
                Mark read
              </button>
            )}
          </div>
          <p className="mt-2 flex items-center gap-1.5 text-xs text-surface-400">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {timeAgo(notification.created_at)}
          </p>
        </div>
      </div>
    </div>
  );
}

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diff = now - date;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export function Notifications() {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["notifications"],
    queryFn: () =>
      client.get<{ items: Notification[] }>("/notifications").then((r) => r.data),
    retry: false,
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) =>
      client.patch(`/notifications/${id}`, { is_read: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => client.post("/notifications/mark-all-read"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const notifications = data?.items || [];
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <div className="mx-auto max-w-2xl space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="section-title">Notifications</h2>
          {unreadCount > 0 && (
            <p className="section-subtitle">
              {unreadCount} unread notification{unreadCount !== 1 ? "s" : ""}
            </p>
          )}
        </div>
        {unreadCount > 0 && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => markAllReadMutation.mutate()}
            isLoading={markAllReadMutation.isPending}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Mark All as Read
          </Button>
        )}
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rect" height={88} />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2.5 rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
          <svg className="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Failed to load notifications.</span>
        </div>
      )}

      {!isLoading && !error && notifications.length === 0 && (
        <div className="empty-state animate-fade-in">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-primary shadow-lg shadow-primary-500/20 mb-5">
            <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
          <h3 className="mb-2 text-xl font-bold text-surface-900">
            No notifications
          </h3>
          <p className="text-sm text-surface-500">
            You're all caught up!
          </p>
        </div>
      )}

      {notifications.length > 0 && (
        <div className="space-y-3">
          {notifications.map((n) => (
            <NotificationItem
              key={n.id}
              notification={n}
              onMarkRead={(id) => markReadMutation.mutate(id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
