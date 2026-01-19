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
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon with Badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors"
        aria-label="Notifications"
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
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-[600px] flex flex-col">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium"
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
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center">
                <FiBell className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                <p className="text-gray-600 text-sm">No notifications yet</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`px-4 py-3 hover:bg-gray-50 transition-colors ${
                      !notification.is_read ? "bg-blue-50" : ""
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        {getNotificationIcon(notification.type, notification.category)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {notification.title}
                        </p>
                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTime(notification.created_at)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {!notification.is_read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                            title="Mark as read"
                          >
                            <FiCheck className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteNotification(notification.id)}
                          className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                          title="Delete"
                        >
                          <FiX className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {notification.link && (
                      <a
                        href={notification.link}
                        className="text-xs text-primary-600 hover:text-primary-700 mt-2 inline-block"
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
