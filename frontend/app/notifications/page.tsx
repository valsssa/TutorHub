"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  Filter,
  Calendar,
  MessageSquare,
  CreditCard,
  User,
  Star,
  AlertCircle,
  Settings,
  ChevronRight,
  RefreshCw,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import EmptyState from "@/components/EmptyState";
import LoadingSpinner from "@/components/LoadingSpinner";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { notifications } from "@/lib/api";
import { useToast } from "@/components/ToastContainer";
import clsx from "clsx";

interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  data?: Record<string, any>;
}

type NotificationFilter = "all" | "unread" | "booking" | "message" | "payment";

const filterOptions: { value: NotificationFilter; label: string; icon: any }[] = [
  { value: "all", label: "All", icon: Bell },
  { value: "unread", label: "Unread", icon: AlertCircle },
  { value: "booking", label: "Bookings", icon: Calendar },
  { value: "message", label: "Messages", icon: MessageSquare },
  { value: "payment", label: "Payments", icon: CreditCard },
];

function getNotificationIcon(type: string) {
  const lowerType = type.toLowerCase();
  if (lowerType.includes("booking") || lowerType.includes("session")) {
    return { icon: Calendar, color: "text-blue-500", bg: "bg-blue-100 dark:bg-blue-900/30" };
  }
  if (lowerType.includes("message")) {
    return { icon: MessageSquare, color: "text-emerald-500", bg: "bg-emerald-100 dark:bg-emerald-900/30" };
  }
  if (lowerType.includes("payment") || lowerType.includes("refund")) {
    return { icon: CreditCard, color: "text-purple-500", bg: "bg-purple-100 dark:bg-purple-900/30" };
  }
  if (lowerType.includes("review") || lowerType.includes("rating")) {
    return { icon: Star, color: "text-amber-500", bg: "bg-amber-100 dark:bg-amber-900/30" };
  }
  if (lowerType.includes("profile") || lowerType.includes("user")) {
    return { icon: User, color: "text-cyan-500", bg: "bg-cyan-100 dark:bg-cyan-900/30" };
  }
  return { icon: Bell, color: "text-slate-500", bg: "bg-slate-100 dark:bg-slate-800" };
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

export default function NotificationsPage() {
  return (
    <ProtectedRoute>
      <NotificationsContent />
    </ProtectedRoute>
  );
}

function NotificationsContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();

  const [notificationsList, setNotificationsList] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<NotificationFilter>("all");
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const loadNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const data = await notifications.list();
      setNotificationsList(data);
    } catch (err: any) {
      showError("Failed to load notifications");
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notifications.markAsRead(id);
      setNotificationsList((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {
      showError("Failed to mark as read");
    }
  };

  const handleMarkAllAsRead = async () => {
    setActionLoading(true);
    try {
      await notifications.markAllAsRead();
      setNotificationsList((prev) =>
        prev.map((n) => ({ ...n, is_read: true }))
      );
      showSuccess("All notifications marked as read");
    } catch {
      showError("Failed to mark all as read");
    } finally {
      setActionLoading(false);
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    // Mark as read
    if (!notification.is_read) {
      handleMarkAsRead(notification.id);
    }

    // Navigate based on notification type/data
    const type = notification.type.toLowerCase();
    const data = notification.data;

    if (type.includes("booking") && data?.booking_id) {
      router.push(`/bookings/${data.booking_id}`);
    } else if (type.includes("message") && data?.thread_id) {
      router.push(`/messages?thread=${data.thread_id}`);
    } else if (type.includes("review") && data?.tutor_id) {
      router.push(`/tutors/${data.tutor_id}`);
    }
  };

  // Filter notifications
  const filteredNotifications = notificationsList.filter((n) => {
    if (filter === "all") return true;
    if (filter === "unread") return !n.is_read;
    const type = n.type.toLowerCase();
    if (filter === "booking") return type.includes("booking") || type.includes("session");
    if (filter === "message") return type.includes("message");
    if (filter === "payment") return type.includes("payment") || type.includes("refund");
    return true;
  });

  const unreadCount = notificationsList.filter((n) => !n.is_read).length;

  // Group by date
  const groupedNotifications = filteredNotifications.reduce((groups, notification) => {
    const date = new Date(notification.created_at);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    let groupKey: string;
    if (date.toDateString() === today.toDateString()) {
      groupKey = "Today";
    } else if (date.toDateString() === yesterday.toDateString()) {
      groupKey = "Yesterday";
    } else {
      groupKey = date.toLocaleDateString("en-US", { month: "long", day: "numeric" });
    }

    if (!groups[groupKey]) {
      groups[groupKey] = [];
    }
    groups[groupKey].push(notification);
    return groups;
  }, {} as Record<string, Notification[]>);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb items={[{ label: "Notifications" }]} />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-3xl">
        {/* Title & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
              <Bell className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Notifications
              </h1>
              {unreadCount > 0 && (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {unreadCount} unread
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={loadNotifications}
              disabled={loading}
            >
              <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
            </Button>
            {unreadCount > 0 && (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleMarkAllAsRead}
                isLoading={actionLoading}
              >
                <CheckCheck className="w-4 h-4 mr-2" />
                Mark all read
              </Button>
            )}
            <Link href="/settings/notifications">
              <Button variant="ghost" size="sm">
                <Settings className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
          {filterOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setFilter(option.value)}
              className={clsx(
                "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap",
                filter === option.value
                  ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                  : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700"
              )}
            >
              <option.icon className="w-4 h-4" />
              {option.label}
              {option.value === "unread" && unreadCount > 0 && (
                <span className="ml-1 px-1.5 py-0.5 rounded-full bg-emerald-600 text-white text-xs">
                  {unreadCount}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <LoadingSpinner size="lg" />
          </div>
        ) : filteredNotifications.length === 0 ? (
          <EmptyState
            variant="no-notifications"
            title={filter === "unread" ? "All caught up!" : "No notifications"}
            description={
              filter === "unread"
                ? "You've read all your notifications."
                : "You don't have any notifications yet."
            }
            action={
              filter !== "all"
                ? {
                    label: "View All",
                    onClick: () => setFilter("all"),
                    variant: "secondary",
                  }
                : undefined
            }
          />
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedNotifications).map(([date, items]) => (
              <div key={date}>
                <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-3">
                  {date}
                </h3>
                <div className="space-y-2">
                  {items.map((notification) => {
                    const iconConfig = getNotificationIcon(notification.type);
                    const Icon = iconConfig.icon;

                    return (
                      <button
                        key={notification.id}
                        onClick={() => handleNotificationClick(notification)}
                        className={clsx(
                          "w-full flex items-start gap-4 p-4 rounded-xl text-left transition-colors",
                          "border border-slate-200 dark:border-slate-800",
                          notification.is_read
                            ? "bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800"
                            : "bg-emerald-50/50 dark:bg-emerald-900/10 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                        )}
                      >
                        {/* Icon */}
                        <div
                          className={clsx(
                            "w-10 h-10 rounded-full flex items-center justify-center shrink-0",
                            iconConfig.bg
                          )}
                        >
                          <Icon className={clsx("w-5 h-5", iconConfig.color)} />
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <p
                              className={clsx(
                                "font-medium",
                                notification.is_read
                                  ? "text-slate-700 dark:text-slate-300"
                                  : "text-slate-900 dark:text-white"
                              )}
                            >
                              {notification.title}
                            </p>
                            <span className="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                              {formatTimeAgo(notification.created_at)}
                            </span>
                          </div>
                          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                            {notification.message}
                          </p>
                        </div>

                        {/* Unread indicator */}
                        {!notification.is_read && (
                          <div className="w-2 h-2 rounded-full bg-emerald-500 shrink-0 mt-2" />
                        )}

                        {/* Arrow */}
                        <ChevronRight className="w-5 h-5 text-slate-400 shrink-0" />
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
