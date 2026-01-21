"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { FiBook, FiCheck, FiArrowRight, FiArrowLeft, FiUser } from "react-icons/fi";
import { auth } from "@/lib/api";
import { detectLocalePreferences } from "@/lib/locale-detection";
import { useToast } from "@/components/ToastContainer";
import { useFormValidation } from "@/hooks/useFormValidation";
import Input from "@/components/Input";
import Button from "@/components/Button";

interface RegisterFormValues {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  isTutor: boolean;
}

export default function RegisterPage() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [detectedPrefs, setDetectedPrefs] = useState({ currency: "USD", timezone: "UTC" });

  // Detect user's locale on mount
  useEffect(() => {
    const prefs = detectLocalePreferences();
    setDetectedPrefs({ currency: prefs.currency, timezone: prefs.timezone });
  }, []);

  const { values, errors, touched, handleChange, handleBlur, handleSubmit } =
    useFormValidation<RegisterFormValues>(
      {
        firstName: "",
        lastName: "",
        email: "",
        password: "",
        confirmPassword: "",
        isTutor: false,
      },
      {
        firstName: {
          required: "First name is required",
          minLength: {
            value: 1,
            message: "First name is required",
          },
          maxLength: {
            value: 100,
            message: "First name must not exceed 100 characters",
          },
        },
        lastName: {
          required: "Last name is required",
          minLength: {
            value: 1,
            message: "Last name is required",
          },
          maxLength: {
            value: 100,
            message: "Last name must not exceed 100 characters",
          },
        },
        email: {
          required: "Email is required",
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: "Invalid email address",
          },
          maxLength: {
            value: 254,
            message: "Email must not exceed 254 characters",
          },
        },
        password: {
          required: "Password is required",
          minLength: {
            value: 6,
            message: "Password must be at least 6 characters",
          },
          maxLength: {
            value: 128,
            message: "Password must not exceed 128 characters",
          },
        },
        confirmPassword: {
          required: "Please confirm your password",
          validate: (value) => {
            if (value !== values.password) {
              return "Passwords do not match";
            }
            return true;
          },
        },
      },
    );

  const onSubmit = async (formValues: RegisterFormValues) => {
    setIsLoading(true);

    try {
      const user = await auth.register(
        formValues.email,
        formValues.password,
        formValues.firstName,
        formValues.lastName,
        formValues.isTutor ? "tutor" : "student",
        detectedPrefs.timezone,
        detectedPrefs.currency
      );

      if (formValues.isTutor) {
        await auth.login(formValues.email, formValues.password);
        showSuccess("Registration successful! Complete your tutor profile.");
        setTimeout(() => router.push("/tutor/onboarding"), 100);
      } else {
        showSuccess("Registration successful! Please log in.");
        setTimeout(() => router.push("/login"), 100);
      }
    } catch (error: unknown) {
      const axiosError = error as {
        response?: { data?: { detail?: unknown } };
        message?: string;
      };

      const detail = axiosError.response?.data?.detail;
      let errorMessage: string | undefined;

      if (typeof detail === "string") {
        errorMessage = detail;
      } else if (Array.isArray(detail)) {
        errorMessage = detail
          .map((item) => {
            if (typeof item === "string") {
              return item;
            }
            if (item && typeof item === "object" && "msg" in item) {
              return String(item.msg);
            }
            return JSON.stringify(item);
          })
          .join(", ");
      } else if (detail && typeof detail === "object") {
        errorMessage = JSON.stringify(detail);
      }

      if (!errorMessage) {
        errorMessage = axiosError.message || "Registration failed. Please try again.";
      }

      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center bg-slate-50 dark:bg-slate-950 relative overflow-hidden transition-colors duration-200 py-12 min-h-screen">
      {/* Background Gradient Orbs */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] right-[-5%] w-[500px] h-[500px] bg-emerald-600/10 rounded-full blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[-5%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[100px]" />
      </div>

      <div className="w-full max-w-md px-4 z-10">
        {/* Registration Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-8 shadow-2xl animate-fade-in">
          {/* Back to Login */}
          <Link
            href="/login"
            className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 text-sm mb-6 transition-colors"
          >
            <FiArrowLeft className="w-4 h-4" /> Back to Login
          </Link>

          {/* Logo and Header */}
          <div className="text-center mb-6">
            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center mx-auto mb-4 text-emerald-600 dark:text-emerald-400">
              <FiUser className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Create Account</h2>
            <p className="text-slate-500 dark:text-slate-400">Join EduConnect today</p>
          </div>

          {/* Role Selection */}
          <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg mb-6">
            <button
              type="button"
              onClick={() => handleChange("isTutor", false)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                !values.isTutor
                  ? 'bg-white dark:bg-slate-700 shadow text-emerald-600 dark:text-emerald-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Student
            </button>
            <button
              type="button"
              onClick={() => handleChange("isTutor", true)}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                values.isTutor
                  ? 'bg-white dark:bg-slate-700 shadow text-emerald-600 dark:text-emerald-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Tutor
            </button>
          </div>

          {/* Registration Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                type="text"
                label="First Name"
                placeholder="John"
                value={values.firstName}
                onChange={(e) => handleChange("firstName", e.target.value)}
                onBlur={() => handleBlur("firstName")}
                error={touched.firstName ? errors.firstName : undefined}
              />
              <Input
                type="text"
                label="Last Name"
                placeholder="Doe"
                value={values.lastName}
                onChange={(e) => handleChange("lastName", e.target.value)}
                onBlur={() => handleBlur("lastName")}
                error={touched.lastName ? errors.lastName : undefined}
              />
            </div>

            <Input
              type="email"
              label="Email Address"
              placeholder="name@example.com"
              value={values.email}
              onChange={(e) => handleChange("email", e.target.value)}
              onBlur={() => handleBlur("email")}
              error={touched.email ? errors.email : undefined}
            />

            <Input
              type="password"
              label="Password"
              placeholder="Create a password"
              value={values.password}
              onChange={(e) => handleChange("password", e.target.value)}
              onBlur={() => handleBlur("password")}
              error={touched.password ? errors.password : undefined}
              helperText={!touched.password && !errors.password ? "6-128 characters" : undefined}
            />

            <Input
              type="password"
              label="Confirm Password"
              placeholder="Confirm your password"
              value={values.confirmPassword}
              onChange={(e) => handleChange("confirmPassword", e.target.value)}
              onBlur={() => handleBlur("confirmPassword")}
              error={touched.confirmPassword ? errors.confirmPassword : undefined}
            />

            {/* Role Info */}
            {values.isTutor ? (
              <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <FiCheck className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-emerald-800 dark:text-emerald-300">
                    You&apos;ll complete your <strong>Tutor Profile</strong> after registration.
                    Your profile will be reviewed before going live.
                  </p>
                </div>
              </div>
            ) : (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <FiCheck className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-blue-800 dark:text-blue-300">
                    Creating a <strong>Student</strong> account. You can browse and book tutors.
                  </p>
                </div>
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              className="w-full mt-2"
              isLoading={isLoading}
            >
              Sign Up <FiArrowRight className="w-4 h-4" />
            </Button>
          </form>

          {/* Sign In Link */}
          <div className="text-center mt-6">
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Already have an account?{" "}
              <Link
                href="/login"
                className="text-emerald-600 dark:text-emerald-400 font-bold hover:underline"
              >
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}