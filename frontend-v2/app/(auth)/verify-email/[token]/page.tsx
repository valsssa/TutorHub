'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { authApi } from '@/lib/api';
import { Card, CardContent, Skeleton } from '@/components/ui';

type VerificationState = 'loading' | 'success' | 'error';

export default function VerifyEmailPage() {
  const params = useParams();
  const token = params.token as string;

  const [state, setState] = useState<VerificationState>('loading');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const verifyEmail = async () => {
      try {
        await authApi.verifyEmail(token);
        setState('success');
      } catch (err) {
        setState('error');
        if (err instanceof Error) {
          if (err.message.includes('expired') || err.message.includes('invalid')) {
            setError('This verification link has expired or is invalid.');
          } else if (err.message.includes('already verified')) {
            setError('This email has already been verified.');
          } else {
            setError(err.message);
          }
        } else {
          setError('Failed to verify email. Please try again.');
        }
      }
    };

    verifyEmail();
  }, [token]);

  if (state === 'loading') {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center mb-4">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
            <Skeleton className="h-8 w-48 mx-auto mb-2" />
            <Skeleton className="h-4 w-64 mx-auto" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (state === 'success') {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20 mb-4">
              <svg
                className="h-6 w-6 text-green-600 dark:text-green-400"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4.5 12.75l6 6 9-13.5"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Email verified!
            </h2>
            <p className="text-slate-500 mb-6">
              Your email has been successfully verified. You can now sign in to your account.
            </p>
            <Link
              href="/login"
              className="inline-flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20 mb-4">
            <svg
              className="h-6 w-6 text-red-600 dark:text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Verification failed
          </h2>
          <p className="text-slate-500 mb-6">
            {error || 'We could not verify your email address.'}
          </p>
          <div className="space-y-3">
            <Link
              href="/login"
              className="inline-flex items-center justify-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium w-full"
            >
              Sign in
            </Link>
            <p className="text-sm text-slate-500">
              Need help?{' '}
              <a href="mailto:support@edustream.com" className="text-primary-600 hover:underline">
                Contact support
              </a>
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
