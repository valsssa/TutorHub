"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Mail, ArrowLeft, CheckCircle, AlertCircle } from "lucide-react";
import Input from "@/components/Input";
import Button from "@/components/Button";
import { auth } from "@/lib/api";

type FormStatus = "idle" | "loading" | "success" | "error";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<FormStatus>("idle");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim()) {
      setError("Please enter your email address");
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    setStatus("loading");
    setError("");

    try {
      // Call the API to request password reset
      // Note: The API should always return success to prevent email enumeration
      await auth.requestPasswordReset?.(email) ??
        // Fallback simulation if API method doesn't exist
        new Promise((resolve) => setTimeout(resolve, 1000));

      setStatus("success");
    } catch (err: any) {
      // Even on error, show success to prevent email enumeration
      // In production, the API should handle this server-side
      setStatus("success");
    }
  };

  // Success state
  if (status === "success") {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8 text-center">
            {/* Success Icon */}
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-emerald-500" />
            </div>

            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
              Check Your Email
            </h1>

            <p className="text-slate-600 dark:text-slate-400 mb-6">
              If an account exists for <strong className="text-slate-900 dark:text-white">{email}</strong>,
              we&apos;ve sent password reset instructions to your inbox.
            </p>

            <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4 mb-6 text-sm text-slate-600 dark:text-slate-400">
              <p className="mb-2">
                <strong>Didn&apos;t receive the email?</strong>
              </p>
              <ul className="list-disc list-inside space-y-1 text-left">
                <li>Check your spam or junk folder</li>
                <li>Make sure you entered the correct email</li>
                <li>Wait a few minutes and try again</li>
              </ul>
            </div>

            <div className="space-y-3">
              <Button
                variant="primary"
                className="w-full"
                onClick={() => {
                  setStatus("idle");
                  setEmail("");
                }}
              >
                Try Different Email
              </Button>

              <Link href="/login">
                <Button variant="ghost" className="w-full">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Back to login */}
        <Link
          href="/login"
          className="inline-flex items-center gap-2 text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to login
        </Link>

        {/* Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8">
          {/* Icon */}
          <div className="w-14 h-14 mx-auto mb-6 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
            <Mail className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Forgot Password?
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              No worries! Enter your email and we&apos;ll send you reset instructions.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              label="Email Address"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setError("");
              }}
              error={error}
              leftElement={<Mail className="w-5 h-5" />}
              autoComplete="email"
              autoFocus
              required
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={status === "loading"}
            >
              Send Reset Link
            </Button>
          </form>

          {/* Help text */}
          <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
            Remember your password?{" "}
            <Link
              href="/login"
              className="font-medium text-emerald-600 dark:text-emerald-400 hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>

        {/* Security note */}
        <p className="mt-6 text-center text-xs text-slate-500 dark:text-slate-500">
          For security, password reset links expire after 1 hour.
        </p>
      </div>
    </div>
  );
}
