'use client';

import { Suspense } from 'react';
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
  const defaultRole = searchParams.get('role') as 'student' | 'tutor' | null;
  const { register: registerUser, isRegistering, registerError } = useAuth();

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      first_name: '',
      last_name: '',
      role: defaultRole || 'student',
    },
  });

  const selectedRole = form.watch('role');

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

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
          Create your account
        </h2>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              I want to
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => form.setValue('role', 'student')}
                className={cn(
                  'p-3 rounded-xl border-2 text-center transition-colors',
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
                onClick={() => form.setValue('role', 'tutor')}
                className={cn(
                  'p-3 rounded-xl border-2 text-center transition-colors',
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
              error={form.formState.errors.first_name?.message}
              {...form.register('first_name')}
            />
            <Input
              label="Last name"
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

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            hint="Min 8 characters with uppercase, lowercase, and number"
            error={form.formState.errors.password?.message}
            {...form.register('password')}
          />

          <Input
            label="Confirm password"
            type="password"
            placeholder="••••••••"
            error={form.formState.errors.confirmPassword?.message}
            {...form.register('confirmPassword')}
          />

          {registerError && (
            <p className="text-sm text-red-500">
              {registerError instanceof Error ? registerError.message : 'Registration failed'}
            </p>
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
      <CardContent className="p-6">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="space-y-4">
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
