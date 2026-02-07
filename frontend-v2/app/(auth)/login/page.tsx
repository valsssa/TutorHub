'use client';

import { Suspense, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/hooks';
import { loginSchema, type LoginFormData } from '@/lib/validators';
import { Card, CardContent, Button, Input, Skeleton } from '@/components/ui';

function LoginFormSkeleton() {
  return (
    <Card>
      <CardContent>
        <Skeleton className="h-7 sm:h-8 w-40 mb-4 sm:mb-6" />
        <div className="space-y-3 sm:space-y-4">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-11 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoading, login, isLoggingIn, loginError } = useAuth();

  const registered = searchParams.get('registered') === 'true';
  const reset = searchParams.get('reset') === 'true';
  const verified = searchParams.get('verified') === 'true';

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const getRoleBasedRedirect = (role?: string) => {
    switch (role) {
      case 'admin': return '/admin';
      case 'tutor': return '/tutor';
      case 'owner': return '/owner';
      default: return '/student';
    }
  };

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data);
      // Redirect will happen after query invalidation refetches user
    } catch {
      // Error handled by useAuth
    }
  };

  // Redirect after successful login once user data is available
  useEffect(() => {
    if (user && !isLoggingIn) {
      const redirectTo = searchParams.get('redirect');
      if (redirectTo && redirectTo.startsWith('/') && !redirectTo.startsWith('//')) {
        router.push(redirectTo);
      } else {
        router.push(getRoleBasedRedirect(user.role));
      }
    }
  }, [user, isLoggingIn, router, searchParams]);

  // Show loading skeleton while checking auth status
  if (isLoading) {
    return <LoginFormSkeleton />;
  }

  // Already authenticated — show skeleton while redirect fires
  if (user) {
    return <LoginFormSkeleton />;
  }

  return (
    <Card>
      <CardContent>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-4 sm:mb-6">
          Welcome back
        </h2>

        {(() => {
          const message = verified
            ? 'Email verified successfully! Please sign in.'
            : reset
              ? 'Password reset successfully! Please sign in with your new password.'
              : registered
                ? 'Account created successfully! Please sign in.'
                : null;
          if (!message) return null;
          return (
            <div className="mb-4 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
              <p className="text-sm text-green-600 dark:text-green-400">
                {message}
              </p>
            </div>
          );
        })()}

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3 sm:space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            error={form.formState.errors.email?.message}
            {...form.register('email')}
          />

          <Input
            label="Password"
            type="password"
            placeholder="Enter your password"
            error={form.formState.errors.password?.message}
            {...form.register('password')}
          />

          {loginError && (
            <p className="text-sm text-red-500">
              {loginError instanceof Error ? loginError.message : 'Login failed'}
            </p>
          )}

          <Button type="submit" loading={isLoggingIn} className="w-full">
            Sign in
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <Link
            href="/forgot-password"
            className="text-primary-600 hover:underline"
          >
            Forgot password?
          </Link>
        </div>

        <div className="mt-4 text-center text-sm text-slate-500">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-primary-600 hover:underline">
            Sign up
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFormSkeleton />}>
      <LoginForm />
    </Suspense>
  );
}
