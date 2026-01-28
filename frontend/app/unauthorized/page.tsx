"use client";

import Link from "next/link";
import { FiAlertCircle } from "react-icons/fi";
import Button from "@/components/Button";

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        <div className="bg-red-100 p-4 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
          <FiAlertCircle className="w-10 h-10 text-red-600" />
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-4">Access Denied</h1>

        <p className="text-gray-600 mb-8">
          You don&apos;t have permission to access this page. Please contact an
          administrator if you believe this is an error.
        </p>

        <div className="space-y-3">
          <Link href="/dashboard">
            <Button variant="primary" className="w-full">
              Go to Dashboard
            </Button>
          </Link>

          <Link href="/login">
            <Button variant="secondary" className="w-full">
              Back to Login
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
