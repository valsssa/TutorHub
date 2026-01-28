"use client";

import React from "react";
import {
  Sparkles,
  Search,
  Calendar,
  BadgeCheck,
  Wallet,
  CalendarClock,
  MessageSquare,
  ArrowRight,
} from "lucide-react";
import { BookingDTO } from "@/types/booking";

interface StudentHeroProps {
  name: string;
  balance: string;
  nextSession?: BookingDTO;
  onBookTutor: () => void;
  onViewBookings: () => void;
  onMessages: () => void;
  onTopUp: () => void;
  onEditProfile: () => void;
}

const actions = [
  {
    label: "Find a tutor",
    description: "Handpicked experts with live availability",
    icon: Search,
    key: "find-tutor",
  },
  {
    label: "My bookings",
    description: "Reschedule or cancel in one tap",
    icon: CalendarClock,
    key: "bookings",
  },
  {
    label: "Messages",
    description: "Chat with tutors before you book",
    icon: MessageSquare,
    key: "messages",
  },
  {
    label: "Learning profile",
    description: "Update goals, interests, and bio",
    icon: BadgeCheck,
    key: "profile",
  },
];

export default function StudentHero({
  name,
  balance,
  nextSession,
  onBookTutor,
  onViewBookings,
  onMessages,
  onTopUp,
  onEditProfile,
}: StudentHeroProps) {
  const actionHandlers: Record<string, () => void> = {
    "find-tutor": onBookTutor,
    bookings: onViewBookings,
    messages: onMessages,
    profile: onEditProfile,
  };

  return (
    <section className="grid gap-6 lg:grid-cols-3">
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-500 p-6 shadow-xl lg:col-span-2">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.18),transparent_35%)]" />
        <div className="relative flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white">
              <Sparkles size={14} /> Student Workspace
            </div>
            <h1 className="mt-4 text-3xl font-bold text-white md:text-4xl">
              Hey {name}, let&apos;s keep your learning streak alive.
            </h1>
            <p className="mt-2 max-w-xl text-sm text-emerald-50">
              Track your sessions, jump into class, and discover tutors who match your pace.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <button
                onClick={onBookTutor}
                className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold text-emerald-700 shadow-lg shadow-emerald-900/20 transition hover:-translate-y-0.5"
              >
                <Search size={16} /> Book a session
              </button>
              <button
                onClick={onViewBookings}
                className="inline-flex items-center gap-2 rounded-full border border-white/40 px-4 py-2 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                <Calendar size={16} /> View schedule
              </button>
            </div>
          </div>
          <div className="flex w-full flex-col gap-3 rounded-2xl bg-white/10 p-4 backdrop-blur md:max-w-xs">
            <div className="flex items-center justify-between text-sm text-emerald-50">
              <span>Available credits</span>
              <BadgeCheck size={16} />
            </div>
            <div className="text-3xl font-bold text-white">${balance}</div>
            <button
              onClick={onTopUp}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-white/90 px-3 py-2 text-sm font-semibold text-emerald-700 transition hover:bg-white"
            >
              <Wallet size={16} /> Top up wallet
            </button>
            <div className="flex items-center justify-between text-xs text-emerald-50/80">
              <span>Next lesson</span>
              <span>
                {nextSession
                  ? new Date(nextSession.start_at).toLocaleString([], {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })
                  : "Not scheduled"}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        {actions.map((action) => (
          <button
            key={action.key}
            onClick={actionHandlers[action.key]}
            className="group flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 transition group-hover:bg-emerald-600 group-hover:text-white dark:bg-emerald-900/40 dark:text-emerald-200">
              <action.icon size={18} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">{action.label}</p>
              <p className="text-xs text-slate-500 dark:text-slate-400">{action.description}</p>
            </div>
            <ArrowRight
              size={16}
              className="ml-auto text-slate-300 transition group-hover:translate-x-1 group-hover:text-emerald-500"
            />
          </button>
        ))}
      </div>
    </section>
  );
}
