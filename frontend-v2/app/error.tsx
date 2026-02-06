'use client';

import { useEffect } from 'react';
import { ErrorDisplay } from '@/components/error';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('Global error:', error);
  }, [error]);

  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
      <ErrorDisplay
        title="Something went wrong"
        message="An unexpected error occurred. Our team has been notified."
        onRetry={reset}
        showHome={true}
        showBack={true}
        errorDetails={isDev ? error.message : undefined}
        showDetails={isDev}
      />
    </div>
  );
}
