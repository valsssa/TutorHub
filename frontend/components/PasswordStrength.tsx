"use client";

import { useMemo } from "react";
import { Check, X, Info } from "lucide-react";
import clsx from "clsx";

interface PasswordStrengthProps {
  password: string;
  showRequirements?: boolean;
  className?: string;
}

interface PasswordRequirement {
  id: string;
  label: string;
  validator: (password: string) => boolean;
}

const PASSWORD_REQUIREMENTS: PasswordRequirement[] = [
  {
    id: "length",
    label: "At least 8 characters",
    validator: (p) => p.length >= 8,
  },
  {
    id: "uppercase",
    label: "One uppercase letter",
    validator: (p) => /[A-Z]/.test(p),
  },
  {
    id: "lowercase",
    label: "One lowercase letter",
    validator: (p) => /[a-z]/.test(p),
  },
  {
    id: "number",
    label: "One number",
    validator: (p) => /[0-9]/.test(p),
  },
  {
    id: "special",
    label: "One special character (!@#$%^&*)",
    validator: (p) => /[!@#$%^&*(),.?":{}|<>]/.test(p),
  },
];

function calculateStrength(password: string): {
  score: number;
  label: string;
  color: string;
  bgColor: string;
} {
  if (!password) {
    return { score: 0, label: "", color: "", bgColor: "bg-slate-200 dark:bg-slate-700" };
  }

  let score = 0;

  // Length scoring
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (password.length >= 16) score += 1;

  // Character type scoring
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/[0-9]/.test(password)) score += 1;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;

  // Penalty for common patterns
  if (/^[a-zA-Z]+$/.test(password)) score -= 1;
  if (/^[0-9]+$/.test(password)) score -= 2;
  if (/(.)\1{2,}/.test(password)) score -= 1; // Repeated characters

  // Normalize to 0-4 scale
  const normalizedScore = Math.max(0, Math.min(4, Math.floor(score / 2)));

  const strengths = [
    { label: "Very weak", color: "text-red-600 dark:text-red-400", bgColor: "bg-red-500" },
    { label: "Weak", color: "text-orange-600 dark:text-orange-400", bgColor: "bg-orange-500" },
    { label: "Fair", color: "text-amber-600 dark:text-amber-400", bgColor: "bg-amber-500" },
    { label: "Strong", color: "text-emerald-600 dark:text-emerald-400", bgColor: "bg-emerald-500" },
    { label: "Very strong", color: "text-emerald-600 dark:text-emerald-400", bgColor: "bg-emerald-600" },
  ];

  return {
    score: normalizedScore,
    ...strengths[normalizedScore],
  };
}

export default function PasswordStrength({
  password,
  showRequirements = true,
  className,
}: PasswordStrengthProps) {
  const strength = useMemo(() => calculateStrength(password), [password]);

  const requirementResults = useMemo(() => {
    return PASSWORD_REQUIREMENTS.map((req) => ({
      ...req,
      met: req.validator(password),
    }));
  }, [password]);

  const allRequirementsMet = requirementResults.every((r) => r.met);

  if (!password) {
    return null;
  }

  return (
    <div className={clsx("space-y-3", className)}>
      {/* Strength Meter */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-600 dark:text-slate-400">
            Password strength
          </span>
          <span className={clsx("text-sm font-medium", strength.color)}>
            {strength.label}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="flex gap-1">
          {[0, 1, 2, 3].map((index) => (
            <div
              key={index}
              className={clsx(
                "h-1.5 flex-1 rounded-full transition-all duration-300",
                index <= strength.score
                  ? strength.bgColor
                  : "bg-slate-200 dark:bg-slate-700"
              )}
            />
          ))}
        </div>
      </div>

      {/* Requirements Checklist */}
      {showRequirements && (
        <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Password requirements
            </span>
          </div>

          <ul className="space-y-2">
            {requirementResults.map((req) => (
              <li
                key={req.id}
                className={clsx(
                  "flex items-center gap-2 text-sm transition-colors",
                  req.met
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-slate-500 dark:text-slate-400"
                )}
              >
                {req.met ? (
                  <Check className="w-4 h-4 shrink-0" />
                ) : (
                  <X className="w-4 h-4 shrink-0 opacity-50" />
                )}
                <span className={req.met ? "line-through opacity-70" : ""}>
                  {req.label}
                </span>
              </li>
            ))}
          </ul>

          {allRequirementsMet && (
            <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700">
              <p className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">
                ✓ All requirements met
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Utility to check if password meets minimum requirements
export function isPasswordValid(password: string): boolean {
  return PASSWORD_REQUIREMENTS.every((req) => req.validator(password));
}

// Export requirements for use in forms
export { PASSWORD_REQUIREMENTS };
