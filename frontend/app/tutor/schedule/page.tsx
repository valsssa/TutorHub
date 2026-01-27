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
  Link as LinkIcon,
  Check,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useToast } from "@/components/ToastContainer";
import { tutors, bookings } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { useAuth } from "@/lib/hooks/useAuth";
import type { TutorProfile } from "@/types";
import type { BookingDTO } from "@/types/booking";

interface TimeSlot {
  start: string;
  end: string;
}

interface DaySchedule {
  day: string;
  enabled: boolean;
  slots: TimeSlot[];
}

interface CalendarEvent {
  id: number;
  title: string;
  start: Date;
  end: Date;
  type: "trial" | "weekly" | "single" | "timeoff" | "event";
  status?: string;
  subject?: string;
  studentName?: string;
  booking?: BookingDTO;
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
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [isEventModalOpen, setIsEventModalOpen] = useState(false);

  // Google Calendar integration state
  const [isCalendarConnected, setIsCalendarConnected] = useState(false);
  const [showConnectBanner, setShowConnectBanner] = useState(true);
  const [isSyncModalOpen, setIsSyncModalOpen] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

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

  const loadBookings = useCallback(async () => {
    try {
      const startOfWeek = getStartOfWeek(currentDate);
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(endOfWeek.getDate() + 7);

      const response = await bookings.list({
        role: "tutor",
        status: "upcoming",
        page_size: 100,
      });

      const events: CalendarEvent[] = response.bookings
        .filter((booking) => {
          const startTime = new Date(booking.start_at);
          return startTime >= startOfWeek && startTime < endOfWeek;
        })
        .map((booking) => {
          const startTime = new Date(booking.start_at);
          const endTime = new Date(booking.end_at);
          
          // Determine event type based on lesson_type
          let eventType: "trial" | "weekly" | "single" = "single";
          if (booking.lesson_type === "TRIAL") {
            eventType = "trial";
          } else if (booking.lesson_type === "PACKAGE") {
            eventType = "weekly";
          }

          return {
            id: booking.id,
            title: booking.student?.name || "Student",
            start: startTime,
            end: endTime,
            type: eventType,
            status: booking.status.toLowerCase(),
            subject: booking.subject_name || undefined,
            studentName: booking.student?.name,
            booking,
          };
        });

      setCalendarEvents(events);
    } catch (error) {
      console.error("Failed to load bookings:", error);
    }
  }, [currentDate]);

  useEffect(() => {
    if (user && authUtils.isTutor(user)) {
      loadProfile();
    }
  }, [user, loadProfile]);

  useEffect(() => {
    if (mode === "calendar" && user && authUtils.isTutor(user)) {
      loadBookings();
    }
  }, [mode, currentDate, user, loadBookings]);

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

  const handleConnectCalendar = () => {
    setIsConnecting(true);
    setTimeout(() => {
      setIsCalendarConnected(true);
      setIsConnecting(false);
      setIsSyncModalOpen(false);
      showSuccess("Google Calendar connected successfully");
    }, 1500);
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

  // Get events for a specific day and time slot
  const getEventsForSlot = (day: typeof days[0], hour: string) => {
    return calendarEvents.filter((event) => {
      const eventDay = event.start.getDay();
      // Map day name to day index (Sunday=0, Monday=1, etc.)
      const dayIndex = DAYS.findIndex(
        (d) => d.name === day.name || d.short === day.name
      );
      const eventHour = event.start.getHours();
      const slotHour = parseInt(hour.split(":")[0]);

      // Check if event is on this day
      // Handle both full name and short name matching
      const eventDayName = event.start.toLocaleDateString("en-US", {
        weekday: "short",
      });
      const isSameDay =
        dayIndex === eventDay ||
        day.name === event.start.toLocaleDateString("en-US", { weekday: "long" }) ||
        day.name === eventDayName ||
        day.fullDate?.toDateString() === event.start.toDateString();

      if (!isSameDay) return false;

      // Check if event starts in this hour slot
      return eventHour === slotHour;
    });
  };

  // Get event color based on type
  const getEventColor = (type: CalendarEvent["type"], status?: string) => {
    if (status === "pending") {
      return {
        bg: "bg-amber-50 dark:bg-amber-900/20",
        border: "border-amber-500",
      };
    }
    switch (type) {
      case "trial":
        return {
          bg: "bg-emerald-50 dark:bg-emerald-900/20",
          border: "border-emerald-500",
        };
      case "weekly":
        return {
          bg: "bg-pink-50 dark:bg-pink-900/20",
          border: "border-pink-500",
        };
      case "single":
        return {
          bg: "bg-blue-50 dark:bg-blue-900/20",
          border: "border-blue-500",
        };
      case "timeoff":
        return {
          bg: "bg-slate-100 dark:bg-slate-800",
          border: "border-amber-600",
        };
      case "event":
        return {
          bg: "bg-slate-100 dark:bg-slate-800",
          border: "border-indigo-500",
        };
      default:
        return {
          bg: "bg-slate-100 dark:bg-slate-800",
          border: "border-slate-500",
        };
    }
  };

  const handleEventClick = (event: CalendarEvent) => {
    setSelectedEvent(event);
    setIsEventModalOpen(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row h-[calc(100vh-100px)] lg:h-[700px] -m-4 md:-m-6 bg-white dark:bg-slate-900 rounded-2xl overflow-hidden relative">
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
              <div className="w-3 h-3 rounded-full bg-slate-500"></div>
              EduConnect events
            </div>
            <div className="flex items-center gap-3 text-slate-600 dark:text-slate-400">
              <div className="w-3 h-3 rounded-full bg-amber-600"></div>
              Time off
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-white dark:bg-slate-900 overflow-hidden relative">
        {mode === "calendar" && (
          <>
            {/* Google Calendar Integration Banner */}
            {!isCalendarConnected && showConnectBanner && (
              <div className="mx-4 mt-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-100 dark:border-blue-800/50 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-in fade-in slide-in-from-top-2 duration-300 shadow-sm relative group">
                <div className="flex gap-4 items-center">
                  <div className="hidden sm:flex p-2.5 bg-white dark:bg-slate-800 rounded-lg shadow-sm text-blue-600 dark:text-blue-400 items-center justify-center">
                    <CalendarIcon size={20} />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white text-sm sm:text-base flex items-center gap-2">
                      Sync Google Calendar
                      <span className="text-[10px] bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full font-bold uppercase tracking-wide">
                        Beta
                      </span>
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 mt-0.5">
                      Avoid double bookings and sync your schedule automatically.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <button
                    onClick={() => setIsSyncModalOpen(true)}
                    className="flex-1 sm:flex-initial px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs sm:text-sm font-bold rounded-lg transition-colors shadow-sm whitespace-nowrap"
                  >
                    Connect Now
                  </button>
                </div>
                <button
                  onClick={() => setShowConnectBanner(false)}
                  className="absolute top-2 right-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 hover:bg-blue-100 dark:hover:bg-blue-900/40 rounded transition-colors opacity-0 group-hover:opacity-100"
                >
                  <X size={16} />
                </button>
              </div>
            )}

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
                    className={`px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-all ${view === "Day" ? "bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white ring-2 ring-emerald-500/20" : "text-slate-500 hover:text-slate-900 dark:hover:text-white"}`}
                  >
                    Today
                  </button>
                  <button
                    onClick={() => setView("Week")}
                    className={`px-3 py-1 rounded-md text-xs sm:text-sm font-medium transition-all ${view === "Week" ? "bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white ring-2 ring-emerald-500/20" : "text-slate-500 hover:text-slate-900 dark:hover:text-white"}`}
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
              {/* Mobile-oriented layout: Day view fits 100%, Week view scrolls */}
              <div className={view === "Day" ? "w-full" : "min-w-[600px] md:min-w-[800px]"}>
                {/* Header Row */}
                <div
                  className="grid border-b border-slate-200 dark:border-slate-800 sticky top-0 bg-white dark:bg-slate-900 z-30"
                  style={{
                    gridTemplateColumns:
                      view === "Day"
                        ? "50px 1fr"
                        : `60px repeat(${days.length}, 1fr)`,
                  }}
                >
                  <div className="sticky left-0 z-40 bg-white dark:bg-slate-900 p-2 sm:p-4 text-[10px] sm:text-xs font-bold text-slate-400 border-r border-slate-100 dark:border-slate-800 text-center flex items-end justify-center pb-2 shadow-[4px_0_10px_-4px_rgba(0,0,0,0.1)] dark:shadow-[4px_0_10px_-4px_rgba(0,0,0,0.5)]">
                    {timezone}
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
                      className="grid h-20 sm:h-24 border-b border-slate-100 dark:border-slate-800"
                      style={{
                        gridTemplateColumns:
                          view === "Day"
                            ? "50px 1fr"
                            : `60px repeat(${days.length}, 1fr)`,
                      }}
                    >
                      {/* Sticky Time Label */}
                      <div className="sticky left-0 z-20 bg-white dark:bg-slate-900 text-[10px] sm:text-xs text-slate-400 text-right pr-2 sm:pr-3 pt-2 border-r border-slate-100 dark:border-slate-800 relative shadow-[4px_0_10px_-4px_rgba(0,0,0,0.1)] dark:shadow-[4px_0_10px_-4px_rgba(0,0,0,0.5)]">
                        <span className="-mt-3 block">{time}</span>
                      </div>

                      {/* Day Cells */}
                      {days.map((day, j) => (
                        <div
                          key={j}
                          className="border-r border-slate-100 dark:border-slate-800 last:border-r-0 relative group"
                        >
                          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-slate-50 dark:bg-slate-800/30 transition-opacity cursor-pointer"></div>

                          {/* Real Calendar Events */}
                          {(() => {
                            const slotEvents = getEventsForSlot(day, time);
                            return slotEvents.map((event) => {
                              const eventStart = event.start;
                              const eventEnd = event.end;
                              const startMinutes = eventStart.getMinutes();
                              const durationMinutes =
                                (eventEnd.getTime() - eventStart.getTime()) / (1000 * 60);
                              const heightPercent = (durationMinutes / 60) * 100;
                              const topOffset = (startMinutes / 60) * 100;
                              const colors = getEventColor(event.type, event.status);

                              return (
                                <div
                                  key={event.id}
                                  onClick={() => handleEventClick(event)}
                                  className={`absolute left-1 right-1 ${colors.bg} border-l-4 ${colors.border} rounded p-1 sm:p-2 z-10 shadow-sm cursor-pointer hover:shadow-md transition-shadow`}
                                  style={{
                                    top: `${topOffset}%`,
                                    height: `${Math.max(heightPercent, 20)}%`,
                                    minHeight: "3rem",
                                  }}
                                >
                                  <div className="font-bold text-[10px] sm:text-xs text-slate-900 dark:text-white truncate">
                                    {event.title}
                                  </div>
                                  <div className="text-[9px] sm:text-[10px] text-slate-500">
                                    {eventStart.toLocaleTimeString("en-US", {
                                      hour: "2-digit",
                                      minute: "2-digit",
                                    })}{" "}
                                    -{" "}
                                    {eventEnd.toLocaleTimeString("en-US", {
                                      hour: "2-digit",
                                      minute: "2-digit",
                                    })}
                                  </div>
                                  {event.subject && (
                                    <div className="text-[9px] sm:text-[10px] text-slate-500 mt-0.5">
                                      {event.subject}
                                    </div>
                                  )}
                                  {event.status && (
                                    <span className="text-[9px] bg-white dark:bg-slate-800 px-1 py-0.5 rounded text-slate-500 mt-1 inline-block">
                                      {event.status}
                                    </span>
                                  )}
                                </div>
                              );
                            });
                          })()}

                          {/* Fallback Mock Events (if no real events) */}
                          {calendarEvents.length === 0 && (
                            <>
                              {view === "Week" && day.name === "Fri" && time === "00:00" && (
                                <div className="absolute top-1 left-1 right-1 h-16 sm:h-20 bg-slate-100 dark:bg-slate-800 border-l-4 border-indigo-500 rounded p-1 sm:p-2 z-10 shadow-sm cursor-pointer hover:shadow-md transition-shadow">
                                  <div className="font-bold text-[10px] sm:text-xs text-slate-900 dark:text-white truncate">
                                    What&apos;s new...
                                  </div>
                                  <div className="text-[9px] sm:text-[10px] text-slate-500">
                                    00:00 - 01:00
                                  </div>
                                </div>
                              )}

                              {view === "Week" && day.name === "Sat" && time === "00:00" && (
                                <div className="absolute top-1 left-1 right-1 h-16 sm:h-20 bg-pink-50 dark:bg-pink-900/20 border-l-4 border-pink-500 rounded p-1 sm:p-2 z-10 shadow-sm cursor-pointer hover:shadow-md transition-shadow">
                                  <div className="font-bold text-[10px] sm:text-xs text-slate-900 dark:text-white truncate">
                                    Mauricio E.
                                  </div>
                                  <div className="text-[9px] sm:text-[10px] text-slate-500">
                                    00:00 - 01:00
                                  </div>
                                </div>
                              )}

                              {view === "Week" && day.name === "Tue" && time === "01:00" && (
                                <div className="absolute top-4 left-1 right-1 h-16 sm:h-20 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded p-1 sm:p-2 z-10 shadow-sm cursor-pointer hover:shadow-md transition-shadow">
                                  <div className="font-bold text-[10px] sm:text-xs text-slate-900 dark:text-white truncate">
                                    Elodie C.
                                  </div>
                                  <div className="text-[9px] sm:text-[10px] text-slate-500">
                                    01:00 - 01:50
                                  </div>
                                </div>
                              )}

                              {view === "Week" && day.name === "Thu" && time === "02:00" && (
                                <div className="absolute top-2 left-1 right-1 h-16 sm:h-20 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 rounded p-1 sm:p-2 z-10 shadow-sm cursor-pointer hover:shadow-md transition-shadow">
                                  <div className="font-bold text-[10px] sm:text-xs text-slate-900 dark:text-white truncate">
                                    Elodie C.
                                  </div>
                                  <div className="text-[9px] sm:text-[10px] text-slate-500">
                                    02:00 - 02:50
                                  </div>
                                </div>
                              )}

                              {/* Day View Example Event */}
                              {view === "Day" && time === "14:00" && (
                                <div className="absolute top-2 left-2 right-2 h-16 sm:h-20 bg-emerald-50 dark:bg-emerald-900/20 border-l-4 border-emerald-500 rounded p-2 z-10 shadow-sm cursor-pointer">
                                  <div className="flex items-center justify-between">
                                    <div className="font-bold text-xs sm:text-sm text-slate-900 dark:text-white">
                                      Meeting with Sarah
                                    </div>
                                    <span className="text-[10px] bg-white dark:bg-slate-800 px-1.5 py-0.5 rounded text-slate-500">
                                      Confirmed
                                    </span>
                                  </div>
                                  <div className="text-xs text-slate-500 mt-1">
                                    14:00 - 15:00 • Algebra
                                  </div>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  ))}
                  {/* Fade out bottom to indicate scroll */}
                  <div className="sticky bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-white dark:from-slate-900 to-transparent pointer-events-none z-20"></div>
                </div>
              </div>
            </div>
          </>
        )}

        {mode === "setup" && (
          <div className="flex flex-col h-full animate-in fade-in slide-in-from-right-4 duration-300">
            {/* Header */}
            <div className="p-4 md:p-6 border-b border-slate-200 dark:border-slate-800 flex justify-between items-start bg-white dark:bg-slate-900 sticky top-0 z-10">
              <div>
                <h2 className="text-lg md:text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span className="p-1 bg-emerald-100 dark:bg-emerald-900/30 rounded text-emerald-600 dark:text-emerald-400">
                    <Clock size={18} />
                  </span>
                  Weekly Availability
                </h2>
                <p className="text-xs md:text-sm text-slate-500 mt-1 max-w-[200px] md:max-w-none">
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
                              className="flex items-center gap-2 animate-in fade-in slide-in-from-top-1 duration-200"
                            >
                              <div className="flex-1 grid grid-cols-2 gap-2">
                                <div className="relative">
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
                                </div>
                                <div className="relative">
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
            <div className="p-4 md:p-6 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex justify-end gap-3 sticky bottom-0 z-20 pb-safe">
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

      {/* Sync Calendar Modal */}
      {isSyncModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-md shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden scale-100 animate-in zoom-in-95 duration-200 relative">
            <button
              onClick={() => setIsSyncModalOpen(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors"
            >
              <X size={20} />
            </button>

            <div className="p-8 text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-6 text-blue-600 dark:text-blue-400">
                <LinkIcon size={32} />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                Connect Google Calendar
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-8 leading-relaxed">
                Sync your lessons with your personal calendar to never miss a
                session and avoid double bookings.
              </p>

              <div className="space-y-3 mb-8 text-left bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                <div className="flex items-start gap-3">
                  <Check
                    className="text-emerald-500 mt-0.5 shrink-0"
                    size={16}
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Auto-add booked lessons to calendar
                  </span>
                </div>
                <div className="flex items-start gap-3">
                  <Check
                    className="text-emerald-500 mt-0.5 shrink-0"
                    size={16}
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Block busy times from your availability
                  </span>
                </div>
                <div className="flex items-start gap-3">
                  <Check
                    className="text-emerald-500 mt-0.5 shrink-0"
                    size={16}
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">
                    Secure connection (Read/Write access)
                  </span>
                </div>
              </div>

              <button
                onClick={handleConnectCalendar}
                disabled={isConnecting}
                className="w-full py-3.5 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 transition-all active:scale-95 flex items-center justify-center gap-2"
              >
                {isConnecting ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <svg
                      viewBox="0 0 24 24"
                      className="w-5 h-5 fill-white"
                    >
                      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                    Sign in with Google
                  </>
                )}
              </button>

              <p className="text-xs text-slate-400 mt-4">
                By connecting, you agree to our{" "}
                <a href="#" className="underline">
                  Terms of Service
                </a>{" "}
                and{" "}
                <a href="#" className="underline">
                  Privacy Policy
                </a>
                .
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Event Detail Modal */}
      {isEventModalOpen && selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-md shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden scale-100 animate-in zoom-in-95 duration-200 relative">
            <button
              onClick={() => {
                setIsEventModalOpen(false);
                setSelectedEvent(null);
              }}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors"
            >
              <X size={20} />
            </button>

            <div className="p-6">
              <div className="flex items-start gap-4 mb-4">
                <div
                  className={`p-3 rounded-lg ${
                    selectedEvent.type === "trial"
                      ? "bg-emerald-100 dark:bg-emerald-900/30"
                      : selectedEvent.type === "weekly"
                      ? "bg-pink-100 dark:bg-pink-900/30"
                      : "bg-blue-100 dark:bg-blue-900/30"
                  }`}
                >
                  <CalendarIcon
                    size={24}
                    className={
                      selectedEvent.type === "trial"
                        ? "text-emerald-600 dark:text-emerald-400"
                        : selectedEvent.type === "weekly"
                        ? "text-pink-600 dark:text-pink-400"
                        : "text-blue-600 dark:text-blue-400"
                    }
                  />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
                    {selectedEvent.title}
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {selectedEvent.subject || "Lesson"}
                  </p>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <div className="flex items-center gap-3 text-sm">
                  <Clock size={16} className="text-slate-400" />
                  <span className="text-slate-700 dark:text-slate-300">
                    {selectedEvent.start.toLocaleString("en-US", {
                      weekday: "long",
                      month: "long",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}{" "}
                    -{" "}
                    {selectedEvent.end.toLocaleTimeString("en-US", {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                {selectedEvent.booking && (
                  <>
                    {selectedEvent.booking.topic && (
                      <div className="flex items-start gap-3 text-sm">
                        <Info size={16} className="text-slate-400 mt-0.5" />
                        <span className="text-slate-700 dark:text-slate-300">
                          {selectedEvent.booking.topic}
                        </span>
                      </div>
                    )}
                    {selectedEvent.booking.notes_student && (
                      <div className="flex items-start gap-3 text-sm">
                        <Info size={16} className="text-slate-400 mt-0.5" />
                        <span className="text-slate-700 dark:text-slate-300">
                          Student notes: {selectedEvent.booking.notes_student}
                        </span>
                      </div>
                    )}
                    {selectedEvent.booking.notes_tutor && (
                      <div className="flex items-start gap-3 text-sm">
                        <Info size={16} className="text-slate-400 mt-0.5" />
                        <span className="text-slate-700 dark:text-slate-300">
                          Your notes: {selectedEvent.booking.notes_tutor}
                        </span>
                      </div>
                    )}
                    {selectedEvent.booking.join_url && (
                      <div className="flex items-center gap-3 text-sm">
                        <LinkIcon size={16} className="text-slate-400" />
                        <a
                          href={selectedEvent.booking.join_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Join Meeting
                        </a>
                      </div>
                    )}
                  </>
                )}
              </div>

              <div className="flex gap-3">
                {selectedEvent.booking && selectedEvent.booking.status === "pending" && (
                  <>
                    <button
                      onClick={async () => {
                        if (selectedEvent.booking) {
                          try {
                            await bookings.confirm(selectedEvent.booking.id);
                            showSuccess("Booking confirmed");
                            setIsEventModalOpen(false);
                            setSelectedEvent(null);
                            loadBookings();
                          } catch (error) {
                            showError("Failed to confirm booking");
                          }
                        }
                      }}
                      className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-colors"
                    >
                      Confirm
                    </button>
                    <button
                      onClick={async () => {
                        if (selectedEvent.booking) {
                          try {
                            await bookings.decline(selectedEvent.booking.id);
                            showSuccess("Booking declined");
                            setIsEventModalOpen(false);
                            setSelectedEvent(null);
                            loadBookings();
                          } catch (error) {
                            showError("Failed to decline booking");
                          }
                        }
                      }}
                      className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-bold rounded-lg transition-colors"
                    >
                      Decline
                    </button>
                  </>
                )}
                <button
                  onClick={() => {
                    setIsEventModalOpen(false);
                    setSelectedEvent(null);
                  }}
                  className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
