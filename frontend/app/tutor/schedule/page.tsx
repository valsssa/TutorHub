"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  Settings,
  Plus,
  Calendar as CalendarIcon,
  Clock,
  XCircle,
  Trash2,
  Copy,
  ArrowLeft,
  X,
  Info,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useToast } from "@/components/ToastContainer";
import { tutors } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { useAuth } from "@/lib/hooks/useAuth";
import type { TutorProfile } from "@/types";

interface TimeSlot {
  start: string;
  end: string;
}

interface DaySchedule {
  day: string;
  enabled: boolean;
  slots: TimeSlot[];
}

const DAYS = [
  { id: 0, name: "Sunday", short: "Sun" },
  { id: 1, name: "Monday", short: "Mon" },
  { id: 2, name: "Tuesday", short: "Tue" },
  { id: 3, name: "Wednesday", short: "Wed" },
  { id: 4, name: "Thursday", short: "Thu" },
  { id: 5, name: "Friday", short: "Fri" },
  { id: 6, name: "Saturday", short: "Sat" },
];

export default function TutorSchedulePage() {
  return (
    <ProtectedRoute requiredRole="tutor">
      <ScheduleContent />
    </ProtectedRoute>
  );
}

function ScheduleContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const { user } = useAuth({ requiredRole: "tutor" });
  const [profile, setProfile] = useState<TutorProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [mode, setMode] = useState<"calendar" | "setup">("calendar");
  const [view, setView] = useState<"Day" | "Week">("Week");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [timezone, setTimezone] = useState("UTC");

  // Helper to get start of week (Monday)
  const getStartOfWeek = (d: Date) => {
    const date = new Date(d);
    const day = date.getDay();
    const diff = date.getDate() - day + (day === 0 ? -6 : 1);
    return new Date(date.setDate(diff));
  };

  // Generate days dynamically
  const days = useMemo(() => {
    if (view === "Day") {
      return [
        {
          name: currentDate.toLocaleDateString("en-US", { weekday: "long" }),
          date: currentDate.getDate(),
          fullDate: currentDate,
          isToday: currentDate.toDateString() === new Date().toDateString(),
        },
      ];
    }

    const start = getStartOfWeek(currentDate);
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(start);
      d.setDate(d.getDate() + i);
      return {
        name: d.toLocaleDateString("en-US", { weekday: "short" }),
        date: d.getDate(),
        fullDate: d,
        isToday: d.toDateString() === new Date().toDateString(),
      };
    });
  }, [currentDate, view]);

  const dateRangeString = useMemo(() => {
    if (view === "Day") {
      return currentDate.toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    }

    const start = getStartOfWeek(currentDate);
    const end = new Date(start);
    end.setDate(end.getDate() + 6);

    if (
      start.getMonth() === end.getMonth() &&
      start.getFullYear() === end.getFullYear()
    ) {
      return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${end.getDate()}, ${end.getFullYear()}`;
    }
    if (start.getFullYear() === end.getFullYear()) {
      return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} – ${end.toLocaleDateString("en-US", { month: "short", day: "numeric" })}, ${end.getFullYear()}`;
    }
    return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })} – ${end.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
  }, [currentDate, view]);

  // Weekly schedule state
  const [weeklySchedule, setWeeklySchedule] = useState<DaySchedule[]>([
    { day: "Monday", enabled: true, slots: [{ start: "09:00", end: "17:00" }] },
    { day: "Tuesday", enabled: true, slots: [{ start: "09:00", end: "17:00" }] },
    { day: "Wednesday", enabled: true, slots: [{ start: "09:00", end: "17:00" }] },
    { day: "Thursday", enabled: true, slots: [{ start: "09:00", end: "17:00" }] },
    { day: "Friday", enabled: true, slots: [{ start: "09:00", end: "15:00" }] },
    { day: "Saturday", enabled: false, slots: [{ start: "10:00", end: "14:00" }] },
    { day: "Sunday", enabled: false, slots: [{ start: "10:00", end: "14:00" }] },
  ]);

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      const profileData = await tutors.getMyProfile();
      setProfile(profileData);
      setTimezone(profileData.timezone || "UTC");

      // Convert availabilities to weekly schedule format
      const scheduleMap: Record<string, DaySchedule> = {
        Sunday: { day: "Sunday", enabled: false, slots: [] },
        Monday: { day: "Monday", enabled: false, slots: [] },
        Tuesday: { day: "Tuesday", enabled: false, slots: [] },
        Wednesday: { day: "Wednesday", enabled: false, slots: [] },
        Thursday: { day: "Thursday", enabled: false, slots: [] },
        Friday: { day: "Friday", enabled: false, slots: [] },
        Saturday: { day: "Saturday", enabled: false, slots: [] },
      };

      (profileData.availabilities || []).forEach((av) => {
        const dayName = DAYS[av.day_of_week].name;
        if (!scheduleMap[dayName].enabled) {
          scheduleMap[dayName].enabled = true;
          scheduleMap[dayName].slots = [];
        }
        scheduleMap[dayName].slots.push({
          start: av.start_time.slice(0, 5),
          end: av.end_time.slice(0, 5),
        });
      });

      setWeeklySchedule(Object.values(scheduleMap));
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      showError(err.response?.data?.detail || "Failed to load availability");
    } finally {
      setLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    if (user && authUtils.isTutor(user)) {
      loadProfile();
    }
  }, [user, loadProfile]);

  const handlePrev = () => {
    const newDate = new Date(currentDate);
    if (view === "Day") {
      newDate.setDate(newDate.getDate() - 1);
    } else {
      newDate.setDate(newDate.getDate() - 7);
    }
    setCurrentDate(newDate);
  };

  const handleNext = () => {
    const newDate = new Date(currentDate);
    if (view === "Day") {
      newDate.setDate(newDate.getDate() + 1);
    } else {
      newDate.setDate(newDate.getDate() + 7);
    }
    setCurrentDate(newDate);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
    setView("Day");
  };

  const toggleDay = (index: number) => {
    const newSchedule = [...weeklySchedule];
    newSchedule[index].enabled = !newSchedule[index].enabled;
    setWeeklySchedule(newSchedule);
  };

  const addSlot = (index: number) => {
    const newSchedule = [...weeklySchedule];
    newSchedule[index].slots.push({ start: "09:00", end: "17:00" });
    setWeeklySchedule(newSchedule);
  };

  const removeSlot = (dayIndex: number, slotIndex: number) => {
    const newSchedule = [...weeklySchedule];
    newSchedule[dayIndex].slots.splice(slotIndex, 1);
    setWeeklySchedule(newSchedule);
  };

  const updateSlot = (
    dayIndex: number,
    slotIndex: number,
    field: "start" | "end",
    value: string
  ) => {
    const newSchedule = [...weeklySchedule];
    newSchedule[dayIndex].slots[slotIndex][field] = value;
    setWeeklySchedule(newSchedule);
  };

  const copyToAll = (dayIndex: number) => {
    const sourceSlots = weeklySchedule[dayIndex].slots;
    const newSchedule = weeklySchedule.map((day) => ({
      ...day,
      enabled: true,
      slots: JSON.parse(JSON.stringify(sourceSlots)),
    }));
    setWeeklySchedule(newSchedule);
    showSuccess("Copied to all days");
  };

  const handleSave = async () => {
    if (!profile) {
      showError("Profile not loaded");
      return;
    }

    // Validate all slots
    for (const day of weeklySchedule) {
      if (day.enabled) {
        for (const slot of day.slots) {
          if (slot.start >= slot.end) {
            showError("End time must be after start time");
            return;
          }
        }
      }
    }

    setSaving(true);
    try {
      // Convert to API format
      const availabilityData = weeklySchedule.flatMap((day) => {
        if (!day.enabled) return [];
        const dayOfWeek = DAYS.findIndex((d) => d.name === day.day);
        return day.slots.map((slot) => ({
          day_of_week: dayOfWeek,
          start_time: slot.start,
          end_time: slot.end,
          is_recurring: true,
        }));
      });

      const updated = await tutors.replaceAvailability({
        availability: availabilityData,
        timezone,
        version: profile.version,
      });

      setProfile(updated);
      showSuccess("Availability updated successfully");
      setMode("calendar");
    } catch (error) {
      const err = error as {
        response?: { data?: { detail?: string }; status?: number };
      };
      if (err.response?.status === 409) {
        showError("Profile was updated by another session. Refreshing...");
        await loadProfile();
      } else {
        showError(
          err.response?.data?.detail || "Failed to update availability"
        );
      }
    } finally {
      setSaving(false);
    }
  };

  const hours = Array.from(
    { length: 24 },
    (_, i) => `${i.toString().padStart(2, "0")}:00`
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-100px)] lg:h-screen bg-white dark:bg-slate-900">
      {/* Left Sidebar */}
      <div className="w-full lg:w-64 bg-slate-50 dark:bg-slate-950 border-b lg:border-b-0 lg:border-r border-slate-200 dark:border-slate-800 p-4 lg:p-6 flex flex-col gap-4 lg:gap-6 flex-shrink-0 lg:overflow-y-auto">
        {/* Actions */}
        <div className="grid grid-cols-2 lg:grid-cols-1 gap-3">
          <button
            onClick={() => setMode("calendar")}
            className={`w-full py-2 lg:py-3 px-4 text-sm font-bold rounded-xl shadow-sm transition-all flex items-center justify-center gap-2 ${
              mode === "calendar"
                ? "bg-emerald-600 text-white shadow-emerald-500/20"
                : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
            }`}
          >
            <CalendarIcon size={18} /> <span className="hidden sm:inline">View</span> Calendar
          </button>
          <button
            onClick={() => setMode("setup")}
            className={`w-full py-2 lg:py-3 px-4 text-sm font-bold rounded-xl shadow-lg transition-all flex items-center justify-center gap-2 ${
              mode === "setup"
                ? "bg-emerald-600 text-white shadow-emerald-500/20"
                : "bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
            }`}
          >
            <Settings size={18} /> <span className="hidden sm:inline">Set up</span> Availability
          </button>
        </div>

        <div className="hidden lg:block h-px bg-slate-200 dark:bg-slate-800"></div>

        {/* Event Types Legend */}
        <div className="hidden lg:block">
          <h4 className="font-bold text-slate-900 dark:text-white mb-4 text-sm">
            Event types
          </h4>
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
              <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
              Trial lesson
            </div>
            <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
              <div className="w-3 h-3 rounded-full bg-pink-500"></div>
              Weekly lesson
            </div>
            <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              Single lesson
            </div>
            <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
              <div className="w-3 h-3 rounded-full bg-amber-600"></div>
              Time off
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-slate-900 overflow-hidden">
        {mode === "calendar" && (
          <>
            {/* Calendar Navigation */}
            <div className="px-4 py-3 flex flex-wrap justify-between items-center gap-3 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2 sm:gap-4 order-1 sm:order-1">
                <div className="flex items-center border border-slate-200 dark:border-slate-700 rounded-lg p-0.5 bg-white dark:bg-slate-800">
                  <button
                    onClick={handlePrev}
                    className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors"
                  >
                    <ChevronLeft size={18} className="text-slate-500" />
                  </button>
                  <button
                    onClick={handleNext}
                    className="p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded transition-colors"
                  >
                    <ChevronRight size={18} className="text-slate-500" />
                  </button>
                </div>
                <span className="text-sm sm:text-lg font-bold text-slate-900 dark:text-white whitespace-nowrap">
                  {dateRangeString}
                </span>
              </div>

              <div className="flex items-center gap-2 order-2 sm:order-2 ml-auto sm:ml-0">
                <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                  <button
                    onClick={handleToday}
                    className={`px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-all ${
                      view === "Day"
                        ? "bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white ring-2 ring-emerald-500/20"
                        : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                    }`}
                  >
                    Today
                  </button>
                  <button
                    onClick={() => setView("Week")}
                    className={`px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-all ${
                      view === "Week"
                        ? "bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white ring-2 ring-emerald-500/20"
                        : "text-slate-500 hover:text-slate-900 dark:hover:text-white"
                    }`}
                  >
                    Week
                  </button>
                </div>
                <button
                  onClick={() => router.back()}
                  className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  title="Close"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Calendar Grid */}
            <div className="flex-1 overflow-auto bg-white dark:bg-slate-900 relative">
              <div
                className={view === "Day" ? "w-full" : "min-w-[600px] md:min-w-[800px]"}
              >
                {/* Header Row */}
                <div
                  className={`grid ${
                    view === "Day"
                      ? "grid-cols-[50px_1fr]"
                      : `grid-cols-[60px_repeat(${days.length},1fr)]`
                  } border-b border-slate-200 dark:border-slate-800 sticky top-0 bg-white dark:bg-slate-900 z-30`}
                >
                  <div className="sticky left-0 z-40 bg-white dark:bg-slate-900 p-2 sm:p-4 text-[10px] sm:text-xs font-bold text-slate-400 border-r border-slate-100 dark:border-slate-800 text-center flex items-end justify-center pb-2">
                    GMT
                  </div>
                  {days.map((day, i) => (
                    <div
                      key={i}
                      className="p-2 sm:p-3 text-center border-r border-slate-100 dark:border-slate-800 last:border-r-0"
                    >
                      <div className="text-xs sm:text-sm font-medium text-slate-500 dark:text-slate-400 mb-1 uppercase">
                        {day.name}
                      </div>
                      <div
                        className={`text-sm sm:text-xl font-bold inline-block w-7 h-7 sm:w-8 sm:h-8 leading-7 sm:leading-8 rounded-lg ${
                          day.isToday
                            ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                            : "text-slate-900 dark:text-white"
                        }`}
                      >
                        {day.date}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Grid Body */}
                <div className="relative">
                  {hours.map((time, i) => (
                    <div
                      key={i}
                      className={`grid ${
                        view === "Day"
                          ? "grid-cols-[50px_1fr]"
                          : `grid-cols-[60px_repeat(${days.length},1fr)]`
                      } h-20 sm:h-24 border-b border-slate-100 dark:border-slate-800`}
                    >
                      {/* Time Label */}
                      <div className="sticky left-0 z-20 bg-white dark:bg-slate-900 text-[10px] sm:text-xs text-slate-400 text-right pr-2 sm:pr-3 pt-2 border-r border-slate-100 dark:border-slate-800">
                        <span className="-mt-3 block">{time}</span>
                      </div>

                      {/* Day Cells */}
                      {days.map((day, j) => (
                        <div
                          key={j}
                          className="border-r border-slate-100 dark:border-slate-800 last:border-r-0 relative group"
                        >
                          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-slate-50 dark:bg-slate-800/30 transition-opacity cursor-pointer"></div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {mode === "setup" && (
          <div className="flex flex-col h-full">
            {/* Header */}
            <div className="p-4 md:p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-start bg-white dark:bg-slate-900 sticky top-0 z-10">
              <div>
                <h2 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="p-1 bg-emerald-100 dark:bg-emerald-900/30 rounded text-emerald-600 dark:text-emerald-400">
                    <Clock size={18} />
                  </span>
                  Weekly Availability
                </h2>
                <p className="text-xs md:text-sm text-slate-500 mt-1">
                  Set your recurring weekly schedule.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setMode("calendar")}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                  title="Back to calendar"
                >
                  <ArrowLeft size={20} className="text-slate-400" />
                </button>
                <button
                  onClick={() => router.back()}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                  title="Close"
                >
                  <XCircle size={20} className="text-slate-400" />
                </button>
              </div>
            </div>

            {/* Timezone Selector */}
            <div className="px-4 md:px-6 pt-4 pb-2">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Timezone
              </label>
              <input
                type="text"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full max-w-md rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                placeholder="America/New_York"
              />
              <p className="text-sm text-slate-500 mt-1">
                Use a valid IANA timezone (e.g., America/New_York, Europe/London)
              </p>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4">
              {weeklySchedule.map((day, dayIndex) => (
                <div
                  key={day.day}
                  className={`p-4 rounded-xl border transition-all ${
                    day.enabled
                      ? "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 shadow-sm"
                      : "bg-slate-50 dark:bg-slate-900 border-transparent opacity-60"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                    {/* Header Row */}
                    <div className="flex items-center justify-between w-full sm:w-auto sm:min-w-[120px]">
                      <div className="flex items-center gap-3">
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            className="sr-only peer"
                            checked={day.enabled}
                            onChange={() => toggleDay(dayIndex)}
                          />
                          <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-500"></div>
                        </label>
                        <h3
                          className={`font-bold text-base ${
                            day.enabled
                              ? "text-slate-900 dark:text-white"
                              : "text-slate-500"
                          }`}
                        >
                          {day.day}
                        </h3>
                      </div>

                      {/* Mobile Actions */}
                      <div className="sm:hidden flex gap-1">
                        {day.enabled && (
                          <>
                            <button
                              onClick={() => addSlot(dayIndex)}
                              className="p-2 text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg"
                              title="Add time slot"
                            >
                              <Plus size={18} />
                            </button>
                            <button
                              onClick={() => copyToAll(dayIndex)}
                              className="p-2 text-slate-500 bg-slate-100 dark:bg-slate-800 rounded-lg"
                              title="Copy schedule to all days"
                            >
                              <Copy size={18} />
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Slots Area */}
                    <div className="flex-1 w-full pl-0 sm:pl-4 sm:border-l sm:border-slate-100 sm:dark:border-slate-800">
                      {/* Desktop Actions */}
                      <div className="hidden sm:flex justify-end gap-2 mb-3">
                        {day.enabled && (
                          <>
                            <button
                              onClick={() => addSlot(dayIndex)}
                              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-400 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors"
                            >
                              <Plus size={14} /> Add Slot
                            </button>
                            <button
                              onClick={() => copyToAll(dayIndex)}
                              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-slate-600 bg-slate-100 dark:bg-slate-800 dark:text-slate-400 rounded-lg hover:bg-slate-200 transition-colors"
                            >
                              <Copy size={14} /> Copy to All
                            </button>
                          </>
                        )}
                      </div>

                      {day.enabled ? (
                        <div className="space-y-3">
                          {day.slots.map((slot, slotIndex) => (
                            <div
                              key={slotIndex}
                              className="flex items-center gap-2"
                            >
                              <div className="flex-1 grid grid-cols-2 gap-2">
                                <input
                                  type="time"
                                  value={slot.start}
                                  onChange={(e) =>
                                    updateSlot(
                                      dayIndex,
                                      slotIndex,
                                      "start",
                                      e.target.value
                                    )
                                  }
                                  className="w-full px-3 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-center font-medium"
                                />
                                <input
                                  type="time"
                                  value={slot.end}
                                  onChange={(e) =>
                                    updateSlot(
                                      dayIndex,
                                      slotIndex,
                                      "end",
                                      e.target.value
                                    )
                                  }
                                  className="w-full px-3 py-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-center font-medium"
                                />
                              </div>
                              <button
                                onClick={() => removeSlot(dayIndex, slotIndex)}
                                className="p-2.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex-shrink-0"
                                title="Remove slot"
                              >
                                <Trash2 size={18} />
                              </button>
                            </div>
                          ))}
                          {day.slots.length === 0 && (
                            <div className="text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 px-4 py-3 rounded-lg border border-amber-100 dark:border-amber-800 flex items-center gap-2">
                              <Info size={16} /> No slots added. Add a slot to appear
                              available.
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="sm:h-full flex items-center">
                          <p className="text-sm text-slate-400 italic">
                            Marked as unavailable
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="p-4 md:p-6 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex justify-end gap-3 sticky bottom-0 z-20">
              <button
                onClick={() => setMode("calendar")}
                className="px-4 py-2 md:px-6 md:py-2.5 text-sm md:text-base text-slate-600 dark:text-slate-300 font-bold hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-6 py-2 md:px-8 md:py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm md:text-base font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
