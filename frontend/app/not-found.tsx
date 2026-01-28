"use client";

import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 p-4">
      <div className="max-w-2xl w-full bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8 md:p-12 text-center">
        {/* 404 Icon */}
        <div className="mb-6">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-blue-100 rounded-full mb-4">
            <svg
              className="w-12 h-12 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h1 className="text-6xl font-bold text-slate-900 dark:text-white mb-2">404</h1>
        </div>

        {/* Error Message */}
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
          Page Not Found
        </h2>
        <p className="text-slate-600 dark:text-slate-400 text-lg mb-8">
          Sorry, we couldn&apos;t find the page you&apos;re looking for. The page might have been moved, deleted, or never existed.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/"
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
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
            Go to Homepage
          </Link>
          <button
            onClick={() => window.history.back()}
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
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            Go Back
          </button>
        </div>

        {/* Helpful Links */}
        <div className="mt-12 pt-8 border-t border-slate-200 dark:border-slate-700">
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            Here are some helpful links instead:
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <Link
              href="/tutors"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              Browse Tutors
            </Link>
            <span className="text-slate-300 dark:text-slate-600">•</span>
            <Link
              href="/bookings"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              My Bookings
            </Link>
            <span className="text-slate-300 dark:text-slate-600">•</span>
            <Link
              href="/dashboard"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              Dashboard
            </Link>
            <span className="text-slate-300 dark:text-slate-600">•</span>
            <Link
              href="/support"
              className="text-sm text-blue-600 hover:text-blue-800 hover:underline"
            >
              Help Center
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
