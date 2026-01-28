"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import { FiCheckCircle, FiClock, FiAlertCircle } from 'react-icons/fi';
import Button from '@/components/Button';
import ProtectedRoute from '@/components/ProtectedRoute';

export default function ProfileSubmittedPage() {
  return (
    <ProtectedRoute requiredRole="tutor">
      <ProfileSubmittedContent />
    </ProtectedRoute>
  );
}

function ProfileSubmittedContent() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4 transition-colors">
      <div className="max-w-2xl w-full bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8 border border-slate-200 dark:border-slate-800">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-emerald-100 dark:bg-emerald-900/30 rounded-full animate-ping opacity-75"></div>
              <div className="relative bg-emerald-500 p-4 rounded-full">
                <FiCheckCircle className="w-16 h-16 text-white" />
              </div>
            </div>
          </div>

          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
            Profile Submitted Successfully!
          </h1>

          {/* Timeline Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-300 text-sm font-semibold mb-4">
            <FiClock className="w-4 h-4" />
            Typical approval time: 24-48 hours
          </div>

          <p className="text-lg text-slate-600 dark:text-slate-400 mb-8">
            Your tutor profile has been submitted for review by our admin team.
          </p>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
            <div className="flex items-start gap-4 mb-4">
              <FiClock className="w-6 h-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="text-left">
                <h3 className="font-semibold text-blue-900 dark:text-blue-200 mb-2">
                  What happens next?
                </h3>
                <ul className="text-sm text-blue-800 dark:text-blue-300 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 dark:text-blue-400">•</span>
                    <span>Our team will review your profile, including your photo, description, and credentials</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 dark:text-blue-400">•</span>
                    <span>We verify all information for compliance with our community standards</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 dark:text-blue-400">•</span>
                    <span>You&apos;ll receive an email notification once your profile is approved or if changes are needed</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-6 mb-8">
            <div className="flex items-start gap-4">
              <FiAlertCircle className="w-6 h-6 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="text-left">
                <h3 className="font-semibold text-amber-900 dark:text-amber-200 mb-2">
                  While waiting for approval
                </h3>
                <p className="text-sm text-amber-800 dark:text-amber-300">
                  Your profile is marked as <strong>&quot;Under Review&quot;</strong> and won&apos;t be visible to students yet.
                  You can still access your dashboard and update your profile information if needed.
                </p>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              variant="primary"
              onClick={() => router.push('/dashboard')}
            >
              Go to Dashboard
            </Button>
            <Button
              variant="ghost"
              onClick={() => router.push('/tutor/profile/page')}
            >
              View My Profile
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
