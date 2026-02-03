'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Mail, Bell, Check } from 'lucide-react';
import {
  notificationPreferencesSchema,
  type NotificationPreferencesFormData,
} from '@/lib/validators/settings';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
} from '@/components/ui';

interface ToggleProps {
  id: string;
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function Toggle({ id, label, description, checked, onChange }: ToggleProps) {
  return (
    <div className="flex items-center justify-between py-3">
      <div className="flex-1 pr-4">
        <label
          htmlFor={id}
          className="text-sm font-medium text-slate-900 dark:text-white cursor-pointer"
        >
          {label}
        </label>
        {description && (
          <p className="text-sm text-slate-500 mt-0.5">{description}</p>
        )}
      </div>
      <button
        type="button"
        id={id}
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
          checked ? 'bg-primary-500' : 'bg-slate-200 dark:bg-slate-700'
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            checked ? 'translate-x-5' : 'translate-x-0'
          }`}
        />
      </button>
    </div>
  );
}

export default function NotificationSettingsPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const form = useForm<NotificationPreferencesFormData>({
    resolver: zodResolver(notificationPreferencesSchema),
    defaultValues: {
      email_booking_confirmations: true,
      email_booking_reminders: true,
      email_messages: true,
      email_marketing: false,
      push_booking_confirmations: true,
      push_booking_reminders: true,
      push_messages: true,
    },
  });

  const values = form.watch();

  const onSubmit = async (data: NotificationPreferencesFormData) => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      // TODO: Implement notification preferences API call
      console.log('Notification preferences:', data);
      await new Promise((resolve) => setTimeout(resolve, 500));
      setSaveSuccess(true);
    } catch {
      // Handle error
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {saveSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
          <Check className="h-4 w-4" />
          <span className="text-sm">Preferences saved successfully!</span>
        </div>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <Mail className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <CardTitle>Email Notifications</CardTitle>
              <CardDescription>
                Choose what email notifications you want to receive
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="divide-y divide-slate-100 dark:divide-slate-800">
          <Toggle
            id="email_booking_confirmations"
            label="Booking Confirmations"
            description="Receive emails when your bookings are confirmed"
            checked={values.email_booking_confirmations}
            onChange={(checked) =>
              form.setValue('email_booking_confirmations', checked)
            }
          />
          <Toggle
            id="email_booking_reminders"
            label="Booking Reminders"
            description="Receive reminder emails before your sessions"
            checked={values.email_booking_reminders}
            onChange={(checked) =>
              form.setValue('email_booking_reminders', checked)
            }
          />
          <Toggle
            id="email_messages"
            label="New Messages"
            description="Receive emails when you get new messages"
            checked={values.email_messages}
            onChange={(checked) => form.setValue('email_messages', checked)}
          />
          <Toggle
            id="email_marketing"
            label="Marketing & Promotions"
            description="Receive emails about new features and promotions"
            checked={values.email_marketing}
            onChange={(checked) => form.setValue('email_marketing', checked)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <Bell className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <CardTitle>Push Notifications</CardTitle>
              <CardDescription>
                Choose what push notifications you want to receive
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="divide-y divide-slate-100 dark:divide-slate-800">
          <Toggle
            id="push_booking_confirmations"
            label="Booking Confirmations"
            description="Get notified when your bookings are confirmed"
            checked={values.push_booking_confirmations}
            onChange={(checked) =>
              form.setValue('push_booking_confirmations', checked)
            }
          />
          <Toggle
            id="push_booking_reminders"
            label="Booking Reminders"
            description="Get reminded before your sessions start"
            checked={values.push_booking_reminders}
            onChange={(checked) =>
              form.setValue('push_booking_reminders', checked)
            }
          />
          <Toggle
            id="push_messages"
            label="New Messages"
            description="Get notified when you receive new messages"
            checked={values.push_messages}
            onChange={(checked) => form.setValue('push_messages', checked)}
          />
        </CardContent>
        <CardFooter className="justify-end">
          <Button type="submit" loading={isSaving}>
            Save Preferences
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
