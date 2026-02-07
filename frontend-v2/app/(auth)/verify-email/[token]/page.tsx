'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { authApi } from '@/lib/api';
import { Card, CardContent, Button, Skeleton } from '@/components/ui';

type VerificationState = 'loading' | 'success' | 'error';

export default function VerifyEmailPage() {
  const params = useParams();
  const token = params.token as string;

  const [state, setState] = useState<VerificationState>('loading');
  const [error, setError] = useState<string | null>(null);
  const [resendEmail, setResendEmail] = useState('');
  const [resendState, setResendState] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');

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
        <CardContent>
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center mb-4">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
            </div>
            <Skeleton className="h-7 sm:h-8 w-48 mx-auto mb-2" />
            <Skeleton className="h-4 w-56 sm:w-64 mx-auto" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (state === 'success') {
    return (
      <Card>
        <CardContent>
          <div className="text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20 mb-4">
              <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Email verified!
            </h2>
            <p className="text-sm sm:text-base text-slate-500 mb-6">
              Your email has been successfully verified. You can now sign in to your account.
            </p>
            <Button asChild>
              <Link href="/login">Sign in</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20 mb-4">
            <AlertCircle className="h-6 w-6 text-red-600 dark:text-red-400" />
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white mb-2">
            Verification failed
          </h2>
          <p className="text-sm sm:text-base text-slate-500 mb-6">
            {error || 'We could not verify your email address.'}
          </p>
          <div className="space-y-3">
            {resendState === 'sent' ? (
              <p className="text-sm text-green-600 dark:text-green-400">
                Verification email sent! Please check your inbox.
              </p>
            ) : (
              <div className="space-y-2">
                <input
                  type="email"
                  placeholder="Enter your email address"
                  value={resendEmail}
                  onChange={(e) => setResendEmail(e.target.value)}
                  className="flex w-full rounded-xl border bg-white px-3 py-2 text-base sm:text-sm border-slate-200 dark:border-slate-700 dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent placeholder:text-slate-400 dark:placeholder:text-slate-500"
                />
                <Button
                  className="w-full"
                  variant="outline"
                  disabled={!resendEmail || resendState === 'sending'}
                  onClick={async () => {
                    setResendState('sending');
                    try {
                      await authApi.resendVerificationEmail(resendEmail);
                      setResendState('sent');
                    } catch {
                      setResendState('error');
                    }
                  }}
                >
                  {resendState === 'sending' ? 'Sending...' : 'Resend verification email'}
                </Button>
                {resendState === 'error' && (
                  <p className="text-xs text-red-500">
                    Failed to resend. Please check your email and try again.
                  </p>
                )}
              </div>
            )}
            <Button asChild className="w-full">
              <Link href="/login">Sign in</Link>
            </Button>
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
