'use client';

import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Check, AlertCircle, Mail, AlertTriangle } from 'lucide-react';
import { useAuth, useUpdateProfile, useRequestPasswordReset } from '@/lib/hooks';
import { accountSettingsSchema, type AccountSettingsFormData } from '@/lib/validators/settings';
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

const timezones = [
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)' },
  { value: 'Europe/London', label: 'London (GMT)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Europe/Berlin', label: 'Berlin (CET)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
  { value: 'Australia/Sydney', label: 'Sydney (AEST)' },
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
];

export default function AccountSettingsPage() {
  const { user, isLoading: isLoadingUser } = useAuth();
  const updateProfile = useUpdateProfile();
  const requestPasswordReset = useRequestPasswordReset();

  const [timezoneSuccess, setTimezoneSuccess] = useState(false);
  const [passwordResetSent, setPasswordResetSent] = useState(false);

  const accountForm = useForm<AccountSettingsFormData>({
    resolver: zodResolver(accountSettingsSchema),
    defaultValues: {
      timezone: 'UTC',
    },
  });

  // Reset form when user data loads
  useEffect(() => {
    if (user) {
      accountForm.reset({
        timezone: user.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
    }
  }, [user, accountForm]);

  const onTimezoneSubmit = async (data: AccountSettingsFormData) => {
    setTimezoneSuccess(false);
    try {
      await updateProfile.mutateAsync({
        timezone: data.timezone,
      });
      setTimezoneSuccess(true);
      setTimeout(() => setTimezoneSuccess(false), 3000);
    } catch {
      // Error handled by mutation
    }
  };

  const handlePasswordReset = async () => {
    if (!user?.email) return;

    setPasswordResetSent(false);
    try {
      await requestPasswordReset.mutateAsync(user.email);
      setPasswordResetSent(true);
    } catch {
      // Error handled by mutation
    }
  };

  if (isLoadingUser) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64 mt-2" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-64 mt-2" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Password Reset Section */}
      <Card>
        <CardHeader>
          <CardTitle>Password</CardTitle>
          <CardDescription>
            Request a password reset link to change your password
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {passwordResetSent && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
              <Check className="h-4 w-4" />
              <span className="text-sm">
                Password reset link sent to {user?.email}. Check your inbox.
              </span>
            </div>
          )}

          {requestPasswordReset.isError && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">
                {requestPasswordReset.error instanceof Error
                  ? requestPasswordReset.error.message
                  : 'Failed to send reset link'}
              </span>
            </div>
          )}

          <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-200 dark:bg-slate-700">
                <Mail className="h-5 w-5 text-slate-600 dark:text-slate-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900 dark:text-white">
                  Email: {user?.email}
                </p>
                <p className="text-xs text-slate-500">
                  A password reset link will be sent to this email
                </p>
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={handlePasswordReset}
              loading={requestPasswordReset.isPending}
            >
              Send Reset Link
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Timezone Section */}
      <Card>
        <form onSubmit={accountForm.handleSubmit(onTimezoneSubmit)}>
          <CardHeader>
            <CardTitle>Timezone</CardTitle>
            <CardDescription>
              Set your timezone for accurate booking times
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {timezoneSuccess && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
                <Check className="h-4 w-4" />
                <span className="text-sm">Timezone updated successfully!</span>
              </div>
            )}

            {updateProfile.isError && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">
                  {updateProfile.error instanceof Error
                    ? updateProfile.error.message
                    : 'Failed to update timezone'}
                </span>
              </div>
            )}

            <div className="space-y-1.5">
              <label
                htmlFor="timezone"
                className="text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Timezone
              </label>
              <select
                id="timezone"
                className="flex h-10 w-full rounded-xl border bg-white px-3 py-2 text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                {...accountForm.register('timezone')}
              >
                {timezones.map((tz) => (
                  <option key={tz.value} value={tz.value}>
                    {tz.label}
                  </option>
                ))}
              </select>
              {accountForm.formState.errors.timezone && (
                <p className="text-sm text-red-500">
                  {accountForm.formState.errors.timezone.message}
                </p>
              )}
              <p className="text-xs text-slate-500">
                Your current browser timezone is: {Intl.DateTimeFormat().resolvedOptions().timeZone}
              </p>
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button type="submit" loading={updateProfile.isPending}>
              Save Timezone
            </Button>
          </CardFooter>
        </form>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200 dark:border-red-900">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <CardTitle className="text-red-600">Danger Zone</CardTitle>
              <CardDescription>
                Irreversible account actions
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 border border-red-200 dark:border-red-800 rounded-xl">
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">
                Delete Account
              </p>
              <p className="text-xs text-slate-500">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
            </div>
            <Button
              type="button"
              variant="outline"
              className="border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:hover:bg-red-900/20"
              onClick={() => {
                // TODO: Implement account deletion with confirmation modal
                alert('Account deletion requires confirmation. This feature is coming soon.');
              }}
            >
              Delete Account
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
