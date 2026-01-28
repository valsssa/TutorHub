"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import {
  FiChevronLeft,
  FiChevronRight,
  FiCalendar,
  FiClock,
} from "react-icons/fi";
import { getApiBaseUrl } from "@/shared/utils/url";
import { useWebSocket } from "@/hooks/useWebSocket";

interface TimeSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

interface TimeSlotPickerProps {
  tutorId: number;
  onSelectSlot: (startTime: string, endTime: string) => void;
  selectedStartTime?: string;
}

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export default function TimeSlotPicker({
  tutorId,
  onSelectSlot,
  selectedStartTime,
}: TimeSlotPickerProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(false);
  const [slotsCache, setSlotsCache] = useState<Record<string, TimeSlot[]>>({});
  const { lastMessage } = useWebSocket();

  // Refetch slots for the currently selected date
  const refetchSelectedDate = useCallback(() => {
    if (selectedDate) {
      setSlotsCache({});
      // Reset selectedDate to trigger the fetch effect
      const date = selectedDate;
      setSelectedDate(null);
      setTimeout(() => setSelectedDate(date), 0);
    }
  }, [selectedDate]);

  // Listen for real-time availability updates via WebSocket
  useEffect(() => {
    if (
      lastMessage?.type === "availability_updated" &&
      lastMessage.tutor_profile_id === tutorId
    ) {
      refetchSelectedDate();
    }
  }, [lastMessage, tutorId, refetchSelectedDate]);

  // Get calendar days for current month
  const calendarDays = useMemo(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days: (Date | null)[] = [];

    // Add empty slots for days before month starts
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }

    // Add all days in month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }

    return days;
  }, [currentMonth]);

  // Fetch available slots when date is selected
  useEffect(() => {
    if (!selectedDate) {
      setAvailableSlots([]);
      return;
    }

    // Use local date components for cache key to match the API query dates
    const year = selectedDate.getFullYear();
    const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
    const day = String(selectedDate.getDate()).padStart(2, '0');
    const dateKey = `${year}-${month}-${day}`;

    // Check cache first
    if (slotsCache[dateKey]) {
      setAvailableSlots(slotsCache[dateKey]);
      return;
    }

    const fetchSlots = async () => {
      setLoading(true);
      try {
        // Use UTC dates to avoid timezone issues
        // The backend expects dates in ISO format and processes them in UTC
        const year = selectedDate.getFullYear();
        const month = selectedDate.getMonth();
        const day = selectedDate.getDate();
        
        // Create dates in local timezone but format as the intended date
        // This ensures we query for the correct calendar day regardless of timezone
        const startDateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}T00:00:00`;
        const endDateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}T23:59:59`;

        const API_URL = getApiBaseUrl(process.env.NEXT_PUBLIC_API_URL);
        if (!API_URL) {
          setAvailableSlots([]);
          return;
        }
        const token = document.cookie
          .split("; ")
          .find((row) => row.startsWith("token="))
          ?.split("=")[1];

        const response = await fetch(
          `${API_URL}/api/tutors/${tutorId}/available-slots?start_date=${startDateStr}&end_date=${endDateStr}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.ok) {
          const slots = await response.json();
          setAvailableSlots(slots);
          setSlotsCache((prev) => ({ ...prev, [dateKey]: slots }));
        } else {
          setAvailableSlots([]);
        }
      } catch (error) {
        // Silent fail - empty state will show "No available slots"
        setAvailableSlots([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSlots();
  }, [selectedDate, tutorId, slotsCache]);

  const handlePrevMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1)
    );
    setSelectedDate(null);
  };

  const handleNextMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1)
    );
    setSelectedDate(null);
  };

  const handleDateClick = (date: Date) => {
    if (date < new Date(new Date().setHours(0, 0, 0, 0))) {
      return; // Can't select past dates
    }
    setSelectedDate(date);
  };

  const formatTime = (timeString: string) => {
    const date = new Date(timeString);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  };

  const isToday = (date: Date) => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const isSelected = (date: Date) => {
    return (
      selectedDate &&
      date.getDate() === selectedDate.getDate() &&
      date.getMonth() === selectedDate.getMonth() &&
      date.getFullYear() === selectedDate.getFullYear()
    );
  };

  return (
    <div className="space-y-6">
      {/* Calendar Section */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {/* Month Navigation */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={handlePrevMonth}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            type="button"
          >
            <FiChevronLeft className="w-5 h-5 text-gray-600" />
          </button>
          <h3 className="text-lg font-semibold text-gray-900">
            {MONTHS[currentMonth.getMonth()]} {currentMonth.getFullYear()}
          </h3>
          <button
            onClick={handleNextMonth}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            type="button"
          >
            <FiChevronRight className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1">
          {/* Day headers */}
          {DAYS.map((day) => (
            <div
              key={day}
              className="text-center text-xs font-medium text-gray-500 py-2"
            >
              {day}
            </div>
          ))}

          {/* Calendar days */}
          {calendarDays.map((date, index) => {
            if (!date) {
              return <div key={`empty-${index}`} className="aspect-square" />;
            }

            const isPast = date < new Date(new Date().setHours(0, 0, 0, 0));
            const today = isToday(date);
            const selected = isSelected(date);

            return (
              <button
                key={date.toISOString()}
                onClick={() => handleDateClick(date)}
                disabled={isPast}
                type="button"
                className={`
                  aspect-square flex items-center justify-center rounded-lg text-sm font-medium
                  transition-all duration-200
                  ${isPast ? "text-gray-300 cursor-not-allowed" : ""}
                  ${!isPast && !selected ? "hover:bg-emerald-50 text-gray-700" : ""}
                  ${selected ? "bg-emerald-500 text-white shadow-md scale-105" : ""}
                  ${today && !selected ? "ring-2 ring-emerald-300" : ""}
                `}
              >
                {date.getDate()}
              </button>
            );
          })}
        </div>
      </div>

      {/* Time Slots Section */}
      {selectedDate && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-4">
            <FiClock className="w-5 h-5 text-emerald-600" />
            <h4 className="font-semibold text-gray-900">
              Available Times - {selectedDate.toLocaleDateString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
              })}
            </h4>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
            </div>
          ) : availableSlots.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-64 overflow-y-auto">
              {availableSlots.map((slot) => {
                const isSlotSelected = selectedStartTime === slot.start_time;
                return (
                  <button
                    key={slot.start_time}
                    onClick={() => onSelectSlot(slot.start_time, slot.end_time)}
                    type="button"
                    className={`
                      px-4 py-3 rounded-lg border-2 font-medium text-sm
                      transition-all duration-200
                      ${
                        isSlotSelected
                          ? "border-emerald-500 bg-emerald-50 text-emerald-700 shadow-sm"
                          : "border-gray-200 hover:border-emerald-300 hover:bg-emerald-50 text-gray-700"
                      }
                    `}
                  >
                    {formatTime(slot.start_time)}
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <FiCalendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">
                No available slots for this date
              </p>
              <p className="text-gray-400 text-xs mt-1">
                Try selecting a different date
              </p>
            </div>
          )}
        </div>
      )}

      {!selectedDate && (
        <div className="text-center py-8 text-gray-500 text-sm">
          <FiCalendar className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p>Select a date to view available time slots</p>
        </div>
      )}
    </div>
  );
}
