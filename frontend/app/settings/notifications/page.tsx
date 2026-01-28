"use client";

import { useState } from "react";
import { Mail, Bell } from "lucide-react";
import { useToast } from "@/components/ToastContainer";
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
    <div className="max-w-2xl space-y-8 animate-in fade-in duration-300">
      <div>
        <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Notification Preferences</h3>
        <p className="text-slate-500 dark:text-slate-400 mb-8">Manage how and when you hear from us.</p>

        <div className="flex items-center gap-2 mb-2 text-slate-900 dark:text-white font-bold text-lg">
          <Mail size={20} /> Email notifications
        </div>
        <p className="text-slate-500 dark:text-slate-400 mb-6 text-sm">Manage the emails you receive from us.</p>

        <div className="space-y-6">
          {/* Transactional */}
          <div className="flex items-start justify-between pb-6 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h4 className="font-bold text-slate-900 dark:text-white mb-1">Transactional</h4>
              <p className="text-slate-500 dark:text-slate-400 text-sm">Important updates about your account and activity.</p>
            </div>
            <span className="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-xs font-bold px-3 py-1.5 rounded">Always active</span>
          </div>

          {/* Tips and discounts */}
          <Toggle
            enabled={notifications.promotions}
            onChange={() => handleToggle("promotions")}
            label="Tips and discounts"
            description="Get learning resources and exclusive offers to support your progress."
          />

          {/* Surveys and interviews */}
          <Toggle
            enabled={notifications.weekly_summary}
            onChange={() => handleToggle("weekly_summary")}
            label="Surveys and interviews"
            description="Take part in research studies to help us improve the platform."
          />
        </div>

        <div className="pt-8">
          <button 
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
          >
            {saving ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
