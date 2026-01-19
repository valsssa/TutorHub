"use client";

import { useState, useEffect, useCallback } from "react";
import { FiClock, FiTrash2, FiPlus, FiSave } from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useToast } from "@/components/ToastContainer";
import { tutors } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { useAuth } from "@/lib/hooks/useAuth";
import { useRouter } from "next/navigation";
import type { TutorProfile } from "@/types";

interface AvailabilitySlot {
  id?: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  is_recurring: boolean;
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

const TIME_SLOTS = Array.from({ length: 48 }, (_, i) => {
  const hour = Math.floor(i / 2);
  const minute = (i % 2) * 30;
  const time = `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
  const displayHour = hour === 0 ? 12 : hour > 12 ? hour - 12 : hour;
  const period = hour < 12 ? "AM" : "PM";
  const displayTime = `${displayHour}:${minute.toString().padStart(2, "0")} ${period}`;
  return { time, displayTime };
});

export default function TutorAvailabilityPage() {
  return (
    <ProtectedRoute requiredRole="tutor">
      <AvailabilityContent />
    </ProtectedRoute>
  );
}

function AvailabilityContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const { user } = useAuth({ requiredRole: "tutor" });
  const [profile, setProfile] = useState<TutorProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [selectedSlots, setSelectedSlots] = useState<
    Record<number, { start: string; end: string }[]>
  >({});
  const [timezone, setTimezone] = useState("UTC");

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      const profileData = await tutors.getMyProfile();
      setProfile(profileData);
      setTimezone(profileData.timezone || "UTC");

      // Convert availabilities to selected slots format
      const slotsMap: Record<number, { start: string; end: string }[]> = {};
      (profileData.availabilities || []).forEach((av) => {
        if (!slotsMap[av.day_of_week]) {
          slotsMap[av.day_of_week] = [];
        }
        slotsMap[av.day_of_week].push({
          start: av.start_time.slice(0, 5),
          end: av.end_time.slice(0, 5),
        });
      });
      setSelectedSlots(slotsMap);
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

  const addTimeSlot = (dayOfWeek: number) => {
    const newSlots = { ...selectedSlots };
    if (!newSlots[dayOfWeek]) {
      newSlots[dayOfWeek] = [];
    }
    newSlots[dayOfWeek].push({ start: "09:00", end: "17:00" });
    setSelectedSlots(newSlots);
  };

  const removeTimeSlot = (dayOfWeek: number, index: number) => {
    const newSlots = { ...selectedSlots };
    newSlots[dayOfWeek].splice(index, 1);
    if (newSlots[dayOfWeek].length === 0) {
      delete newSlots[dayOfWeek];
    }
    setSelectedSlots(newSlots);
  };

  const updateTimeSlot = (
    dayOfWeek: number,
    index: number,
    field: "start" | "end",
    value: string
  ) => {
    const newSlots = { ...selectedSlots };
    if (newSlots[dayOfWeek] && newSlots[dayOfWeek][index]) {
      newSlots[dayOfWeek][index][field] = value;
      setSelectedSlots(newSlots);
    }
  };

  const handleSave = async () => {
    if (!profile) {
      showError("Profile not loaded");
      return;
    }

    // Validate all slots
    for (const dayOfWeek in selectedSlots) {
      for (const slot of selectedSlots[dayOfWeek]) {
        if (slot.start >= slot.end) {
          showError("End time must be after start time");
          return;
        }
      }
    }

    setSaving(true);
    try {
      // Convert to API format
      const availabilityData = Object.entries(selectedSlots).flatMap(
        ([dayOfWeek, slots]) =>
          slots.map((slot) => ({
            day_of_week: Number(dayOfWeek),
            start_time: slot.start,
            end_time: slot.end,
            is_recurring: true,
          }))
      );

      const updated = await tutors.replaceAvailability({
        availability: availabilityData,
        timezone,
        version: profile.version,
      });

      setProfile(updated);
      showSuccess("Availability updated successfully");
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string }; status?: number } };
      if (err.response?.status === 409) {
        showError("Profile was updated by another session. Refreshing...");
        await loadProfile();
      } else {
        showError(err.response?.data?.detail || "Failed to update availability");
      }
    } finally {
      setSaving(false);
    }
  };

  const copyToAllDays = (dayOfWeek: number) => {
    const slots = selectedSlots[dayOfWeek];
    if (!slots || slots.length === 0) {
      showError("No slots to copy from this day");
      return;
    }

    const newSlots = { ...selectedSlots };
    DAYS.forEach((day) => {
      newSlots[day.id] = [...slots];
    });
    setSelectedSlots(newSlots);
    showSuccess("Copied to all days");
  };

  const clearDay = (dayOfWeek: number) => {
    const newSlots = { ...selectedSlots };
    delete newSlots[dayOfWeek];
    setSelectedSlots(newSlots);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Manage Availability</h1>
        <p className="text-gray-600 mt-2">
          Set your weekly availability for tutoring sessions
        </p>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
        <p className="text-sm text-blue-800 flex items-center gap-2">
          <FiClock className="w-4 h-4" />
          Students will only be able to book sessions during your available hours.
          Set recurring weekly time slots below.
        </p>
      </div>

      {/* Timezone Selector */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Timezone
        </label>
        <input
          type="text"
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          className="w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="America/New_York"
        />
        <p className="text-sm text-gray-500 mt-1">
          Use a valid IANA timezone (e.g., America/New_York, Europe/London)
        </p>
      </div>

      {/* Weekly Calendar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {DAYS.map((day) => (
          <div
            key={day.id}
            className="border-b border-gray-200 last:border-b-0 hover:bg-gray-50 transition-colors"
          >
            <div className="p-6">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                {/* Day Header */}
                <div className="flex items-center gap-4">
                  <div className="w-24">
                    <h3 className="font-semibold text-gray-900">{day.name}</h3>
                    <p className="text-xs text-gray-500">{day.short}</p>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => addTimeSlot(day.id)}
                      className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 hover:bg-primary-50 px-3 py-1 rounded-lg transition-colors"
                      type="button"
                    >
                      <FiPlus className="w-4 h-4" /> Add Time
                    </button>
                    {selectedSlots[day.id] && selectedSlots[day.id].length > 0 && (
                      <>
                        <button
                          onClick={() => copyToAllDays(day.id)}
                          className="text-sm text-gray-600 hover:text-gray-700 font-medium hover:bg-gray-100 px-3 py-1 rounded-lg transition-colors"
                          type="button"
                        >
                          Copy to All
                        </button>
                        <button
                          onClick={() => clearDay(day.id)}
                          className="text-sm text-red-600 hover:text-red-700 font-medium hover:bg-red-50 px-3 py-1 rounded-lg transition-colors"
                          type="button"
                        >
                          Clear
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* Time Slots */}
                <div className="flex-1 space-y-3">
                  {selectedSlots[day.id] && selectedSlots[day.id].length > 0 ? (
                    selectedSlots[day.id].map((slot, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-3 bg-gradient-to-r from-primary-50 to-blue-50 p-3 rounded-lg border border-primary-200"
                      >
                        <select
                          value={slot.start}
                          onChange={(e) =>
                            updateTimeSlot(day.id, index, "start", e.target.value)
                          }
                          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                        >
                          {TIME_SLOTS.map((ts) => (
                            <option key={ts.time} value={ts.time}>
                              {ts.displayTime}
                            </option>
                          ))}
                        </select>

                        <span className="text-gray-500 font-medium">to</span>

                        <select
                          value={slot.end}
                          onChange={(e) =>
                            updateTimeSlot(day.id, index, "end", e.target.value)
                          }
                          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
                        >
                          {TIME_SLOTS.map((ts) => (
                            <option key={ts.time} value={ts.time}>
                              {ts.displayTime}
                            </option>
                          ))}
                        </select>

                        <button
                          onClick={() => removeTimeSlot(day.id, index)}
                          className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                          type="button"
                        >
                          <FiTrash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))
                  ) : (
                    <div className="text-sm text-gray-500 italic py-2">
                      No availability set
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Save Button */}
      <div className="mt-8 flex justify-end gap-3">
        <Button variant="ghost" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-8"
        >
          <FiSave className="w-4 h-4" />
          {saving ? "Saving..." : "Save Availability"}
        </Button>
      </div>
    </div>
  );
}
