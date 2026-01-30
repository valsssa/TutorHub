"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  List,
  Clock,
  User,
  Video,
  Plus,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { CalendarSkeleton } from "@/components/SkeletonLoader";
import { bookings as bookingsApi, auth } from "@/lib/api";
import type { BookingDTO } from "@/types/booking";
import type { User as UserType } from "@/types";
import clsx from "clsx";

type ViewMode = "month" | "week";

const DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

function getStatusColor(status: string): string {
  const normalized = status.toLowerCase();
  if (normalized === "confirmed") return "bg-emerald-500";
  if (normalized === "pending") return "bg-amber-500";
  if (normalized === "completed") return "bg-slate-400";
  if (normalized.includes("cancelled")) return "bg-red-500";
  return "bg-slate-400";
}

function getDaysInMonth(year: number, month: number): Date[] {
  const days: Date[] = [];
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);

  // Add days from previous month to fill the first week
  const startDayOfWeek = firstDay.getDay();
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    const date = new Date(year, month, -i);
    days.push(date);
  }

  // Add days of current month
  for (let i = 1; i <= lastDay.getDate(); i++) {
    days.push(new Date(year, month, i));
  }

  // Add days from next month to fill the last week
  const remainingDays = 42 - days.length; // 6 rows * 7 days
  for (let i = 1; i <= remainingDays; i++) {
    days.push(new Date(year, month + 1, i));
  }

  return days;
}

function getWeekDays(date: Date): Date[] {
  const days: Date[] = [];
  const startOfWeek = new Date(date);
  startOfWeek.setDate(date.getDate() - date.getDay());

  for (let i = 0; i < 7; i++) {
    const day = new Date(startOfWeek);
    day.setDate(startOfWeek.getDate() + i);
    days.push(day);
  }

  return days;
}

function isSameDay(date1: Date, date2: Date): boolean {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
}

export default function BookingCalendarPage() {
  return (
    <ProtectedRoute>
      <CalendarContent />
    </ProtectedRoute>
  );
}

function CalendarContent() {
  const router = useRouter();

  const [currentUser, setCurrentUser] = useState<UserType | null>(null);
  const [bookingsList, setBookingsList] = useState<BookingDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [user, data] = await Promise.all([
        auth.getCurrentUser(),
        bookingsApi.getMyBookings(),
      ]);
      setCurrentUser(user);
      setBookingsList(data);
    } catch (error) {
      console.error("Failed to load bookings:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Calculate calendar days
  const calendarDays = useMemo(() => {
    if (viewMode === "month") {
      return getDaysInMonth(currentDate.getFullYear(), currentDate.getMonth());
    }
    return getWeekDays(currentDate);
  }, [currentDate, viewMode]);

  // Get bookings for a specific day
  const getBookingsForDay = useCallback(
    (date: Date): BookingDTO[] => {
      return bookingsList.filter((booking) => {
        const bookingDate = new Date(booking.start_at);
        return isSameDay(bookingDate, date);
      });
    },
    [bookingsList]
  );

  // Get bookings for selected date
  const selectedDateBookings = useMemo(() => {
    if (!selectedDate) return [];
    return getBookingsForDay(selectedDate);
  }, [selectedDate, getBookingsForDay]);

  // Navigation
  const goToPrevious = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
    } else {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() - 7);
      setCurrentDate(newDate);
    }
  };

  const goToNext = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
    } else {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() + 7);
      setCurrentDate(newDate);
    }
  };

  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  };

  const today = new Date();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
          <div className="container mx-auto px-4 py-4">
            <Breadcrumb
              items={[
                { label: "Bookings", href: "/bookings" },
                { label: "Calendar" },
              ]}
            />
          </div>
        </div>
        <div className="container mx-auto px-4 py-8 max-w-6xl">
          <CalendarSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb
            items={[
              { label: "Bookings", href: "/bookings" },
              { label: "Calendar" },
            ]}
          />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Calendar Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              {viewMode === "month"
                ? `${MONTHS[currentDate.getMonth()]} ${currentDate.getFullYear()}`
                : `Week of ${currentDate.toLocaleDateString("en-US", { month: "short", day: "numeric" })}`}
            </h1>
            <div className="flex items-center gap-1">
              <button
                onClick={goToPrevious}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <ChevronLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              </button>
              <button
                onClick={goToNext}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <ChevronRight className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={goToToday}>
              Today
            </Button>

            {/* View Mode Toggle */}
            <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-1">
              <button
                onClick={() => setViewMode("month")}
                className={clsx(
                  "px-3 py-1.5 rounded text-sm font-medium transition-colors",
                  viewMode === "month"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400"
                )}
              >
                Month
              </button>
              <button
                onClick={() => setViewMode("week")}
                className={clsx(
                  "px-3 py-1.5 rounded text-sm font-medium transition-colors",
                  viewMode === "week"
                    ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm"
                    : "text-slate-600 dark:text-slate-400"
                )}
              >
                Week
              </button>
            </div>

            <Link href="/bookings">
              <Button variant="secondary" size="sm">
                <List className="w-4 h-4 mr-2" />
                List View
              </Button>
            </Link>

            {currentUser?.role === "student" && (
              <Link href="/tutors">
                <Button size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Book Session
                </Button>
              </Link>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calendar Grid */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              {/* Days Header */}
              <div className="grid grid-cols-7 border-b border-slate-200 dark:border-slate-700">
                {DAYS_OF_WEEK.map((day) => (
                  <div
                    key={day}
                    className="py-3 text-center text-sm font-medium text-slate-500 dark:text-slate-400"
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Days */}
              <div className={clsx(
                "grid grid-cols-7",
                viewMode === "month" ? "auto-rows-[100px]" : "auto-rows-[200px]"
              )}>
                {calendarDays.map((date, index) => {
                  const dayBookings = getBookingsForDay(date);
                  const isCurrentMonth = date.getMonth() === currentDate.getMonth();
                  const isToday = isSameDay(date, today);
                  const isSelected = selectedDate && isSameDay(date, selectedDate);

                  return (
                    <button
                      key={index}
                      onClick={() => setSelectedDate(date)}
                      className={clsx(
                        "relative p-2 border-b border-r border-slate-100 dark:border-slate-800 text-left transition-colors",
                        "hover:bg-slate-50 dark:hover:bg-slate-800/50",
                        !isCurrentMonth && "bg-slate-50/50 dark:bg-slate-950/50",
                        isSelected && "bg-emerald-50 dark:bg-emerald-900/20 ring-2 ring-emerald-500 ring-inset"
                      )}
                    >
                      {/* Date Number */}
                      <div
                        className={clsx(
                          "w-7 h-7 flex items-center justify-center rounded-full text-sm font-medium mb-1",
                          isToday && "bg-emerald-600 text-white",
                          !isToday && isCurrentMonth && "text-slate-900 dark:text-white",
                          !isToday && !isCurrentMonth && "text-slate-400 dark:text-slate-600"
                        )}
                      >
                        {date.getDate()}
                      </div>

                      {/* Bookings */}
                      <div className="space-y-1 overflow-hidden">
                        {dayBookings.slice(0, viewMode === "month" ? 2 : 5).map((booking) => (
                          <div
                            key={booking.id}
                            className={clsx(
                              "text-xs px-1.5 py-0.5 rounded truncate text-white",
                              getStatusColor(booking.status)
                            )}
                            title={`${booking.subject_name || "Session"} - ${new Date(booking.start_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`}
                          >
                            {new Date(booking.start_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                            {" "}
                            {booking.subject_name || "Session"}
                          </div>
                        ))}
                        {dayBookings.length > (viewMode === "month" ? 2 : 5) && (
                          <div className="text-xs text-slate-500 dark:text-slate-400 px-1.5">
                            +{dayBookings.length - (viewMode === "month" ? 2 : 5)} more
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Legend */}
            <div className="flex flex-wrap gap-4 mt-4 px-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-emerald-500" />
                <span className="text-sm text-slate-600 dark:text-slate-400">Confirmed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-amber-500" />
                <span className="text-sm text-slate-600 dark:text-slate-400">Pending</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-slate-400" />
                <span className="text-sm text-slate-600 dark:text-slate-400">Completed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500" />
                <span className="text-sm text-slate-600 dark:text-slate-400">Cancelled</span>
              </div>
            </div>
          </div>

          {/* Selected Day Details */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden sticky top-24">
              <div className="px-5 py-4 border-b border-slate-200 dark:border-slate-800">
                <h2 className="font-bold text-slate-900 dark:text-white">
                  {selectedDate
                    ? selectedDate.toLocaleDateString("en-US", {
                        weekday: "long",
                        month: "long",
                        day: "numeric",
                      })
                    : "Select a date"}
                </h2>
              </div>

              <div className="p-4">
                {!selectedDate ? (
                  <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-8">
                    Click on a date to view bookings
                  </p>
                ) : selectedDateBookings.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3">
                      <CalendarIcon className="w-6 h-6 text-slate-400" />
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                      No bookings on this day
                    </p>
                    {currentUser?.role === "student" && (
                      <Link href="/tutors">
                        <Button size="sm">Book a Session</Button>
                      </Link>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedDateBookings.map((booking) => {
                      const otherPerson =
                        currentUser?.role === "student" ? booking.tutor : booking.student;
                      return (
                        <Link
                          key={booking.id}
                          href={`/bookings/${booking.id}`}
                          className="block p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <div>
                              <p className="font-medium text-slate-900 dark:text-white">
                                {booking.subject_name || "Session"}
                              </p>
                              <div className="flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400">
                                <User className="w-3 h-3" />
                                {otherPerson?.name}
                              </div>
                            </div>
                            <StatusBadge status={booking.status} type="session" />
                          </div>

                          <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-400">
                            <span className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {new Date(booking.start_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                              {" - "}
                              {new Date(booking.end_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>

                          {booking.join_url && booking.status.toLowerCase() === "confirmed" && (
                            <Button
                              size="sm"
                              className="w-full mt-3"
                              onClick={(e) => {
                                e.preventDefault();
                                window.open(booking.join_url, "_blank");
                              }}
                            >
                              <Video className="w-4 h-4 mr-2" />
                              Join Session
                            </Button>
                          )}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
