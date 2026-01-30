"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle, XCircle, Loader2, Mail, ArrowRight } from "lucide-react";
import Button from "@/components/Button";
import { auth } from "@/lib/api";

type VerificationStatus = "loading" | "success" | "error" | "expired" | "already_verified";

export default function VerifyEmailPage() {
  const params = useParams();
  const router = useRouter();
  const token = params?.token as string;

  const [status, setStatus] = useState<VerificationStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  const verifyEmail = useCallback(async () => {
    if (!token) {
      setStatus("error");
      setError("Invalid verification link");
      return;
    }

    try {
      await auth.verifyEmail(token);
      setStatus("success");
    } catch (err: any) {
      const errorDetail = err?.response?.data?.detail || "";

      if (errorDetail.includes("expired")) {
        setStatus("expired");
        setError("This verification link has expired. Please request a new one.");
      } else if (errorDetail.includes("already") || errorDetail.includes("verified")) {
        setStatus("already_verified");
      } else {
        setStatus("error");
        setError(errorDetail || "Failed to verify email. The link may be invalid.");
      }
    }
  }, [token]);

  useEffect(() => {
    verifyEmail();
  }, [verifyEmail]);

  const handleResendVerification = async () => {
    setResendLoading(true);
    try {
      await auth.resendVerificationEmail();
      setResendSuccess(true);
    } catch {
      setError("Failed to send verification email. Please try again.");
    } finally {
      setResendLoading(false);
    }
  };

  const handleContinue = () => {
    router.push("/dashboard");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
          {/* Loading State */}
          {status === "loading" && (
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
                <Loader2 className="w-8 h-8 text-emerald-600 dark:text-emerald-400 animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Verifying your email
              </h1>
              <p className="text-slate-500 dark:text-slate-400">
                Please wait while we verify your email address...
              </p>
            </div>
          )}

          {/* Success State */}
          {status === "success" && (
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Email verified!
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mb-8">
                Your email has been successfully verified. You can now access all features.
              </p>
              <Button onClick={handleContinue} size="lg" className="w-full">
                Continue to Dashboard
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}

          {/* Already Verified State */}
          {status === "already_verified" && (
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Already verified
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mb-8">
                Your email address has already been verified. You're all set!
              </p>
              <Button onClick={handleContinue} size="lg" className="w-full">
                Go to Dashboard
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}

          {/* Expired State */}
          {status === "expired" && (
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-amber-100 dark:bg-amber-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
                <Mail className="w-8 h-8 text-amber-600 dark:text-amber-400" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Link expired
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mb-6">
                {error}
              </p>

              {resendSuccess ? (
                <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-xl p-4 mb-6">
                  <p className="text-emerald-700 dark:text-emerald-300 text-sm">
                    A new verification email has been sent. Please check your inbox.
                  </p>
                </div>
              ) : (
                <Button
                  onClick={handleResendVerification}
                  isLoading={resendLoading}
                  size="lg"
                  className="w-full mb-4"
                >
                  <Mail className="w-4 h-4 mr-2" />
                  Resend verification email
                </Button>
              )}

              <Link
                href="/login"
                className="text-sm text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 font-medium"
              >
                Back to login
              </Link>
            </div>
          )}

          {/* Error State */}
          {status === "error" && (
            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-6">
                <XCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Verification failed
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mb-6">
                {error}
              </p>

              <div className="space-y-3">
                <Button
                  onClick={handleResendVerification}
                  isLoading={resendLoading}
                  variant="secondary"
                  size="lg"
                  className="w-full"
                >
                  <Mail className="w-4 h-4 mr-2" />
                  Request new verification link
                </Button>

                <Link href="/login">
                  <Button variant="ghost" size="lg" className="w-full">
                    Back to login
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-6">
          Having trouble?{" "}
          <Link
            href="/help"
            className="text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 font-medium"
          >
            Contact support
          </Link>
        </p>
      </div>
    </div>
  );
}
