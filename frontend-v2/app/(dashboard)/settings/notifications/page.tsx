'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Bell, Check, AlertCircle, Settings2 } from 'lucide-react';
import { useNotificationPreferences, useUpdateNotificationPreferences } from '@/lib/hooks';
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
  Skeleton,
} from '@/components/ui';

interface ToggleProps {
  id: string;
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

function Toggle({ id, label, description, checked, onChange, disabled }: ToggleProps) {
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
        onClick={() => !disabled && onChange(!checked)}
        disabled={disabled}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
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

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-64 mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center justify-between py-3">
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-6 w-11 rounded-full" />
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-64 mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between py-3">
              <div className="space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-6 w-11 rounded-full" />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

export default function NotificationSettingsPage() {
  const { data: preferences, isLoading, error: fetchError } = useNotificationPreferences();
  const updatePreferences = useUpdateNotificationPreferences();
  const [saveSuccess, setSaveSuccess] = useState(false);

  const form = useForm<NotificationPreferencesFormData>({
    resolver: zodResolver(notificationPreferencesSchema),
    defaultValues: {
      email_enabled: true,
      push_enabled: true,
      session_reminders_enabled: true,
      booking_requests_enabled: true,
      review_prompts_enabled: true,
      marketing_enabled: false,
    },
  });

  const values = form.watch();

  // Reset form when preferences load from API
  useEffect(() => {
    if (preferences) {
      form.reset({
        email_enabled: preferences.email_enabled ?? true,
        push_enabled: preferences.push_enabled ?? true,
        session_reminders_enabled: preferences.session_reminders_enabled ?? true,
        booking_requests_enabled: preferences.booking_requests_enabled ?? true,
        review_prompts_enabled: preferences.review_prompts_enabled ?? true,
        marketing_enabled: preferences.marketing_enabled ?? false,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preferences]);

  const onSubmit = async (data: NotificationPreferencesFormData) => {
    setSaveSuccess(false);
    try {
      await updatePreferences.mutateAsync(data);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch {
      // Error handled by mutation
    }
  };

  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (fetchError) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-4 text-center">
            <AlertCircle className="h-10 w-10 text-red-500" />
            <div>
              <p className="font-medium text-slate-900 dark:text-white">
                Failed to load preferences
              </p>
              <p className="text-sm text-slate-500">
                {fetchError instanceof Error ? fetchError.message : 'Please try again later'}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
      {saveSuccess && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
          <Check className="h-4 w-4" />
          <span className="text-sm">Preferences saved successfully!</span>
        </div>
      )}

      {updatePreferences.isError && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">
            {updatePreferences.error instanceof Error
              ? updatePreferences.error.message
              : 'Failed to save preferences'}
          </span>
        </div>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary-100 dark:bg-primary-900/30">
              <Settings2 className="h-5 w-5 text-primary-600" />
            </div>
            <div>
              <CardTitle>Notification Channels</CardTitle>
              <CardDescription>
                Enable or disable notification delivery channels
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="divide-y divide-slate-100 dark:divide-slate-800">
          <Toggle
            id="email_enabled"
            label="Email Notifications"
            description="Receive notifications via email"
            checked={values.email_enabled}
            onChange={(checked) => form.setValue('email_enabled', checked)}
            disabled={updatePreferences.isPending}
          />
          <Toggle
            id="push_enabled"
            label="Push Notifications"
            description="Receive push notifications in your browser"
            checked={values.push_enabled}
            onChange={(checked) => form.setValue('push_enabled', checked)}
            disabled={updatePreferences.isPending}
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
              <CardTitle>Notification Types</CardTitle>
              <CardDescription>
                Choose which types of notifications you want to receive
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="divide-y divide-slate-100 dark:divide-slate-800">
          <Toggle
            id="session_reminders_enabled"
            label="Session Reminders"
            description="Get reminded before your sessions start"
            checked={values.session_reminders_enabled}
            onChange={(checked) => form.setValue('session_reminders_enabled', checked)}
            disabled={updatePreferences.isPending}
          />
          <Toggle
            id="booking_requests_enabled"
            label="Booking Requests"
            description="Get notified when you receive new booking requests"
            checked={values.booking_requests_enabled}
            onChange={(checked) => form.setValue('booking_requests_enabled', checked)}
            disabled={updatePreferences.isPending}
          />
          <Toggle
            id="review_prompts_enabled"
            label="Review Prompts"
            description="Get prompted to review completed sessions"
            checked={values.review_prompts_enabled}
            onChange={(checked) => form.setValue('review_prompts_enabled', checked)}
            disabled={updatePreferences.isPending}
          />
          <Toggle
            id="marketing_enabled"
            label="Marketing & Promotions"
            description="Receive updates about new features and promotions"
            checked={values.marketing_enabled}
            onChange={(checked) => form.setValue('marketing_enabled', checked)}
            disabled={updatePreferences.isPending}
          />
        </CardContent>
        <CardFooter className="justify-end">
          <Button type="submit" loading={updatePreferences.isPending}>
            Save Preferences
          </Button>
        </CardFooter>
      </Card>
    </form>
  );
}
