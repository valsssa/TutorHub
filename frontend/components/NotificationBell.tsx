"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { FiBell, FiCheck, FiX, FiMail, FiCalendar, FiAlertCircle } from "react-icons/fi";
import { notifications as notificationAPI } from "@/lib/api";
import { useToast } from "./ToastContainer";
import { useWebSocket } from "@/hooks/useWebSocket";

interface Notification {
  id: number;
  type: string;
  title: string;
  message: string;
  link?: string | null;
  is_read: boolean;
  created_at: string;
  category?: string;
  priority?: number;
}

export default function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const { showError } = useToast();
  const { lastMessage } = useWebSocket();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const loadNotifications = useCallback(async () => {
    try {
      setLoading(true);
      const data = await notificationAPI.list();
      const notifications = Array.isArray(data) ? data : [];
      setNotifications(notifications);
      setUnreadCount(notifications.filter((n: Notification) => !n.is_read).length);
    } catch (error) {
      showError("Failed to load notifications");
      setNotifications([]);
      setUnreadCount(0);
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  // Handle WebSocket notification updates
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "notification") {
      // Add new notification to list
      const newNotification: Notification = {
        id: lastMessage.notification_id,
        type: lastMessage.notification_type,
        title: lastMessage.title,
        message: lastMessage.message,
        link: lastMessage.link,
        is_read: false,
        created_at: lastMessage.created_at,
        category: lastMessage.category,
        priority: lastMessage.priority,
      };
      setNotifications((prev) => [newNotification, ...prev]);
      setUnreadCount((prev) => prev + 1);
    }
  }, [lastMessage]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const markAsRead = async (notificationId: number) => {
    try {
      await notificationAPI.markRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notificationId ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      showError("Failed to mark notification as read");
    }
  };

  const markAllAsRead = async () => {
    try {
      await notificationAPI.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (error) {
      showError("Failed to mark all notifications as read");
    }
  };

  const deleteNotification = async (notificationId: number) => {
    try {
      await notificationAPI.delete(notificationId);
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      setUnreadCount((prev) => {
        const notification = notifications.find((n) => n.id === notificationId);
        return notification && !notification.is_read ? prev - 1 : prev;
      });
    } catch (error) {
      showError("Failed to delete notification");
    }
  };

  const getNotificationIcon = (type: string, category?: string) => {
    switch (type) {
      case "new_message":
        return <FiMail className="w-4 h-4 text-blue-600" />;
      case "booking_confirmed":
      case "booking_reminder":
        return <FiCalendar className="w-4 h-4 text-green-600" />;
      case "booking_cancelled":
      case "booking_rescheduled":
        return <FiAlertCircle className="w-4 h-4 text-orange-600" />;
      default:
        return <FiBell className="w-4 h-4 text-gray-600" />;
    }
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative z-[10000]" ref={dropdownRef}>
      {/* Bell Icon with Badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative tap-target p-2 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
        aria-label="Notifications"
        aria-expanded={isOpen}
      >
        <FiBell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full min-w-[20px]">
            {unreadCount > 99 ? "99+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 max-w-[calc(100vw-2rem)] bg-white dark:bg-slate-900 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 z-[10001] max-h-[600px] flex flex-col">
          {/* Header */}
          <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 font-medium"
                >
                  Mark all read
                </button>
              )}
            </div>
          </div>

          {/* Notification List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto" role="status"><span className="sr-only">Loading...</span></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <FiBell className="w-12 h-12 text-slate-400 dark:text-slate-600 mx-auto mb-3" />
                <p className="text-slate-600 dark:text-slate-400 text-sm">No notifications yet</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-200 dark:divide-slate-700">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors ${
                      !notification.is_read ? "bg-blue-50 dark:bg-blue-900/20" : ""
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        {getNotificationIcon(notification.type, notification.category)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {notification.title}
                        </p>
                        <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {formatTime(notification.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {!notification.is_read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="p-1 text-slate-400 dark:text-slate-500 hover:text-green-600 dark:hover:text-green-400 transition-colors"
                            title="Mark as read"
                            aria-label="Mark notification as read"
                          >
                            <FiCheck className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteNotification(notification.id)}
                          className="p-1 text-slate-400 dark:text-slate-500 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                          title="Delete notification"
                          aria-label="Delete notification"
                        >
                          <FiX className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {notification.link && (
                      <a
                        href={notification.link}
                        className="text-xs text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 mt-2 inline-block"
                        onClick={() => setIsOpen(false)}
                      >
                        View →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
