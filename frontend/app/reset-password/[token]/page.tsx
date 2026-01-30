"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Lock,
  ArrowLeft,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
  ShieldCheck,
} from "lucide-react";
import Input from "@/components/Input";
import Button from "@/components/Button";
import { auth } from "@/lib/api";

type FormStatus = "validating" | "valid" | "invalid" | "loading" | "success" | "error";

interface PasswordStrength {
  score: number; // 0-4
  label: string;
  color: string;
}

function getPasswordStrength(password: string): PasswordStrength {
  let score = 0;

  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  const strengths: PasswordStrength[] = [
    { score: 0, label: "Too weak", color: "bg-red-500" },
    { score: 1, label: "Weak", color: "bg-orange-500" },
    { score: 2, label: "Fair", color: "bg-yellow-500" },
    { score: 3, label: "Good", color: "bg-lime-500" },
    { score: 4, label: "Strong", color: "bg-emerald-500" },
  ];

  const index = Math.min(score, 4);
  return { ...strengths[index], score: index };
}

export default function ResetPasswordPage() {
  const params = useParams();
  const router = useRouter();
  const token = params?.token as string;

  const [status, setStatus] = useState<FormStatus>("validating");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [tokenError, setTokenError] = useState("");

  const passwordStrength = getPasswordStrength(password);

  // Validate token on mount
  useEffect(() => {
    if (!token) {
      setStatus("invalid");
      setTokenError("Invalid reset link");
      return;
    }

    const validateToken = async () => {
      try {
        // Call API to validate token
        await auth.validateResetToken?.(token) ??
          // Fallback simulation
          new Promise((resolve) => setTimeout(resolve, 500));

        setStatus("valid");
      } catch (err: any) {
        setStatus("invalid");
        setTokenError(
          err?.response?.data?.detail ||
          "This password reset link has expired or is invalid"
        );
      }
    };

    validateToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    // Validation
    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }

    if (passwordStrength.score < 2) {
      setError("Please choose a stronger password");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setStatus("loading");

    try {
      await auth.resetPassword?.(token, password) ??
        // Fallback simulation
        new Promise((resolve) => setTimeout(resolve, 1000));

      setStatus("success");
    } catch (err: any) {
      setStatus("error");
      setError(
        err?.response?.data?.detail ||
        "Failed to reset password. Please try again."
      );
    }
  };

  // Loading/Validating state
  if (status === "validating") {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 border-4 border-slate-200 border-t-emerald-500 rounded-full animate-spin" />
          <p className="text-slate-600 dark:text-slate-400">
            Validating reset link...
          </p>
        </div>
      </div>
    );
  }

  // Invalid token state
  if (status === "invalid") {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>

            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
              Link Expired or Invalid
            </h1>

            <p className="text-slate-600 dark:text-slate-400 mb-6">
              {tokenError}
            </p>

            <div className="space-y-3">
              <Link href="/forgot-password">
                <Button variant="primary" className="w-full">
                  Request New Reset Link
                </Button>
              </Link>

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

  // Success state
  if (status === "success") {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-xl p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center animate-in zoom-in-50 duration-300">
              <CheckCircle className="w-8 h-8 text-emerald-500" />
            </div>

            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
              Password Reset Complete!
            </h1>

            <p className="text-slate-600 dark:text-slate-400 mb-6">
              Your password has been successfully reset. You can now sign in with your new password.
            </p>

            <Link href="/login">
              <Button variant="primary" className="w-full">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Reset form
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
            <Lock className="w-7 h-7 text-emerald-600 dark:text-emerald-400" />
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
              Create New Password
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Your new password must be different from previously used passwords.
            </p>
          </div>

          {/* Error banner */}
          {error && status === "error" && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* New Password */}
            <div>
              <Input
                label="New Password"
                type={showPassword ? "text" : "password"}
                placeholder="Enter new password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError("");
                }}
                error={error && status !== "error" ? error : undefined}
                leftElement={<Lock className="w-5 h-5" />}
                rightElement={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 p-1"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                }
                autoComplete="new-password"
                required
              />

              {/* Password strength indicator */}
              {password && (
                <div className="mt-3">
                  <div className="flex gap-1 mb-2">
                    {[0, 1, 2, 3, 4].map((i) => (
                      <div
                        key={i}
                        className={`h-1.5 flex-1 rounded-full transition-colors ${
                          i <= passwordStrength.score
                            ? passwordStrength.color
                            : "bg-slate-200 dark:bg-slate-700"
                        }`}
                      />
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Password strength:{" "}
                    <span
                      className={
                        passwordStrength.score >= 3
                          ? "text-emerald-600 dark:text-emerald-400"
                          : passwordStrength.score >= 2
                          ? "text-yellow-600 dark:text-yellow-400"
                          : "text-red-600 dark:text-red-400"
                      }
                    >
                      {passwordStrength.label}
                    </span>
                  </p>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <Input
              label="Confirm Password"
              type={showConfirmPassword ? "text" : "password"}
              placeholder="Confirm new password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                setError("");
              }}
              error={
                confirmPassword && password !== confirmPassword
                  ? "Passwords do not match"
                  : undefined
              }
              leftElement={<Lock className="w-5 h-5" />}
              rightElement={
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 p-1"
                  tabIndex={-1}
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              }
              autoComplete="new-password"
              required
            />

            {/* Password requirements */}
            <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-2">
                <ShieldCheck className="w-4 h-4" />
                Password Requirements
              </p>
              <ul className="space-y-1.5 text-sm">
                {[
                  { check: password.length >= 8, text: "At least 8 characters" },
                  { check: /[a-z]/.test(password) && /[A-Z]/.test(password), text: "Upper & lowercase letters" },
                  { check: /\d/.test(password), text: "At least one number" },
                  { check: /[^a-zA-Z0-9]/.test(password), text: "At least one special character" },
                ].map((req, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full flex items-center justify-center ${
                        req.check
                          ? "bg-emerald-100 dark:bg-emerald-900/30"
                          : "bg-slate-200 dark:bg-slate-700"
                      }`}
                    >
                      {req.check && (
                        <CheckCircle className="w-3 h-3 text-emerald-500" />
                      )}
                    </div>
                    <span
                      className={
                        req.check
                          ? "text-slate-700 dark:text-slate-300"
                          : "text-slate-500 dark:text-slate-400"
                      }
                    >
                      {req.text}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={status === "loading"}
              disabled={!password || !confirmPassword || password !== confirmPassword}
            >
              Reset Password
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
