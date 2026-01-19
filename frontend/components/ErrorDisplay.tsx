"use client";

import Link from 'next/link'

interface ErrorDisplayProps {
  title: string
  message: string
  statusCode?: number
  suggestion?: string
  actionLabel?: string
  actionHref?: string
  showBackButton?: boolean
  variant?: 'error' | 'warning' | 'info'
}

export default function ErrorDisplay({
  title,
  message,
  statusCode,
  suggestion,
  actionLabel = 'Go to Homepage',
  actionHref = '/',
  showBackButton = true,
  variant = 'error',
}: ErrorDisplayProps) {
  const variantStyles = {
    error: {
      bg: 'from-red-50 to-orange-50',
      iconBg: 'bg-red-100',
      iconColor: 'text-red-600',
      buttonBg: 'bg-red-600 hover:bg-red-700',
    },
    warning: {
      bg: 'from-yellow-50 to-orange-50',
      iconBg: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      buttonBg: 'bg-yellow-600 hover:bg-yellow-700',
    },
    info: {
      bg: 'from-blue-50 to-indigo-50',
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      buttonBg: 'bg-blue-600 hover:bg-blue-700',
    },
  }

  const styles = variantStyles[variant]

  return (
    <div className={`min-h-screen flex items-center justify-center bg-gradient-to-br ${styles.bg} p-4`}>
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 md:p-12 text-center">
        {/* Icon */}
        <div className="mb-6">
          <div className={`inline-flex items-center justify-center w-24 h-24 ${styles.iconBg} rounded-full mb-4`}>
            {variant === 'error' && (
              <svg
                className={`w-12 h-12 ${styles.iconColor}`}
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
            )}
            {variant === 'warning' && (
              <svg
                className={`w-12 h-12 ${styles.iconColor}`}
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
            )}
            {variant === 'info' && (
              <svg
                className={`w-12 h-12 ${styles.iconColor}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            )}
          </div>
          {statusCode && (
            <h1 className="text-6xl font-bold text-gray-900 mb-2">{statusCode}</h1>
          )}
        </div>

        {/* Error Message */}
        <h2 className="text-3xl font-bold text-gray-900 mb-4">{title}</h2>
        <p className="text-gray-600 text-lg mb-2">{message}</p>

        {suggestion && (
          <p className="text-gray-500 text-sm mb-8">{suggestion}</p>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mt-8">
          <Link
            href={actionHref}
            className={`inline-flex items-center justify-center px-6 py-3 ${styles.buttonBg} text-white font-medium rounded-lg transition-colors`}
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
            {actionLabel}
          </Link>
          {showBackButton && (
            <button
              onClick={() => window.history.back()}
              className="inline-flex items-center justify-center px-6 py-3 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition-colors"
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
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
              Go Back
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
