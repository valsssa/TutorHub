"use client";

import { useState, useEffect, useCallback } from "react";
import { Mail, Bell, Clock, MessageSquare, Calendar, Gift, Star, Megaphone } from "lucide-react";
import { useToast } from "@/components/ToastContainer";
import { notifications, NotificationPreferences, NotificationPreferencesUpdate } from "@/lib/api";
import Toggle from "@/components/settings/Toggle";
import LoadingSpinner from "@/components/LoadingSpinner";
import { createLogger } from "@/lib/logger";

const logger = createLogger('NotificationSettings');

export default function NotificationsPage() {
  const { showSuccess, showError } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const fetchPreferences = useCallback(async () => {
    try {
      setLoading(true);
      const data = await notifications.getPreferences();
      setPreferences(data);
      setHasChanges(false);
    } catch (error) {
      logger.error("Failed to fetch notification preferences:", error);
      showError("Failed to load notification preferences");
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  const handleToggle = (key: keyof NotificationPreferences) => {
    if (!preferences) return;

    const newValue = !preferences[key];
    setPreferences(prev => prev ? { ...prev, [key]: newValue } : null);
    setHasChanges(true);
  };

  const handleTimeChange = (key: 'quiet_hours_start' | 'quiet_hours_end' | 'preferred_notification_time', value: string) => {
    if (!preferences) return;
    setPreferences(prev => prev ? { ...prev, [key]: value || null } : null);
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (!preferences) return;

    setSaving(true);
    try {
      const update: NotificationPreferencesUpdate = {
        email_enabled: preferences.email_enabled,
        push_enabled: preferences.push_enabled,
        sms_enabled: preferences.sms_enabled,
        session_reminders_enabled: preferences.session_reminders_enabled,
        booking_requests_enabled: preferences.booking_requests_enabled,
        learning_nudges_enabled: preferences.learning_nudges_enabled,
        review_prompts_enabled: preferences.review_prompts_enabled,
        achievements_enabled: preferences.achievements_enabled,
        marketing_enabled: preferences.marketing_enabled,
        max_daily_notifications: preferences.max_daily_notifications,
        max_weekly_nudges: preferences.max_weekly_nudges,
      };

      if (preferences.quiet_hours_start) {
        update.quiet_hours_start = preferences.quiet_hours_start;
      }
      if (preferences.quiet_hours_end) {
        update.quiet_hours_end = preferences.quiet_hours_end;
      }
      if (preferences.preferred_notification_time) {
        update.preferred_notification_time = preferences.preferred_notification_time;
      }

      const updated = await notifications.updatePreferences(update);
      setPreferences(updated);
      setHasChanges(false);
      showSuccess("Notification preferences saved");
    } catch (error) {
      logger.error("Failed to save notification preferences:", error);
      showError("Failed to save notification preferences");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-600 dark:text-slate-400">Failed to load preferences. Please try again.</p>
        <button
          onClick={fetchPreferences}
          className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
      <div>
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Notification Preferences</h3>
        <p className="text-slate-500 dark:text-slate-400 mb-8">Manage how and when you hear from us.</p>

        {/* Delivery Channels */}
        <section className="mb-10">
          <div className="flex items-center gap-2 mb-4 text-slate-900 dark:text-white font-bold text-lg">
            <Bell size={20} /> Delivery Channels
          </div>
          <div className="space-y-4">
            <Toggle
              enabled={preferences.email_enabled}
              onChange={() => handleToggle("email_enabled")}
              label="Email notifications"
              description="Receive notifications via email"
              icon={<Mail size={18} />}
            />
            <Toggle
              enabled={preferences.push_enabled}
              onChange={() => handleToggle("push_enabled")}
              label="Push notifications"
              description="Receive push notifications on your devices"
              icon={<Bell size={18} />}
            />
            <Toggle
              enabled={preferences.sms_enabled}
              onChange={() => handleToggle("sms_enabled")}
              label="SMS notifications"
              description="Receive text messages for urgent updates (carrier rates may apply)"
              icon={<MessageSquare size={18} />}
            />
          </div>
        </section>

        {/* Notification Types */}
        <section className="mb-10">
          <div className="flex items-center gap-2 mb-4 text-slate-900 dark:text-white font-bold text-lg">
            <MessageSquare size={20} /> Notification Types
          </div>
          <div className="space-y-4">
            <Toggle
              enabled={preferences.session_reminders_enabled}
              onChange={() => handleToggle("session_reminders_enabled")}
              label="Session reminders"
              description="Get reminders before your upcoming sessions"
              icon={<Calendar size={18} />}
            />
            <Toggle
              enabled={preferences.booking_requests_enabled}
              onChange={() => handleToggle("booking_requests_enabled")}
              label="Booking requests"
              description="Notifications about new and updated bookings"
              icon={<Calendar size={18} />}
            />
            <Toggle
              enabled={preferences.learning_nudges_enabled}
              onChange={() => handleToggle("learning_nudges_enabled")}
              label="Learning nudges"
              description="Tips and reminders to help you stay on track"
              icon={<Star size={18} />}
            />
            <Toggle
              enabled={preferences.review_prompts_enabled}
              onChange={() => handleToggle("review_prompts_enabled")}
              label="Review prompts"
              description="Reminders to review your completed sessions"
              icon={<Star size={18} />}
            />
            <Toggle
              enabled={preferences.achievements_enabled}
              onChange={() => handleToggle("achievements_enabled")}
              label="Achievements"
              description="Celebrate your learning milestones"
              icon={<Gift size={18} />}
            />
            <Toggle
              enabled={preferences.marketing_enabled}
              onChange={() => handleToggle("marketing_enabled")}
              label="Marketing & promotions"
              description="Special offers and platform updates"
              icon={<Megaphone size={18} />}
            />
          </div>
        </section>

        {/* Quiet Hours */}
        <section className="mb-10">
          <div className="flex items-center gap-2 mb-4 text-slate-900 dark:text-white font-bold text-lg">
            <Clock size={20} /> Quiet Hours
          </div>
          <p className="text-slate-500 dark:text-slate-400 mb-4 text-sm">
            We won&apos;t send you notifications during these hours.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Start time
              </label>
              <input
                type="time"
                value={preferences.quiet_hours_start || ""}
                onChange={(e) => handleTimeChange("quiet_hours_start", e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                End time
              </label>
              <input
                type="time"
                value={preferences.quiet_hours_end || ""}
                onChange={(e) => handleTimeChange("quiet_hours_end", e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>
          </div>
        </section>

        {/* Transactional Notice */}
        <section className="mb-8 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
              <Mail className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white mb-1">Transactional emails</h4>
              <p className="text-slate-500 dark:text-slate-400 text-sm">
                Important notifications about your account, payments, and security will always be sent regardless of your preferences.
              </p>
            </div>
          </div>
        </section>

        {/* Save Button */}
        <div className="pt-4">
          <button
            onClick={handleSave}
            disabled={saving || !hasChanges}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
          >
            {saving ? 'Saving...' : hasChanges ? 'Save changes' : 'No changes to save'}
          </button>
        </div>
      </div>
    </div>
  );
}
