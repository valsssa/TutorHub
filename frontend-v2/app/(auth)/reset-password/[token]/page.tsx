'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import Link from 'next/link';
import { authApi } from '@/lib/api';
import { resetPasswordSchema, type ResetPasswordFormData } from '@/lib/validators';
import { Card, CardContent, Button, Input, Skeleton } from '@/components/ui';
import { cn } from '@/lib/utils';

export default function ResetPasswordPage() {
  const params = useParams();
  const router = useRouter();
  const token = params.token as string;

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tokenStatus, setTokenStatus] = useState<'validating' | 'valid' | 'invalid'>('validating');

  const form = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  const passwordValue = form.watch('password');

  // Validate token on mount
  useEffect(() => {
    let cancelled = false;
    async function verifyToken() {
      try {
        await authApi.verifyResetToken(token);
        if (!cancelled) setTokenStatus('valid');
      } catch {
        if (!cancelled) setTokenStatus('invalid');
      }
    }
    verifyToken();
    return () => { cancelled = true; };
  }, [token]);

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

  // Show loading state while validating token
  if (tokenStatus === 'validating') {
    return (
      <Card>
        <CardContent>
          <Skeleton className="h-7 sm:h-8 w-48 mb-2" />
          <Skeleton className="h-5 w-56 mb-4 sm:mb-6" />
          <div className="space-y-3 sm:space-y-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-11 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Show error state if token is invalid
  if (tokenStatus === 'invalid') {
    return (
      <Card>
        <CardContent>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Invalid reset link
          </h2>
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 mb-4">
            <p className="text-sm text-red-600 dark:text-red-400">
              This password reset link has expired or is invalid. Please request a new one.
            </p>
          </div>
          <div className="space-y-3">
            <Button asChild className="w-full">
              <Link href="/forgot-password">
                Request a new reset link
              </Link>
            </Button>
            <div className="text-center text-sm">
              <Link
                href="/login"
                className="text-primary-600 hover:underline"
              >
                Back to login
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-2">
          Reset your password
        </h2>
        <p className="text-sm sm:text-base text-slate-500 mb-4 sm:mb-6">
          Enter your new password below.
        </p>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3 sm:space-y-4">
          <div>
            <Input
              label="New password"
              type="password"
              placeholder="Enter new password"
              autoComplete="new-password"
              error={form.formState.errors.password?.message}
              {...form.register('password')}
            />
            <ul className="mt-2 space-y-1 text-xs">
              <li className={cn(
                'flex items-center gap-1.5',
                passwordValue.length >= 8 ? 'text-green-600 dark:text-green-400' : 'text-slate-400 dark:text-slate-500'
              )}>
                <span>{passwordValue.length >= 8 ? '\u2713' : '\u2717'}</span>
                At least 8 characters
              </li>
              <li className={cn(
                'flex items-center gap-1.5',
                /[A-Z]/.test(passwordValue) ? 'text-green-600 dark:text-green-400' : 'text-slate-400 dark:text-slate-500'
              )}>
                <span>{/[A-Z]/.test(passwordValue) ? '\u2713' : '\u2717'}</span>
                One uppercase letter
              </li>
              <li className={cn(
                'flex items-center gap-1.5',
                /[a-z]/.test(passwordValue) ? 'text-green-600 dark:text-green-400' : 'text-slate-400 dark:text-slate-500'
              )}>
                <span>{/[a-z]/.test(passwordValue) ? '\u2713' : '\u2717'}</span>
                One lowercase letter
              </li>
              <li className={cn(
                'flex items-center gap-1.5',
                /[0-9]/.test(passwordValue) ? 'text-green-600 dark:text-green-400' : 'text-slate-400 dark:text-slate-500'
              )}>
                <span>{/[0-9]/.test(passwordValue) ? '\u2713' : '\u2717'}</span>
                One number
              </li>
            </ul>
          </div>

          <Input
            label="Confirm password"
            type="password"
            placeholder="Confirm new password"
            autoComplete="new-password"
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
