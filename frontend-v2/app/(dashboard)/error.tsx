'use client';

import { useEffect } from 'react';
import { ErrorDisplay } from '@/components/error';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function DashboardError({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('Dashboard error:', error);
  }, [error]);

  const isDev = process.env.NODE_ENV === 'development';

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
      <ErrorDisplay
        title="Dashboard Error"
        message="Something went wrong while loading this page. Please try again."
        onRetry={reset}
        showHome={true}
        showBack={false}
        errorDetails={isDev ? error.message : undefined}
        showDetails={isDev}
      />
    </div>
  );
}
