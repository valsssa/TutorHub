"use client";

import React from "react";
import { Calendar, CalendarClock, Clock, Video } from "lucide-react";
import { BookingDTO } from "@/types/booking";

interface StudentSessionsListProps {
  sessions: BookingDTO[];
  isJoinable: (startAt: string) => boolean;
  onJoin: (booking: BookingDTO) => void;
  onReview: (bookingId: number) => void;
  onManageAll?: () => void;
}

function getSubjectIcon(subjectName?: string | null): string {
  if (!subjectName) return "📚";
  const lower = subjectName.toLowerCase();
  if (lower.includes("math")) return "∫";
  if (lower.includes("physics")) return "⚛";
  if (lower.includes("chemistry")) return "🧪";
  if (lower.includes("programming") || lower.includes("code") || lower.includes("computer"))
    return "💻";
  if (lower.includes("english") || lower.includes("language")) return "📝";
  if (lower.includes("music")) return "🎵";
  if (lower.includes("art")) return "🎨";
  if (lower.includes("history")) return "📜";
  if (lower.includes("biology")) return "🧬";
  return "📚";
}

function getStatusMeta(status: string): { label: string; className: string } {
  const normalized = status.toLowerCase();
  if (normalized === "confirmed") {
    return { label: "Confirmed", className: "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-200" };
  }
  if (normalized === "pending") {
    return { label: "Pending", className: "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-200" };
  }
  if (normalized.includes("cancelled") || normalized === "cancelled") {
    return { label: "Cancelled", className: "bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-200" };
  }
  if (normalized === "completed") {
    return { label: "Completed", className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200" };
  }
  return { label: status, className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200" };
}

export default function StudentSessionsList({
  sessions,
  isJoinable,
  onJoin,
  onReview,
  onManageAll,
}: StudentSessionsListProps) {
  return (
    <div>
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-slate-900 dark:text-white">
          <Calendar size={20} /> Your Sessions
        </h2>
        {onManageAll && (
          <button
            onClick={onManageAll}
            className="text-sm font-semibold text-emerald-600 hover:text-emerald-500 dark:text-emerald-300"
          >
            Manage all
          </button>
        )}
      </div>

      <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {sessions.length === 0 ? (
          <div className="p-10 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
              <Calendar className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              No sessions yet
            </h3>
            <p className="text-slate-500 dark:text-slate-400 mb-6 max-w-sm mx-auto">
              Book your first lesson with a tutor to start your learning journey.
            </p>
            {onManageAll && (
              <button
                onClick={onManageAll}
                className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white font-semibold rounded-lg hover:bg-emerald-500 transition-colors"
              >
                Find a Tutor
              </button>
            )}
          </div>
        ) : (
          sessions.map((booking, idx) => {
            const meta = getStatusMeta(booking.status);
            const normalized = booking.status.toLowerCase();
            const canJoin =
              (normalized === "confirmed" || normalized === "pending") &&
              isJoinable(booking.start_at) &&
              Boolean(booking.join_url);

            return (
              <div
                key={booking.id}
                className={`flex flex-col gap-4 border-b border-slate-200 px-5 py-4 last:border-none dark:border-slate-800 md:flex-row md:items-center md:justify-between ${
                  idx === 0 ? "bg-emerald-50/40 dark:bg-emerald-900/10" : ""
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-lg dark:bg-slate-800">
                    {getSubjectIcon(booking.subject_name)}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                      {booking.subject_name || booking.topic || "Session"} with {booking.tutor.name}
                    </p>
                    <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                      <span className="inline-flex items-center gap-1">
                        <CalendarClock size={14} />
                        {new Date(booking.start_at).toLocaleDateString(undefined, {
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock size={14} />
                        {new Date(booking.start_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                      <span className={`inline-flex items-center gap-2 rounded-full px-2 py-1 text-xs font-semibold ${meta.className}`}>
                        {meta.label}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-2 md:items-end">
                  {canJoin ? (
                    <button
                      onClick={() => onJoin(booking)}
                      className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-[0_10px_40px_-20px_rgba(16,185,129,0.9)] transition hover:-translate-y-0.5 hover:bg-emerald-500"
                    >
                      <Video size={18} /> Join classroom
                    </button>
                  ) : normalized === "completed" ? (
                    <button
                      onClick={() => onReview(booking.id)}
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-emerald-200 px-4 py-2 text-sm font-semibold text-emerald-700 transition hover:border-emerald-400 hover:text-emerald-600 dark:border-emerald-900/40 dark:text-emerald-200 dark:hover:border-emerald-600"
                    >
                      Rate & review
                    </button>
                  ) : (
                    <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">
                      {meta.label}
                    </span>
                  )}
                  <span className="text-xs text-slate-400 dark:text-slate-500">
                    Created {new Date(booking.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
