"use client";

import React from "react";
import { Calendar, CalendarClock, Heart, Video, ArrowRight } from "lucide-react";
import { BookingDTO } from "@/types/booking";
import { TutorPublicSummary } from "@/types";

interface StudentSavedTutorsPanelProps {
  loading: boolean;
  savedTutors: TutorPublicSummary[];
  nextSession?: BookingDTO;
  isJoinable: (startAt: string) => boolean;
  onJoin: (booking: BookingDTO) => void;
  onViewProfile: (tutor: TutorPublicSummary) => void;
  onViewAll: () => void;
  onBookNow: () => void;
}

export default function StudentSavedTutorsPanel({
  loading,
  savedTutors,
  nextSession,
  isJoinable,
  onJoin,
  onViewProfile,
  onViewAll,
  onBookNow,
}: StudentSavedTutorsPanelProps) {
  return (
    <aside className="space-y-4">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Next session</h3>
          <CalendarClock size={18} className="text-emerald-500" />
        </div>
        {nextSession ? (
          <div className="mt-3 space-y-2">
            <p className="text-base font-semibold text-slate-900 dark:text-white">
              {nextSession.subject_name || nextSession.topic || "Upcoming lesson"}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">with {nextSession.tutor.name}</p>
            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
              <Calendar size={16} />
              {new Date(nextSession.start_at).toLocaleString([], {
                weekday: "short",
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </div>
            <button
              onClick={() => onJoin(nextSession)}
              disabled={!isJoinable(nextSession.start_at) || !nextSession.join_url}
              className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition enabled:hover:-translate-y-0.5 enabled:hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-emerald-800/60"
            >
              <Video size={18} /> {isJoinable(nextSession.start_at) ? "Join classroom" : "Join opens 15 mins before"}
            </button>
          </div>
        ) : (
          <div className="mt-3 rounded-xl bg-slate-100 p-4 text-sm text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            Nothing scheduled yet. Book a lesson to see it here.
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Saved tutors</h3>
          <Heart size={18} className="text-emerald-500" />
        </div>
        {loading ? (
          <div className="mt-3 space-y-2 text-sm text-slate-500 dark:text-slate-400">Loading your tutors...</div>
        ) : savedTutors.length === 0 ? (
          <div className="mt-3 rounded-xl bg-slate-100 p-4 text-sm text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            Save tutors you like to jump back in faster.
            <button
              onClick={onBookNow}
              className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-emerald-600 hover:text-emerald-500 dark:text-emerald-300"
            >
              Browse tutors
              <ArrowRight size={14} />
            </button>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {savedTutors.slice(0, 3).map((tutor) => (
              <button
                key={tutor.id}
                onClick={() => onViewProfile(tutor)}
                className="group flex w-full items-center justify-between gap-3 rounded-xl border border-slate-200 px-3 py-3 text-left transition hover:border-emerald-200 hover:bg-emerald-50 dark:border-slate-800 dark:hover:border-emerald-700/40 dark:hover:bg-emerald-900/10"
              >
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">
                    {tutor.name || `${tutor.first_name ?? ""} ${tutor.last_name ?? ""}`.trim()}
                  </span>
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {tutor.subjects?.slice(0, 2).join(" • ") || "Multidisciplinary"}
                  </span>
                </div>
                <ArrowRight
                  size={16}
                  className="text-slate-400 transition group-hover:translate-x-1 group-hover:text-emerald-500"
                />
              </button>
            ))}
            {savedTutors.length > 3 && (
              <button
                onClick={onViewAll}
                className="text-xs font-semibold text-emerald-600 hover:text-emerald-500 dark:text-emerald-300"
              >
                View all saved tutors
              </button>
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
