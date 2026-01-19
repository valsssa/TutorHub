"use client";

import { useState, useEffect } from "react";
import { FiMail, FiSmartphone, FiBell, FiSave } from "react-icons/fi";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import SettingsCard from "@/components/settings/SettingsCard";
import Toggle from "@/components/settings/Toggle";

export default function NotificationsPage() {
  const { showSuccess } = useToast();
  const [saving, setSaving] = useState(false);
  const [notifications, setNotifications] = useState({
    lesson_reminders: true,
    new_messages: true,
    booking_updates: true,
    payment_confirmations: true,
    promotions: false,
    weekly_summary: true,
    push_enabled: true,
    email_enabled: true,
    sms_enabled: false,
  });

  const handleToggle = (key: keyof typeof notifications) => {
    setNotifications((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      showSuccess("Notification preferences updated ✅");
    } catch (error) {
      // Handle error
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          🔔 Notifications
        </h2>
        <p className="text-slate-600">
          Choose how and when you want to be notified
        </p>
      </div>

      {/* Notification Channels */}
      <SettingsCard
        title="Notification Channels"
        description="Select which channels we can use to reach you"
      >
        <div className="divide-y divide-slate-100">
          <Toggle
            enabled={notifications.email_enabled}
            onChange={() => handleToggle("email_enabled")}
            label="📧 Email Notifications"
            description="Receive updates via email"
          />
          <Toggle
            enabled={notifications.push_enabled}
            onChange={() => handleToggle("push_enabled")}
            label="📱 Push Notifications"
            description="Get alerts in your browser or app"
          />
          <Toggle
            enabled={notifications.sms_enabled}
            onChange={() => handleToggle("sms_enabled")}
            label="💬 SMS Messages"
            description="Text message alerts for urgent updates"
          />
        </div>
      </SettingsCard>

      {/* Lesson & Booking Updates */}
      <SettingsCard
        title="Lessons & Bookings"
        description="Stay updated about your tutoring sessions"
      >
        <div className="divide-y divide-slate-100">
          <Toggle
            enabled={notifications.lesson_reminders}
            onChange={() => handleToggle("lesson_reminders")}
            label="Lesson Reminders"
            description="Get reminded 1 hour before your lesson starts"
          />
          <Toggle
            enabled={notifications.booking_updates}
            onChange={() => handleToggle("booking_updates")}
            label="Booking Updates"
            description="Notifications about new, changed, or cancelled bookings"
          />
        </div>
      </SettingsCard>

      {/* Communication */}
      <SettingsCard
        title="Messages & Communication"
        description="Control message notifications"
      >
        <div className="divide-y divide-slate-100">
          <Toggle
            enabled={notifications.new_messages}
            onChange={() => handleToggle("new_messages")}
            label="New Messages"
            description="Get notified when you receive a new message"
          />
        </div>
      </SettingsCard>

      {/* Financial */}
      <SettingsCard
        title="Payments & Billing"
        description="Financial transaction notifications"
      >
        <div className="divide-y divide-slate-100">
          <Toggle
            enabled={notifications.payment_confirmations}
            onChange={() => handleToggle("payment_confirmations")}
            label="Payment Confirmations"
            description="Receipts and payment confirmations 🔒"
          />
        </div>
        <div className="mt-4 p-3 bg-sky-50 border border-sky-100 rounded-lg">
          <p className="text-xs text-sky-800">
            <strong>Note:</strong> Payment notifications cannot be disabled for security and compliance reasons.
          </p>
        </div>
      </SettingsCard>

      {/* Tips & Updates */}
      <SettingsCard
        title="Tips & Updates"
        description="Stay informed about platform news"
      >
        <div className="divide-y divide-slate-100">
          <Toggle
            enabled={notifications.weekly_summary}
            onChange={() => handleToggle("weekly_summary")}
            label="Weekly Summary"
            description="Get a weekly roundup of your activity"
          />
          <Toggle
            enabled={notifications.promotions}
            onChange={() => handleToggle("promotions")}
            label="Promotions & Offers"
            description="Special deals and platform updates"
          />
        </div>
        <div className="mt-4 text-xs text-slate-500">
          You can unsubscribe anytime from our emails.
        </div>
      </SettingsCard>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 bg-rose-500 hover:bg-rose-600"
        >
          <FiSave className="w-4 h-4" />
          {saving ? "Saving..." : "Save Preferences"}
        </Button>
      </div>
    </div>
  );
}
