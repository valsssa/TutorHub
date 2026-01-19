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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="absolute inset-0 bg-green-100 rounded-full animate-ping opacity-75"></div>
              <div className="relative bg-green-500 p-4 rounded-full">
                <FiCheckCircle className="w-16 h-16 text-white" />
              </div>
            </div>
          </div>

          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Profile Submitted Successfully!
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Your tutor profile has been submitted for review by our admin team.
          </p>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
            <div className="flex items-start gap-4 mb-4">
              <FiClock className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-left">
                <h3 className="font-semibold text-blue-900 mb-2">
                  What happens next?
                </h3>
                <ul className="text-sm text-blue-800 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span>Our team will review your profile, including your photo, description, and credentials</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span>We verify all information for compliance with our community standards</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span>You&apos;ll receive a notification once your profile is approved or if changes are needed</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600">•</span>
                    <span>Review typically takes 24-48 hours</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
            <div className="flex items-start gap-4">
              <FiAlertCircle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="text-left">
                <h3 className="font-semibold text-yellow-900 mb-2">
                  While waiting for approval
                </h3>
                <p className="text-sm text-yellow-800">
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
