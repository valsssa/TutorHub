'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { authApi } from '@/lib/api';
import { resetPasswordSchema, type ResetPasswordFormData } from '@/lib/validators';
import { Card, CardContent, Button, Input } from '@/components/ui';

export default function ResetPasswordPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    setIsSubmitting(true);
    setError(null);

    try {
      await authApi.resetPassword(token, data.password);
      router.push('/login?reset=true');
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('expired') || err.message.includes('invalid')) {
          setError('This reset link has expired or is invalid. Please request a new one.');
        } else {
          setError(err.message);
        }
      } else {
        setError('Failed to reset password. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card>
      <CardContent className="p-4 sm:p-6">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Reset your password
        </h2>
        <p className="text-sm sm:text-base text-slate-500 mb-4 sm:mb-6">
          Enter your new password below.
        </p>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3 sm:space-y-4">
          <Input
            label="New password"
            type="password"
            placeholder="Enter new password"
            hint="Min 8 characters with uppercase, lowercase, and number"
            error={form.formState.errors.password?.message}
            {...form.register('password')}
          />

          <Input
            label="Confirm password"
            type="password"
            placeholder="Confirm new password"
            error={form.formState.errors.confirmPassword?.message}
            {...form.register('confirmPassword')}
          />

          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              {error.includes('expired') && (
                <Link
                  href="/forgot-password"
                  className="text-sm text-red-600 dark:text-red-400 underline mt-1 inline-block"
                >
                  Request a new reset link
                </Link>
              )}
            </div>
          )}

          <Button type="submit" loading={isSubmitting} className="w-full">
            Reset password
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <Link
            href="/login"
            className="text-primary-600 hover:underline"
          >
            Back to login
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
