'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import * as Sentry from '@sentry/nextjs'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // Log the error to Sentry for production monitoring
    Sentry.captureException(error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-orange-50 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-2xl w-full bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8 md:p-12 text-center">
        {/* Error Icon */}
        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-red-100 rounded-full mb-4">
            <svg
              className="w-12 h-12 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <h1 className="text-6xl font-bold text-slate-900 dark:text-white mb-2">Oops!</h1>
        </div>

        {/* Error Message */}
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
          Something went wrong
        </h2>
        <p className="text-slate-600 dark:text-slate-400 text-lg mb-2">
          We encountered an unexpected error while processing your request.
        </p>

        {/* Error Details (only in development) */}
        {process.env.NODE_ENV === 'development' && error.message && (
          <div className="my-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-left text-red-800 font-mono break-all">
              <strong>Error:</strong> {error.message}
            </p>
            {error.digest && (
              <p className="text-xs text-left text-red-600 mt-2 font-mono">
                <strong>Digest:</strong> {error.digest}
              </p>
            )}
          </div>
        )}

        <p className="text-slate-500 dark:text-slate-400 text-sm mb-8">
          Don&apos;t worry, our team has been notified and we&apos;re working on it.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={reset}
            className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Try Again
          </button>
          <Link
            href="/"
            className="inline-flex items-center justify-center px-6 py-3 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors"
          >
            <svg
              className="w-5 h-5 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            Go to Homepage
          </Link>
        </div>

        {/* Support Information */}
        <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-2">
            Need immediate help?
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link
              href="/support"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              Contact Support
            </Link>
            <span className="text-slate-300 dark:text-slate-600">•</span>
            <Link
              href="/support"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              Help Center
            </Link>
            <span className="text-slate-300 dark:text-slate-600">•</span>
            <a
              href="mailto:support@edustream.com"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              Email Us
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
