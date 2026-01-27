"use client";

import { useState, useEffect } from "react";
import { X } from "lucide-react";
import {
  User,
  Calendar,
  RotateCw,
  ArrowRight,
  Clock,
  ChevronDown,
} from "lucide-react";
import { bookings, availability } from "@/lib/api";
import { useToast } from "@/components/ToastContainer";

interface ScheduleManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: "Lesson" | "Time off" | "Extra slots";
}

export default function ScheduleManagerModal({
  isOpen,
  onClose,
  initialTab = "Lesson",
}: ScheduleManagerModalProps) {
  const { showSuccess, showError } = useToast();
  const [activeTab, setActiveTab] = useState<
    "Lesson" | "Time off" | "Extra slots"
  >(initialTab);
  const [lessonType, setLessonType] = useState<"Single" | "Weekly">("Single");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Time off state
  const [timeOffTitle, setTimeOffTitle] = useState("Busy");
  const [isAllDay, setIsAllDay] = useState(false);

  // Form state
  const [studentName, setStudentName] = useState("");
  const [lessonDuration, setLessonDuration] = useState("50");
  const [lessonDate, setLessonDate] = useState("");
  const [lessonTime, setLessonTime] = useState("20:00");

  // Time off form state
  const [startDate, setStartDate] = useState("");
  const [startTime, setStartTime] = useState("20:00");
  const [endDate, setEndDate] = useState("");
  const [endTime, setEndTime] = useState("21:00");

  // Extra slots state
  const [extraStartDate, setExtraStartDate] = useState("");
  const [extraStartTime, setExtraStartTime] = useState("20:00");
  const [extraEndDate, setExtraEndDate] = useState("");
  const [extraEndTime, setExtraEndTime] = useState("21:00");

  // Update active tab when modal opens or initialTab changes
  useEffect(() => {
    if (isOpen && initialTab) {
      setActiveTab(initialTab);
    }
  }, [isOpen, initialTab]);

  const handleScheduleLesson = async () => {
    if (!studentName.trim()) {
      showError("Please enter a student name");
      return;
    }
    if (!lessonDate) {
      showError("Please select a date");
      return;
    }

    setIsSubmitting(true);
    try {
      const startDateTime = new Date(`${lessonDate}T${lessonTime}:00`);

      await bookings.create({
        tutor_profile_id: 0,
        start_at: startDateTime.toISOString(),
        duration_minutes: parseInt(lessonDuration),
        notes_student: `Lesson with ${studentName}, Type: ${lessonType}`,
      });

      showSuccess("Lesson scheduled successfully");
      onClose();
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to schedule lesson");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBookTimeOff = async () => {
    if (!startDate || !endDate) {
      showError("Please select start and end dates");
      return;
    }

    setIsSubmitting(true);
    try {
      const startDateTime = isAllDay
        ? new Date(`${startDate}T00:00:00`)
        : new Date(`${startDate}T${startTime}:00`);
      const endDateTime = isAllDay
        ? new Date(`${endDate}T23:59:59`)
        : new Date(`${endDate}T${endTime}:00`);

      showSuccess(`Time off booked: ${timeOffTitle} from ${startDateTime.toLocaleString()} to ${endDateTime.toLocaleString()}`);
      onClose();
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to book time off");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAddExtraSlots = async () => {
    if (!extraStartDate || !extraEndDate) {
      showError("Please select start and end dates");
      return;
    }

    setIsSubmitting(true);
    try {
      const startDateTime = new Date(`${extraStartDate}T${extraStartTime}:00`);
      const dayOfWeek = startDateTime.getDay();

      await availability.createAvailability({
        day_of_week: dayOfWeek,
        start_time: extraStartTime + ":00",
        end_time: extraEndTime + ":00",
        is_recurring: false,
      });

      showSuccess("Extra availability slots added successfully");
      onClose();
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to add extra slots");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="schedule-modal-title"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white dark:bg-slate-900 rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
            <div>
              <h2
                id="schedule-modal-title"
                className="text-2xl font-bold text-slate-900 dark:text-white"
              >
                Schedule Management
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Manage your lessons, time off, and availability
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <X size={20} className="text-slate-400" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Tabs */}
            <div className="flex border-b border-slate-200 dark:border-slate-700 mb-6">
              {["Lesson", "Time off", "Extra slots"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as any)}
                  className={`px-4 py-3 text-sm font-medium transition-all relative ${
                    activeTab === tab
                      ? "text-slate-900 dark:text-white"
                      : "text-slate-500 hover:text-slate-700 dark:hover:text-slate-300"
                  }`}
                >
                  {tab}
                  {activeTab === tab && (
                    <span className="absolute bottom-0 left-0 w-full h-0.5 rounded-t-full bg-emerald-500"></span>
                  )}
                </button>
              ))}
            </div>

            {activeTab === "Lesson" && (
              <div className="space-y-5 animate-in fade-in duration-300">
                {/* Student Input */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Student
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                      <User size={18} />
                    </div>
                    <input
                      type="text"
                      placeholder="Add student"
                      value={studentName}
                      onChange={(e) => setStudentName(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all text-slate-900 dark:text-white placeholder-slate-400"
                    />
                  </div>
                </div>

                {/* Lesson Type */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Lesson type
                  </label>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setLessonType("Single")}
                      className={`flex-1 flex items-center justify-center gap-2 py-2.5 border rounded-xl text-sm font-medium transition-all ${
                        lessonType === "Single"
                          ? "border-emerald-500 ring-1 ring-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20 text-slate-900 dark:text-white"
                          : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-600"
                      }`}
                    >
                      <Calendar size={16} /> Single
                    </button>
                    <button
                      onClick={() => setLessonType("Weekly")}
                      className={`flex-1 flex items-center justify-center gap-2 py-2.5 border rounded-xl text-sm font-medium transition-all ${
                        lessonType === "Weekly"
                          ? "border-emerald-500 ring-1 ring-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20 text-slate-900 dark:text-white"
                          : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300 dark:hover:border-slate-600"
                      }`}
                    >
                      <RotateCw size={16} /> Weekly
                    </button>
                  </div>
                </div>

                {/* Date and Time */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Date and time
                  </label>
                  <div className="space-y-3">
                    <select
                      value={lessonDuration}
                      onChange={(e) => setLessonDuration(e.target.value)}
                      className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer"
                    >
                      <option value="50">50 minutes (Standard lesson)</option>
                      <option value="25">25 minutes (Trial lesson)</option>
                    </select>

                    <div className="flex items-center gap-3">
                      <div className="relative flex-1">
                        <input
                          type="date"
                          value={lessonDate}
                          onChange={(e) => setLessonDate(e.target.value)}
                          className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                        />
                      </div>
                      <ArrowRight
                        size={16}
                        className="text-slate-400 shrink-0"
                      />
                      <div className="relative w-1/3">
                        <select
                          value={lessonTime}
                          onChange={(e) => setLessonTime(e.target.value)}
                          className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer text-center"
                        >
                          {Array.from({ length: 24 }, (_, i) => (
                            <option
                              key={i}
                              value={`${i.toString().padStart(2, "0")}:00`}
                            >
                              {i.toString().padStart(2, "0")}:00
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <button
                  onClick={handleScheduleLesson}
                  disabled={isSubmitting}
                  className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-400 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 mt-4 active:scale-[0.98]"
                >
                  {isSubmitting ? "Scheduling..." : "Schedule lesson"}
                </button>
              </div>
            )}

            {activeTab === "Time off" && (
              <div className="space-y-5 animate-in fade-in duration-300">
                {/* Title Input */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Title
                  </label>
                  <input
                    type="text"
                    value={timeOffTitle}
                    onChange={(e) => setTimeOffTitle(e.target.value)}
                    placeholder="Busy"
                    className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all text-slate-900 dark:text-white placeholder-slate-400"
                  />
                  <p className="text-xs text-slate-500 mt-1.5">
                    Visible only to you
                  </p>
                </div>

                {/* Starts */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Starts
                  </label>
                  <div className="flex gap-3">
                    <div className="relative flex-1">
                      <input
                        type="date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                      />
                    </div>
                    <div className={`relative ${isAllDay ? "hidden" : "w-1/3"}`}>
                      <select
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer"
                      >
                        {Array.from({ length: 48 }, (_, i) => {
                          const hour = Math.floor(i / 2);
                          const minute = i % 2 === 0 ? "00" : "30";
                          return (
                            <option
                              key={i}
                              value={`${hour.toString().padStart(2, "0")}:${minute}`}
                            >
                              {hour.toString().padStart(2, "0")}:{minute}
                            </option>
                          );
                        })}
                      </select>
                      <ChevronDown
                        size={14}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Ends */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Ends
                  </label>
                  <div className="flex gap-3">
                    <div className="relative flex-1">
                      <input
                        type="date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                      />
                    </div>
                    <div className={`relative ${isAllDay ? "hidden" : "w-1/3"}`}>
                      <select
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer"
                      >
                        {Array.from({ length: 48 }, (_, i) => {
                          const hour = Math.floor(i / 2);
                          const minute = i % 2 === 0 ? "00" : "30";
                          return (
                            <option
                              key={i}
                              value={`${hour.toString().padStart(2, "0")}:${minute}`}
                            >
                              {hour.toString().padStart(2, "0")}:{minute}
                            </option>
                          );
                        })}
                      </select>
                      <ChevronDown
                        size={14}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                      />
                    </div>
                  </div>
                </div>

                {/* All day checkbox */}
                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="all-day"
                    checked={isAllDay}
                    onChange={(e) => setIsAllDay(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-emerald-500 focus:ring-emerald-500"
                  />
                  <label
                    htmlFor="all-day"
                    className="text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer select-none"
                  >
                    All day
                  </label>
                </div>

                {/* Submit Button */}
                <button
                  onClick={handleBookTimeOff}
                  disabled={isSubmitting}
                  className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-400 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 mt-4 active:scale-[0.98]"
                >
                  {isSubmitting ? "Booking..." : "Book time off"}
                </button>
              </div>
            )}

            {activeTab === "Extra slots" && (
              <div className="space-y-5 animate-in fade-in duration-300">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-base">
                    Add extra slots
                  </h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Choose time slots up to 24 hours long.
                  </p>
                </div>

                {/* Starts */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Starts
                  </label>
                  <div className="flex gap-3">
                    <div className="relative flex-1">
                      <input
                        type="date"
                        value={extraStartDate}
                        onChange={(e) => setExtraStartDate(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                      />
                    </div>
                    <div className="relative w-1/3">
                      <select
                        value={extraStartTime}
                        onChange={(e) => setExtraStartTime(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer"
                      >
                        {Array.from({ length: 48 }, (_, i) => {
                          const hour = Math.floor(i / 2);
                          const minute = i % 2 === 0 ? "00" : "30";
                          return (
                            <option
                              key={i}
                              value={`${hour.toString().padStart(2, "0")}:${minute}`}
                            >
                              {hour.toString().padStart(2, "0")}:{minute}
                            </option>
                          );
                        })}
                      </select>
                      <ChevronDown
                        size={14}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Ends */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Ends
                  </label>
                  <div className="flex gap-3">
                    <div className="relative flex-1">
                      <input
                        type="date"
                        value={extraEndDate}
                        onChange={(e) => setExtraEndDate(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all"
                      />
                    </div>
                    <div className="relative w-1/3">
                      <select
                        value={extraEndTime}
                        onChange={(e) => setExtraEndTime(e.target.value)}
                        className="w-full px-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-all appearance-none cursor-pointer"
                      >
                        {Array.from({ length: 48 }, (_, i) => {
                          const hour = Math.floor(i / 2);
                          const minute = i % 2 === 0 ? "00" : "30";
                          return (
                            <option
                              key={i}
                              value={`${hour.toString().padStart(2, "0")}:${minute}`}
                            >
                              {hour.toString().padStart(2, "0")}:{minute}
                            </option>
                          );
                        })}
                      </select>
                      <ChevronDown
                        size={14}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                <button
                  onClick={handleAddExtraSlots}
                  disabled={isSubmitting}
                  className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-400 disabled:cursor-not-allowed text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2 mt-4 active:scale-[0.98]"
                >
                  {isSubmitting ? "Adding..." : "Add"}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
