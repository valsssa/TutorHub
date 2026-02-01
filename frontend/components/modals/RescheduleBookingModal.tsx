"use client";

/**
 * Modal for rescheduling a booking
 * Uses base Modal component for consistent UX
 */

import { useState, useEffect } from "react";
import { Calendar, Clock, AlertCircle } from "lucide-react";
import Modal from "@/components/Modal";
import Button from "@/components/Button";
import { BookingDTO } from "@/types/booking";

interface RescheduleBookingModalProps {
  booking: BookingDTO | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (newStartTime: string) => void;
}

export default function RescheduleBookingModal({
  booking,
  isOpen,
  onClose,
  onConfirm,
}: RescheduleBookingModalProps) {
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isOpen && booking) {
      // Pre-fill with current booking date/time
      // Use local date components to avoid timezone conversion issues
      const currentStart = new Date(booking.start_at);
      const year = currentStart.getFullYear();
      const month = String(currentStart.getMonth() + 1).padStart(2, '0');
      const day = String(currentStart.getDate()).padStart(2, '0');
      const dateStr = `${year}-${month}-${day}`;
      const timeStr = currentStart.toTimeString().slice(0, 5);
      setSelectedDate(dateStr);
      setSelectedTime(timeStr);
    }
  }, [isOpen, booking]);

  if (!booking) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedDate || !selectedTime) {
      return;
    }

    setIsSubmitting(true);
    try {
      const newStartTime = `${selectedDate}T${selectedTime}:00`;
      await onConfirm(newStartTime);
      onClose();
    } catch (error) {
      // Error handling is done in parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentStart = new Date(booking.start_at);
  const currentEnd = new Date(booking.end_at);
  const duration = Math.round((currentEnd.getTime() - currentStart.getTime()) / 60000);

  // Calculate minimum date (tomorrow) using local date components
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minYear = tomorrow.getFullYear();
  const minMonth = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const minDay = String(tomorrow.getDate()).padStart(2, '0');
  const minDate = `${minYear}-${minMonth}-${minDay}`;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Reschedule Booking"
      size="md"
      closeOnBackdropClick={!isSubmitting}
      footer={
        <div className="flex flex-col-reverse sm:flex-row gap-3">
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={isSubmitting}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            form="reschedule-form"
            variant="primary"
            disabled={isSubmitting || !selectedDate || !selectedTime}
            isLoading={isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? "Rescheduling..." : "Confirm Reschedule"}
          </Button>
        </div>
      }
    >
      {/* Current Booking Info */}
      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
        <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
          Current Schedule
        </h3>
        <div className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
              <Calendar className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <span>{currentStart.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center">
              <Clock className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <span>
              {currentStart.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -{" "}
              {currentEnd.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} ({duration} min)
            </span>
          </div>
        </div>
      </div>

      {/* Form */}
      <form id="reschedule-form" onSubmit={handleSubmit} className="space-y-5">
        {/* Date Selection */}
        <div>
          <label
            htmlFor="reschedule-date"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
          >
            New Date
          </label>
          <input
            id="reschedule-date"
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            min={minDate}
            required
            className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all min-h-[44px]"
          />
          <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
            Must be at least 24 hours in advance
          </p>
        </div>

        {/* Time Selection */}
        <div>
          <label
            htmlFor="reschedule-time"
            className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
          >
            New Time
          </label>
          <input
            id="reschedule-time"
            type="time"
            value={selectedTime}
            onChange={(e) => setSelectedTime(e.target.value)}
            required
            className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all min-h-[44px]"
          />
          <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
            Duration will remain {duration} minutes
          </p>
        </div>

        {/* Info Message */}
        <div className="flex gap-3 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl">
          <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-800 dark:text-amber-200">
            The tutor will be notified of this reschedule request and may need to confirm the new time.
          </p>
        </div>
      </form>
    </Modal>
  );
}
