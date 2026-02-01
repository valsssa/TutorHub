"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import confetti from "canvas-confetti";
import {
  Calendar,
  Clock,
  CheckCircle,
  X,
  ChevronLeft,
  ChevronRight,
  DollarSign,
  BookOpen,
  MessageSquare,
  Zap,
  Check,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { TutorProfile, Subject } from "@/types";
import { useToast } from "./ToastContainer";
import axios from "axios";
import { bookings } from "@/lib/api";
import type { BookingCreateRequest } from "@/types/booking";
import { getApiBaseUrl } from "@/shared/utils/url";
import { useWebSocket } from "@/hooks/useWebSocket";

interface ModernBookingModalProps {
  tutor: TutorProfile;
  subjects: Subject[];
  onClose: () => void;
  onSuccess: () => void;
}

type BookingStep = 1 | 2 | 3;

interface TimeSlot {
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

export default function ModernBookingModal({
  tutor,
  subjects,
  onClose,
  onSuccess,
}: ModernBookingModalProps) {
  const { showError } = useToast();
  const { lastMessage } = useWebSocket();
  const [step, setStep] = useState<BookingStep>(1);
  const [submitting, setSubmitting] = useState(false);
  
  // Calendar state
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [slotsCache, setSlotsCache] = useState<Record<string, TimeSlot[]>>({});
  
  // Slot conflict state
  const [slotConflict, setSlotConflict] = useState(false);
  
  // Booking state
  const [duration, setDuration] = useState<25 | 50>(50);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  const [bookingData, setBookingData] = useState({
    subject_id: tutor.subjects?.[0]?.subject_id || subjects[0]?.id || 0,
    topic: "",
    notes: "",
  });

  // Trigger confetti animation
  const triggerConfetti = () => {
    const duration = 3000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 9999 };

    function randomInRange(min: number, max: number) {
      return Math.random() * (max - min) + min;
    }

    const interval: NodeJS.Timeout = setInterval(function() {
      const timeLeft = animationEnd - Date.now();
      if (timeLeft <= 0) return clearInterval(interval);

      const particleCount = 50 * (timeLeft / duration);
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
      });
      confetti({
        ...defaults,
        particleCount,
        origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
      });
    }, 250);
  };

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days: (Date | null)[] = [];
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }
    return days;
  }, [currentMonth]);

  // Function to fetch slots for a specific date
  const fetchSlotsForDate = useCallback(async (date: Date, forceRefresh = false) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateKey = `${year}-${month}-${day}`;

    // Use cache unless force refresh
    if (!forceRefresh && slotsCache[dateKey]) {
      setAvailableSlots(slotsCache[dateKey]);
      return;
    }

    setLoadingSlots(true);
    try {
      const startDateStr = `${dateKey}T00:00:00`;
      const endDateStr = `${dateKey}T23:59:59`;

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
        `${API_URL}/api/v1/tutors/${tutor.id}/available-slots?start_date=${startDateStr}&end_date=${endDateStr}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.ok) {
        const slots = await response.json();
        setAvailableSlots(slots);
        setSlotsCache((prev) => ({ ...prev, [dateKey]: slots }));
      } else {
        setAvailableSlots([]);
      }
    } catch {
      setAvailableSlots([]);
    } finally {
      setLoadingSlots(false);
    }
  }, [tutor.id, slotsCache]);

  // Fetch available slots when date is selected
  useEffect(() => {
    if (!selectedDate) {
      setAvailableSlots([]);
      return;
    }
    fetchSlotsForDate(selectedDate);
  }, [selectedDate, fetchSlotsForDate]);

  // Function to refresh slots (clear cache and refetch)
  const refreshSlots = useCallback(() => {
    if (selectedDate) {
      // Clear cache for this date
      const year = selectedDate.getFullYear();
      const month = String(selectedDate.getMonth() + 1).padStart(2, '0');
      const day = String(selectedDate.getDate()).padStart(2, '0');
      const dateKey = `${year}-${month}-${day}`;
      setSlotsCache((prev) => {
        const newCache = { ...prev };
        delete newCache[dateKey];
        return newCache;
      });
      // Force refetch
      fetchSlotsForDate(selectedDate, true);
    }
  }, [selectedDate, fetchSlotsForDate]);

  // Listen for real-time availability updates via WebSocket
  useEffect(() => {
    if (
      lastMessage?.type === "availability_updated" &&
      lastMessage.tutor_profile_id === tutor.id
    ) {
      setSelectedSlot(null);
      refreshSlots();
    }
  }, [lastMessage, tutor.id, refreshSlots]);

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
    setSelectedDate(null);
    setSelectedSlot(null);
  };

  const handleNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
    setSelectedDate(null);
    setSelectedSlot(null);
  };

  const handleDateClick = (date: Date) => {
    if (date < new Date(new Date().setHours(0, 0, 0, 0))) return;
    setSelectedDate(date);
    setSelectedSlot(null);
  };

  const handleSlotSelect = (slot: TimeSlot) => {
    setSelectedSlot(slot.start_time);
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
    return date.toDateString() === today.toDateString();
  };

  const isSelected = (date: Date) => {
    return selectedDate?.toDateString() === date.toDateString();
  };

  const handleNextStep = () => {
    if (step === 1) {
      if (!selectedSlot) {
        showError("Please select a time slot");
        return;
      }
      setStep(2);
    } else if (step === 2) {
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    if (!selectedSlot) return;

    const startDate = new Date(selectedSlot);

    const payload: BookingCreateRequest = {
      tutor_profile_id: tutor.id,
      start_at: startDate.toISOString(),
      duration_minutes: duration,
      lesson_type: "REGULAR",
      subject_id: bookingData.subject_id,
      notes_student: bookingData.notes || undefined,
    };

    setSubmitting(true);
    setSlotConflict(false);
    try {
      await bookings.create(payload);
      setStep(3);
      triggerConfetti();
      setTimeout(() => onSuccess(), 2500);
    } catch (error) {
      const axiosError = axios.isAxiosError(error) ? error : null;
      const responseStatus = axiosError?.response?.status;
      const rawDetail =
        axiosError?.response?.data?.detail ||
        (error instanceof Error ? error.message : "Failed to create booking");
      const errorMessage = rawDetail || "Failed to create booking";

      const lowerDetail = errorMessage.toLowerCase();
      const isSlotConflict =
        responseStatus === 409 ||
        lowerDetail.includes("not available") ||
        lowerDetail.includes("already booked") ||
        lowerDetail.includes("slot") ||
        lowerDetail.includes("conflict") ||
        lowerDetail.includes("availability");

      if (isSlotConflict) {
        setSlotConflict(true);
        setSelectedSlot(null);
        setStep(1);
        refreshSlots();
        showError("This time slot is no longer available. The schedule has been updated.");
      } else {
        showError(errorMessage);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const calculateTotal = () => {
    const hourlyRate = Number(tutor.hourly_rate);
    const sessionRate = (hourlyRate * duration) / 50;
    return sessionRate.toFixed(2);
  };

  const serviceFee = 5.00;

  const selectedSubject = subjects.find((s) => s.id === bookingData.subject_id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl max-h-[90vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-slate-100 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Book Session</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">with {tutor.title}</p>
          </div>
          <button 
            onClick={onClose} 
            className="text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-10rem)]">
          {/* Step 1: Select Time */}
          {step === 1 && (
            <div className="space-y-6">
              {/* Slot Conflict Warning */}
              {slotConflict && (
                <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 flex items-start gap-3">
                  <AlertTriangle size={20} className="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                      Schedule Updated
                    </p>
                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                      The tutor&apos;s availability has changed. Please select a new time slot.
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSlotConflict(false);
                      refreshSlots();
                    }}
                    className="p-1.5 hover:bg-amber-100 dark:hover:bg-amber-900/30 rounded-lg transition-colors"
                    title="Refresh slots"
                  >
                    <RefreshCw size={16} className="text-amber-600 dark:text-amber-400" />
                  </button>
                </div>
              )}

              {/* Duration Toggle */}
              <div>
                <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-3">
                  Session Duration
                </label>
                <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
                  <button
                    onClick={() => setDuration(25)}
                    className={`flex-1 py-3 text-sm font-bold rounded-lg transition-all ${
                      duration === 25 
                        ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' 
                        : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                    }`}
                  >
                    25 mins
                  </button>
                  <button
                    onClick={() => setDuration(50)}
                    className={`flex-1 py-3 text-sm font-bold rounded-lg transition-all ${
                      duration === 50 
                        ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' 
                        : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                    }`}
                  >
                    50 mins
                  </button>
                </div>
              </div>

              {/* Calendar and Time Slots */}
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Calendar */}
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-slate-900 dark:text-white">
                      {MONTHS[currentMonth.getMonth()]} {currentMonth.getFullYear()}
                    </h3>
                    <div className="flex gap-1">
                      <button 
                        onClick={handlePrevMonth} 
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                      >
                        <ChevronLeft size={20} className="text-slate-600 dark:text-slate-400" />
                      </button>
                      <button 
                        onClick={handleNextMonth} 
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                      >
                        <ChevronRight size={20} className="text-slate-600 dark:text-slate-400" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-7 text-center mb-2">
                    {DAYS.map(d => (
                      <div key={d} className="text-xs font-semibold text-slate-400 uppercase tracking-wider py-2">
                        {d}
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-7 gap-1">
                    {calendarDays.map((date, idx) => {
                      if (!date) return <div key={`pad-${idx}`} className="aspect-square" />;

                      const isPast = date < new Date(new Date().setHours(0, 0, 0, 0));
                      const today = isToday(date);
                      const selected = isSelected(date);

                      return (
                        <button
                          key={date.toISOString()}
                          onClick={() => handleDateClick(date)}
                          disabled={isPast}
                          className={`
                            aspect-square rounded-xl flex flex-col items-center justify-center relative transition-all border text-sm
                            ${isPast ? 'text-slate-300 dark:text-slate-700 cursor-not-allowed' : ''}
                            ${selected 
                              ? 'bg-emerald-600 text-white border-emerald-600 shadow-md scale-105 z-10' 
                              : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-100 dark:border-slate-800 hover:border-emerald-400 dark:hover:border-emerald-600'
                            }
                            ${today && !selected ? 'bg-slate-50 dark:bg-slate-800 font-semibold ring-2 ring-emerald-300' : ''}
                          `}
                        >
                          {date.getDate()}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Time Slots */}
                <div className="w-full lg:w-56 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-2xl p-4">
                  <div className="mb-4 pb-4 border-b border-slate-200 dark:border-slate-700">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                        <Clock size={18} className="text-emerald-500" />
                        {selectedDate 
                          ? selectedDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
                          : 'Select a date'
                        }
                      </h4>
                      {selectedDate && (
                        <button
                          onClick={refreshSlots}
                          disabled={loadingSlots}
                          className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
                          title="Refresh available times"
                        >
                          <RefreshCw size={14} className={`text-slate-500 ${loadingSlots ? 'animate-spin' : ''}`} />
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {selectedDate ? 'Select a time to book' : 'Pick a date from calendar'}
                    </p>
                  </div>

                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {loadingSlots ? (
                      <div className="flex justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
                      </div>
                    ) : selectedDate && availableSlots.length > 0 ? (
                      availableSlots.map((slot) => {
                        const isSlotSelected = selectedSlot === slot.start_time;
                        return (
                          <button
                            key={slot.start_time}
                            onClick={() => handleSlotSelect(slot)}
                            className={`
                              w-full py-3 px-4 rounded-xl flex items-center justify-between transition-all border
                              ${isSlotSelected 
                                ? 'bg-emerald-100 dark:bg-emerald-900/30 border-emerald-500 text-emerald-800 dark:text-emerald-300' 
                                : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-emerald-500 hover:shadow-md text-slate-700 dark:text-slate-200'
                              }
                            `}
                          >
                            <span className="font-medium">{formatTime(slot.start_time)}</span>
                            {isSlotSelected && <Check size={16} />}
                          </button>
                        );
                      })
                    ) : selectedDate ? (
                      <div className="text-center py-8 text-slate-400 text-sm">
                        <Calendar className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                        No slots available on this date.
                      </div>
                    ) : (
                      <div className="text-center py-8 text-slate-400 text-sm">
                        <Calendar className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                        Select a date to view times
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Subject Selection */}
              <div>
                <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                  <BookOpen size={16} />
                  Subject
                </label>
                <select
                  value={bookingData.subject_id}
                  onChange={(e) => setBookingData({ ...bookingData, subject_id: Number(e.target.value) })}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                >
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Topic Input */}
              <div>
                <label className="block text-sm font-semibold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                  <MessageSquare size={16} />
                  What would you like to learn? (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g., Calculus basics, Grammar review..."
                  value={bookingData.topic}
                  onChange={(e) => setBookingData({ ...bookingData, topic: e.target.value })}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all"
                />
              </div>
            </div>
          )}

          {/* Step 2: Confirm */}
          {step === 2 && selectedSlot && (
            <div className="space-y-6">
              {/* Session Details Card */}
              <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-800 flex gap-4">
                <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
                  <Calendar size={24} />
                </div>
                <div>
                  <h4 className="font-bold text-slate-900 dark:text-white">Session Details</h4>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{selectedSubject?.name} • {duration} mins</p>
                  <p className="text-sm text-emerald-600 dark:text-emerald-400 mt-1 font-medium">
                    {new Date(selectedSlot).toLocaleString('en-US', {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric',
                      hour: 'numeric',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </p>
                </div>
              </div>

              {/* Pricing Breakdown */}
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Session Rate ({duration} min)</span>
                  <span className="font-medium text-slate-900 dark:text-white">${calculateTotal()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Service Fee</span>
                  <span className="font-medium text-slate-900 dark:text-white">${serviceFee.toFixed(2)}</span>
                </div>
                <div className="border-t border-slate-200 dark:border-slate-800 pt-3 flex justify-between font-bold text-lg">
                  <span className="text-slate-900 dark:text-white">Total</span>
                  <span className="text-emerald-600 dark:text-emerald-400">${(Number(calculateTotal()) + serviceFee).toFixed(2)}</span>
                </div>
              </div>

              {/* Topic Display */}
              {bookingData.topic && (
                <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                  <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Session Topic</p>
                  <p className="text-slate-900 dark:text-white font-medium">{bookingData.topic}</p>
                </div>
              )}

              {/* Info Banner */}
              <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-xl border border-blue-100 dark:border-blue-800/50">
                <p className="text-sm text-blue-800 dark:text-blue-200 font-medium">
                  💡 Your booking will be pending until {tutor.title} confirms. You&apos;ll receive a notification once confirmed.
                </p>
              </div>
            </div>
          )}

          {/* Step 3: Success */}
          {step === 3 && (
            <div className="text-center py-8">
              <div className="w-20 h-20 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-6 animate-in zoom-in duration-300">
                <CheckCircle size={40} />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">Booking Confirmed!</h3>
              <p className="text-slate-500 dark:text-slate-400 mb-8">
                You&apos;re all set. A confirmation has been sent to your email.
              </p>
              <button 
                onClick={onSuccess}
                className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-8 py-3 rounded-xl font-semibold hover:opacity-90 transition-opacity"
              >
                Back to Dashboard
              </button>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {step !== 3 && (
          <div className="p-6 border-t border-slate-100 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95">
            <div className="flex gap-3">
              {step === 2 && (
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 py-3 border border-slate-200 dark:border-slate-700 rounded-xl font-semibold text-slate-900 dark:text-white hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                  Back
                </button>
              )}
              <button
                onClick={handleNextStep}
                disabled={step === 1 ? !selectedSlot : submitting}
                className={`flex-1 py-3 rounded-xl font-bold transition-all flex items-center justify-center gap-2 shadow-lg ${
                  (step === 1 && !selectedSlot) || submitting
                    ? 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-500/20'
                }`}
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                    Booking...
                  </>
                ) : step === 1 ? (
                  <>
                    Continue <ChevronRight size={20} />
                  </>
                ) : (
                  <>
                    <Zap size={20} className="fill-current" />
                    Confirm & Pay
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
