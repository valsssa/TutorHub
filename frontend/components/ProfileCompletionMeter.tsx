"use client";

import { useMemo } from "react";
import { CheckCircle, Circle, ChevronRight } from "lucide-react";
import { TutorProfile } from "@/types";
import clsx from "clsx";

interface ProfileCompletionMeterProps {
  profile: TutorProfile;
  onNavigate?: (section: string) => void;
  compact?: boolean;
}

interface CompletionStep {
  id: string;
  label: string;
  description: string;
  isComplete: boolean;
  section: string;
}

export default function ProfileCompletionMeter({
  profile,
  onNavigate,
  compact = false,
}: ProfileCompletionMeterProps) {
  const steps = useMemo<CompletionStep[]>(() => [
    {
      id: "basic",
      label: "Basic Info",
      description: "Name, title, and bio",
      isComplete: Boolean(profile.title && profile.bio && profile.bio.length >= 50),
      section: "basic",
    },
    {
      id: "subjects",
      label: "Subjects",
      description: "At least one teaching subject",
      isComplete: Boolean(profile.subjects && profile.subjects.length > 0),
      section: "subjects",
    },
    {
      id: "availability",
      label: "Availability",
      description: "Set your weekly schedule",
      isComplete: Boolean(profile.availability && profile.availability.length > 0),
      section: "availability",
    },
    {
      id: "pricing",
      label: "Pricing",
      description: "Set your hourly rate",
      isComplete: Boolean(profile.hourly_rate_cents && profile.hourly_rate_cents > 0),
      section: "pricing",
    },
    {
      id: "photo",
      label: "Profile Photo",
      description: "Upload a professional photo",
      isComplete: Boolean(profile.avatar_url),
      section: "photo",
    },
    {
      id: "education",
      label: "Education",
      description: "Add your qualifications",
      isComplete: Boolean(profile.education && profile.education.length > 0),
      section: "education",
    },
  ], [profile]);

  const completedSteps = steps.filter((s) => s.isComplete).length;
  const totalSteps = steps.length;
  const percentage = Math.round((completedSteps / totalSteps) * 100);

  const nextIncompleteStep = steps.find((s) => !s.isComplete);

  if (compact) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Profile Completion
          </span>
          <span className={clsx(
            "text-sm font-bold",
            percentage === 100 ? "text-emerald-600 dark:text-emerald-400" : "text-slate-900 dark:text-white"
          )}>
            {percentage}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden mb-3">
          <div
            className={clsx(
              "h-full rounded-full transition-all duration-500",
              percentage === 100
                ? "bg-emerald-500"
                : percentage >= 75
                ? "bg-emerald-500"
                : percentage >= 50
                ? "bg-amber-500"
                : "bg-red-500"
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>

        {percentage < 100 && nextIncompleteStep && (
          <button
            onClick={() => onNavigate?.(nextIncompleteStep.section)}
            className="w-full flex items-center justify-between p-2 -mx-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors group"
          >
            <div className="flex items-center gap-2 text-sm">
              <Circle className="w-4 h-4 text-slate-400" />
              <span className="text-slate-600 dark:text-slate-400">
                Next: <span className="font-medium text-slate-900 dark:text-white">{nextIncompleteStep.label}</span>
              </span>
            </div>
            <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-500 transition-colors" />
          </button>
        )}

        {percentage === 100 && (
          <div className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
            <CheckCircle className="w-4 h-4" />
            <span>Profile complete!</span>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-lg text-slate-900 dark:text-white">
              Profile Completion
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Complete your profile to attract more students
            </p>
          </div>
          <div className={clsx(
            "w-14 h-14 rounded-full flex items-center justify-center text-lg font-bold",
            percentage === 100
              ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400"
              : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white"
          )}>
            {percentage}%
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4 h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
          <div
            className={clsx(
              "h-full rounded-full transition-all duration-500",
              percentage === 100
                ? "bg-emerald-500"
                : percentage >= 75
                ? "bg-emerald-500"
                : percentage >= 50
                ? "bg-amber-500"
                : "bg-red-500"
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>

      {/* Steps List */}
      <div className="divide-y divide-slate-100 dark:divide-slate-800">
        {steps.map((step) => (
          <button
            key={step.id}
            onClick={() => onNavigate?.(step.section)}
            disabled={step.isComplete}
            className={clsx(
              "w-full flex items-center gap-4 px-6 py-4 text-left transition-colors",
              step.isComplete
                ? "bg-emerald-50/50 dark:bg-emerald-900/10"
                : "hover:bg-slate-50 dark:hover:bg-slate-800"
            )}
          >
            <div className={clsx(
              "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
              step.isComplete
                ? "bg-emerald-100 dark:bg-emerald-900/30"
                : "bg-slate-100 dark:bg-slate-800"
            )}>
              {step.isComplete ? (
                <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              ) : (
                <Circle className="w-5 h-5 text-slate-400" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <p className={clsx(
                "font-medium",
                step.isComplete
                  ? "text-emerald-700 dark:text-emerald-300"
                  : "text-slate-900 dark:text-white"
              )}>
                {step.label}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400 truncate">
                {step.description}
              </p>
            </div>

            {!step.isComplete && (
              <ChevronRight className="w-5 h-5 text-slate-400" />
            )}
          </button>
        ))}
      </div>

      {/* Footer */}
      {percentage < 100 && (
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-800">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            <strong className="text-slate-900 dark:text-white">{completedSteps} of {totalSteps}</strong> steps completed.
            {" "}
            {percentage < 50 && "Complete more sections to appear in search results."}
            {percentage >= 50 && percentage < 100 && "You're almost there! Complete all sections for the best visibility."}
          </p>
        </div>
      )}

      {percentage === 100 && (
        <div className="px-6 py-4 bg-emerald-50 dark:bg-emerald-900/20 border-t border-emerald-200 dark:border-emerald-800">
          <div className="flex items-center gap-2 text-emerald-700 dark:text-emerald-300">
            <CheckCircle className="w-5 h-5" />
            <span className="font-medium">Your profile is complete and visible to students!</span>
          </div>
        </div>
      )}
    </div>
  );
}
