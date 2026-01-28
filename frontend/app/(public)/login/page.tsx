"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FiMail, FiLock, FiBook, FiArrowRight } from "react-icons/fi";
import { auth } from "@/lib/api";
import { useToast } from "@/components/ToastContainer";
import { useFormValidation } from "@/hooks/useFormValidation";
import { useTimezone } from "@/contexts/TimezoneContext";
import { getBrowserTimezone } from "@/lib/timezone";
import Input from "@/components/Input";
import Button from "@/components/Button";
import TimezoneConfirmModal from "@/components/TimezoneConfirmModal";

interface LoginFormValues {
  email: string;
  password: string;
}

interface TimezoneCheckState {
  showModal: boolean;
  detectedTimezone: string;
  savedTimezone: string;
  pendingRoute: string;
}

export default function LoginPage() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const { setUserTimezone } = useTimezone();
  const [isLoading, setIsLoading] = useState(false);
  const [isUpdatingTimezone, setIsUpdatingTimezone] = useState(false);
  const [timezoneCheck, setTimezoneCheck] = useState<TimezoneCheckState>({
    showModal: false,
    detectedTimezone: "",
    savedTimezone: "",
    pendingRoute: "/dashboard",
  });

  const loginAndRoute = async (
    email: string,
    password: string,
    { showRoleToast = false }: { showRoleToast?: boolean } = {},
  ) => {
    setIsLoading(true);
    try {
      await auth.login(email, password);
      const user = await auth.getCurrentUser();

      if (showRoleToast) {
        showSuccess(`Logged in as ${user.role}`);
      }

      // Set user timezone in context
      if (user.timezone) {
        setUserTimezone(user.timezone);
      }

      // Determine route based on role
      const targetRoute = user.role === "admin" ? "/admin" : "/dashboard";

      // Check if browser timezone differs from saved timezone
      const browserTz = getBrowserTimezone();
      const savedTz = user.timezone || "UTC";

      if (browserTz !== savedTz) {
        // Show confirmation modal instead of routing immediately
        setTimezoneCheck({
          showModal: true,
          detectedTimezone: browserTz,
          savedTimezone: savedTz,
          pendingRoute: targetRoute,
        });
      } else {
        // Timezones match, route directly
        router.push(targetRoute);
      }
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      showError(
        err.response?.data?.detail ||
          "Login failed. Please check your credentials.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleTimezoneUpdate = async () => {
    setIsUpdatingTimezone(true);
    try {
      await auth.updatePreferences("", timezoneCheck.detectedTimezone);
      setUserTimezone(timezoneCheck.detectedTimezone);
      showSuccess("Timezone updated");
      router.push(timezoneCheck.pendingRoute);
    } catch (error) {
      showError("Failed to update timezone");
      // Still route even if update fails
      router.push(timezoneCheck.pendingRoute);
    } finally {
      setIsUpdatingTimezone(false);
      setTimezoneCheck((prev) => ({ ...prev, showModal: false }));
    }
  };

  const handleKeepTimezone = () => {
    setTimezoneCheck((prev) => ({ ...prev, showModal: false }));
    router.push(timezoneCheck.pendingRoute);
  };

  const { values, errors, touched, handleChange, handleBlur, handleSubmit } =
    useFormValidation<LoginFormValues>(
      {
        email: "",
        password: "",
      },
      {
        email: {
          required: "Email is required",
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: "Invalid email address",
          },
        },
        password: {
          required: "Password is required",
          minLength: {
            value: 6,
            message: "Password must be at least 6 characters",
          },
        },
      },
    );

  const onSubmit = async (formValues: LoginFormValues) => {
    await loginAndRoute(formValues.email, formValues.password);
  };

  const fillDemoCredentials = (email: string, password: string) => {
    handleChange("email", email);
    handleChange("password", password);
  };

  return (
    <>
      <TimezoneConfirmModal
        isOpen={timezoneCheck.showModal}
        detectedTimezone={timezoneCheck.detectedTimezone}
        savedTimezone={timezoneCheck.savedTimezone}
        onConfirmUpdate={handleTimezoneUpdate}
        onKeepCurrent={handleKeepTimezone}
        isLoading={isUpdatingTimezone}
      />
    <div className="flex-1 flex items-center justify-center bg-slate-50 dark:bg-slate-950 relative overflow-hidden transition-colors duration-200 py-12 min-h-screen">
      {/* Background Gradient Orbs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-emerald-600/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px]" />
      </div>

      <div className="w-full max-w-md px-4 z-10">
        {/* Login Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-2xl animate-fade-in">
          {/* Logo and Header */}
          <div className="text-center mb-8">
            <div className="w-12 h-12 bg-emerald-600 rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-900/20">
              <FiBook className="text-white w-6 h-6" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Welcome Back</h1>
            <p className="text-slate-500 dark:text-slate-400">Sign in to continue your learning journey</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Input
                type="email"
                label="Email Address"
                placeholder="name@example.com"
                value={values.email}
                onChange={(e) => handleChange("email", e.target.value)}
                onBlur={() => handleBlur("email")}
                error={touched.email ? errors.email : undefined}
              />
            </div>

            <div>
              <Input
                type="password"
                label="Password"
                placeholder="••••••••"
                value={values.password}
                onChange={(e) => handleChange("password", e.target.value)}
                onBlur={() => handleBlur("password")}
                error={touched.password ? errors.password : undefined}
              />
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-slate-500 dark:text-slate-400 cursor-pointer tap-target">
                <input
                  type="checkbox"
                  className="rounded bg-slate-200 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-emerald-500 focus:ring-0"
                />
                Remember me
              </label>
              <Link
                href="/help-center"
                className="text-emerald-500 hover:underline focus:outline-none tap-target"
              >
                Need help signing in?
              </Link>
            </div>

            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={isLoading}
            >
              Sign In <FiArrowRight className="w-4 h-4" />
            </Button>
          </form>

          {/* Sign Up Link */}
          <div className="text-center mt-6">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="text-emerald-600 dark:text-emerald-400 font-bold hover:underline"
              >
                Sign up
              </Link>
            </p>
          </div>

          {/* Quick Login Buttons - Development only */}
          {process.env.NODE_ENV === "development" && (
          <div className="mt-6">
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200 dark:border-slate-800"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400">
                  Or sign in with default account
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => loginAndRoute("admin@example.com", "admin123", { showRoleToast: true })}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-slate-900 dark:bg-slate-200 text-white dark:text-slate-900 border border-slate-900 dark:border-slate-200 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-300 transition-colors shadow-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Sign in as Admin</span>
              </button>
              <button
                type="button"
                onClick={() => loginAndRoute("tutor@example.com", "tutor123", { showRoleToast: true })}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-blue-600 dark:bg-blue-500 text-white border border-blue-600 dark:border-blue-500 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors shadow-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Sign in as Tutor</span>
              </button>
              <button
                type="button"
                onClick={() => loginAndRoute("student@example.com", "student123", { showRoleToast: true })}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-emerald-600 dark:bg-emerald-500 text-white border border-emerald-600 dark:border-emerald-500 rounded-lg hover:bg-emerald-700 dark:hover:bg-emerald-600 transition-colors shadow-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span>Sign in as Student</span>
              </button>
            </div>
          </div>
          )}

          {/* Demo Credentials */}
          {process.env.NODE_ENV === "development" && (
            <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-800">
              <p className="text-xs text-center text-slate-500 dark:text-slate-600 mb-3">Demo Credentials (Click to fill)</p>
              <div className="flex gap-2 justify-center flex-wrap">
                <button
                  type="button"
                  onClick={() => fillDemoCredentials("student@example.com", "student123")}
                  className="px-3 text-[10px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 py-2 rounded border border-slate-200 dark:border-slate-700 transition-colors"
                >
                  Student
                </button>
                <button
                  type="button"
                  onClick={() => fillDemoCredentials("tutor@example.com", "tutor123")}
                  className="px-3 text-[10px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 py-2 rounded border border-slate-200 dark:border-slate-700 transition-colors"
                >
                  Tutor
                </button>
                <button
                  type="button"
                  onClick={() => fillDemoCredentials("admin@example.com", "admin123")}
                  className="px-3 text-[10px] bg-slate-900 dark:bg-slate-200 text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-300 py-2 rounded border border-slate-900 dark:border-slate-200 transition-colors font-bold"
                >
                  Admin
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
    </>
  );
}
