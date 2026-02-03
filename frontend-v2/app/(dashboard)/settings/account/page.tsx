'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, Check } from 'lucide-react';
import {
  passwordChangeSchema,
  accountSettingsSchema,
  type PasswordChangeFormData,
  type AccountSettingsFormData,
} from '@/lib/validators/settings';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  Input,
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
];

export default function AccountSettingsPage() {
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isSavingTimezone, setIsSavingTimezone] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  const passwordForm = useForm<PasswordChangeFormData>({
    resolver: zodResolver(passwordChangeSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  const accountForm = useForm<AccountSettingsFormData>({
    resolver: zodResolver(accountSettingsSchema),
    defaultValues: {
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    },
  });

  const onPasswordSubmit = async (data: PasswordChangeFormData) => {
    setIsChangingPassword(true);
    setPasswordSuccess(false);
    try {
      // TODO: Implement password change API call
      console.log('Password change:', data);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setPasswordSuccess(true);
      passwordForm.reset();
    } catch {
      // Handle error
    } finally {
      setIsChangingPassword(false);
    }
  };

  const onTimezoneSubmit = async (data: AccountSettingsFormData) => {
    setIsSavingTimezone(true);
    try {
      // TODO: Implement timezone save API call
      console.log('Timezone save:', data);
      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch {
      // Handle error
    } finally {
      setIsSavingTimezone(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)}>
          <CardHeader>
            <CardTitle>Change Password</CardTitle>
            <CardDescription>
              Update your password to keep your account secure
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {passwordSuccess && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400">
                <Check className="h-4 w-4" />
                <span className="text-sm">Password changed successfully!</span>
              </div>
            )}

            <div className="relative">
              <Input
                label="Current Password"
                type={showCurrentPassword ? 'text' : 'password'}
                placeholder="Enter current password"
                error={passwordForm.formState.errors.current_password?.message}
                {...passwordForm.register('current_password')}
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute right-3 top-[34px] text-slate-400 hover:text-slate-600"
              >
                {showCurrentPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>

            <div className="relative">
              <Input
                label="New Password"
                type={showNewPassword ? 'text' : 'password'}
                placeholder="Enter new password"
                error={passwordForm.formState.errors.new_password?.message}
                hint="Must be at least 8 characters with uppercase, lowercase, and number"
                {...passwordForm.register('new_password')}
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3 top-[34px] text-slate-400 hover:text-slate-600"
              >
                {showNewPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>

            <div className="relative">
              <Input
                label="Confirm New Password"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="Confirm new password"
                error={passwordForm.formState.errors.confirm_password?.message}
                {...passwordForm.register('confirm_password')}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-[34px] text-slate-400 hover:text-slate-600"
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button type="submit" loading={isChangingPassword}>
              Change Password
            </Button>
          </CardFooter>
        </form>
      </Card>

      <Card>
        <form onSubmit={accountForm.handleSubmit(onTimezoneSubmit)}>
          <CardHeader>
            <CardTitle>Timezone</CardTitle>
            <CardDescription>
              Set your timezone for accurate booking times
            </CardDescription>
          </CardHeader>
          <CardContent>
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
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button type="submit" loading={isSavingTimezone}>
              Save Timezone
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
