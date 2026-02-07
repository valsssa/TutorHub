'use client';

import { Suspense, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/hooks';
import { registerSchema, type RegisterFormData } from '@/lib/validators';
import { Card, CardContent, Button, Input, Skeleton } from '@/components/ui';
import { cn } from '@/lib/utils';

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const roleParam = searchParams.get('role');
  const defaultRole = roleParam === 'student' || roleParam === 'tutor' ? roleParam : 'student';
  const { user, isLoading, register: registerUser, isRegistering, registerError } = useAuth();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (user && !isLoading) {
      const getRoleBasedRedirect = (role?: string) => {
        switch (role) {
          case 'admin': return '/admin';
          case 'tutor': return '/tutor';
          case 'owner': return '/owner';
          default: return '/student';
        }
      };
      router.push(getRoleBasedRedirect(user.role));
    }
  }, [user, isLoading, router]);

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      first_name: '',
      last_name: '',
      role: defaultRole,
    },
  });

  const selectedRole = form.watch('role');
  const passwordValue = form.watch('password');

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        first_name: data.first_name,
        last_name: data.last_name,
        role: data.role,
      });
      router.push('/login?registered=true');
    } catch {
      // Error handled by useAuth
    }
  };

  // Show skeleton while checking auth or if already authenticated
  if (isLoading || user) {
    return <RegisterFormSkeleton />;
  }

  return (
    <Card>
      <CardContent>
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-4 sm:mb-6">
          Create your account
        </h2>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-3 sm:space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              I want to
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                disabled={isRegistering}
                onClick={() => form.setValue('role', 'student')}
                className={cn(
                  'p-3 rounded-xl border-2 text-center transition-colors',
                  'disabled:pointer-events-none disabled:opacity-50',
                  selectedRole === 'student'
                    ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/20'
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'
                )}
              >
                <span className="font-medium">Learn</span>
                <p className="text-xs text-slate-500 mt-1">Find tutors</p>
              </button>
              <button
                type="button"
                disabled={isRegistering}
                onClick={() => form.setValue('role', 'tutor')}
                className={cn(
                  'p-3 rounded-xl border-2 text-center transition-colors',
                  'disabled:pointer-events-none disabled:opacity-50',
                  selectedRole === 'tutor'
                    ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/20'
                    : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'
                )}
              >
                <span className="font-medium">Teach</span>
                <p className="text-xs text-slate-500 mt-1">Become a tutor</p>
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First name"
              placeholder="John"
              error={form.formState.errors.first_name?.message}
              {...form.register('first_name')}
            />
            <Input
              label="Last name"
              placeholder="Doe"
              error={form.formState.errors.last_name?.message}
              {...form.register('last_name')}
            />
          </div>

          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            error={form.formState.errors.email?.message}
            {...form.register('email')}
          />

          <div>
            <Input
              label="Password"
              type="password"
              placeholder="••••••••"
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
            placeholder="••••••••"
            autoComplete="new-password"
            error={form.formState.errors.confirmPassword?.message}
            {...form.register('confirmPassword')}
          />

          {form.formState.errors.root && (
            <p className="text-sm text-red-500" role="alert">
              {form.formState.errors.root.message}
            </p>
          )}

          {registerError && (
            <div className="text-sm text-red-500" role="alert">
              {registerError instanceof Error &&
              /already (exists|registered)/i.test(registerError.message) ? (
                <p>
                  An account with this email already exists.{' '}
                  <Link href="/login" className="text-primary-600 hover:underline font-medium">
                    Sign in instead
                  </Link>
                </p>
              ) : (
                <p>
                  {registerError instanceof Error ? registerError.message : 'Registration failed'}
                </p>
              )}
            </div>
          )}

          <Button type="submit" loading={isRegistering} className="w-full">
            Create account
          </Button>
        </form>

        <div className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{' '}
          <Link href="/login" className="text-primary-600 hover:underline">
            Sign in
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

function RegisterFormSkeleton() {
  return (
    <Card>
      <CardContent>
        <Skeleton className="h-7 sm:h-8 w-48 mb-4 sm:mb-6" />
        <div className="space-y-3 sm:space-y-4">
          <Skeleton className="h-20 w-full" />
          <div className="grid grid-cols-2 gap-3">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<RegisterFormSkeleton />}>
      <RegisterForm />
    </Suspense>
  );
}
