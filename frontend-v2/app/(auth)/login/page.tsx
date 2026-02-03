'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/hooks';
import { loginSchema, type LoginFormData } from '@/lib/validators';
import { Card, CardContent, Button, Input } from '@/components/ui';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoggingIn, loginError } = useAuth();

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data);
      router.push('/student');
    } catch {
      // Error handled by useAuth
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">
          Welcome back
        </h2>

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
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
