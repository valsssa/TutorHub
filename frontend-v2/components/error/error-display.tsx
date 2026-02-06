'use client';

import Link from 'next/link';
import { AlertCircle, RefreshCw, Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';

interface ErrorDisplayProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  showHome?: boolean;
  showBack?: boolean;
  errorDetails?: string;
  showDetails?: boolean;
  className?: string;
}

export function ErrorDisplay({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again later.',
  onRetry,
  showHome = true,
  showBack = false,
  errorDetails,
  showDetails = false,
  className,
}: ErrorDisplayProps) {
  return (
    <div
      className={cn(
        'flex min-h-[300px] sm:min-h-[400px] flex-col items-center justify-center text-center px-4',
        className
      )}
    >
      <div className="rounded-full bg-red-100 p-3 sm:p-4 dark:bg-red-900/20">
        <AlertCircle className="h-8 w-8 sm:h-12 sm:w-12 text-red-500" />
      </div>

      <h1 className="mt-4 sm:mt-6 text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
        {title}
      </h1>

      <p className="mt-2 max-w-md text-sm sm:text-base text-slate-600 dark:text-slate-400">
        {message}
      </p>

      {showDetails && errorDetails && (
        <div className="mt-4 max-w-lg rounded-lg bg-slate-100 p-4 dark:bg-slate-800">
          <p className="text-left text-sm font-mono text-slate-700 dark:text-slate-300 break-all">
            {errorDetails}
          </p>
        </div>
      )}

      <div className="mt-6 sm:mt-8 flex flex-wrap items-center justify-center gap-3 w-full sm:w-auto">
        {onRetry && (
          <Button onClick={onRetry} variant="primary">
            <RefreshCw className="mr-2 h-4 w-4" />
            Try again
          </Button>
        )}

        {showBack && (
          <Button
            onClick={() => window.history.back()}
            variant="secondary"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Go back
          </Button>
        )}

        {showHome && (
          <Button asChild variant={onRetry ? 'outline' : 'primary'}>
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              Go home
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
