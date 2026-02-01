"use client";

import React from "react";
import { Wallet, CalendarClock, TrendingUp, BookOpen, LucideIcon } from "lucide-react";

interface StudentStatsGridProps {
  balance: string;
  upcomingCount: number;
  monthlyCount: number;
  totalHours: string;
}

export default function StudentStatsGrid({
  balance,
  upcomingCount,
  monthlyCount,
  totalHours,
}: StudentStatsGridProps) {
  const stats = [
    { icon: Wallet, label: "Credits", value: `$${balance}`, helper: "Ready to spend" },
    { icon: CalendarClock, label: "Upcoming lessons", value: upcomingCount, helper: "next 7 days" },
    { icon: TrendingUp, label: "This month", value: monthlyCount, helper: "sessions booked" },
    { icon: BookOpen, label: "Hours scheduled", value: totalHours, helper: "all time" },
  ];

  return (
    <section className="mt-8 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <StatCard
          key={stat.label}
          icon={stat.icon}
          label={stat.label}
          value={stat.value}
          helper={stat.helper}
        />
      ))}
    </section>
  );
}

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  helper?: string;
}

function StatCard({ icon: Icon, label, value, helper }: StatCardProps) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200">
        <Icon size={18} />
      </div>
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {label}
        </p>
        <p className="text-lg font-bold text-slate-900 dark:text-white">{value}</p>
        {helper && <p className="text-xs text-slate-400 dark:text-slate-500">{helper}</p>}
      </div>
    </div>
  );
}
