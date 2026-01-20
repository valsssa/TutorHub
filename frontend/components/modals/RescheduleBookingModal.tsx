"use client";

import { useState, useEffect } from "react";
import { FiX, FiCalendar, FiClock } from "react-icons/fi";
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

  if (!isOpen || !booking) return null;

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
  // to avoid timezone conversion issues with toISOString()
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minYear = tomorrow.getFullYear();
  const minMonth = String(tomorrow.getMonth() + 1).padStart(2, '0');
  const minDay = String(tomorrow.getDate()).padStart(2, '0');
  const minDate = `${minYear}-${minMonth}-${minDay}`;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Reschedule Booking</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isSubmitting}
          >
            <FiX className="w-6 h-6" />
          </button>
        </div>

        {/* Current Booking Info */}
        <div className="p-6 bg-blue-50 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Current Schedule</h3>
          <div className="space-y-1 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <FiCalendar className="w-4 h-4" />
              <span>{currentStart.toLocaleDateString()}</span>
            </div>
            <div className="flex items-center gap-2">
              <FiClock className="w-4 h-4" />
              <span>
                {currentStart.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} -{" "}
                {currentEnd.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} ({duration} min)
              </span>
            </div>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Date Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={minDate}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
            <p className="mt-1 text-xs text-gray-500">
              Must be at least 24 hours in advance
            </p>
          </div>

          {/* Time Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Time
            </label>
            <input
              type="time"
              value={selectedTime}
              onChange={(e) => setSelectedTime(e.target.value)}
              required
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            />
            <p className="mt-1 text-xs text-gray-500">
              Duration will remain {duration} minutes
            </p>
          </div>

          {/* Info Message */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              <strong>Note:</strong> The tutor will be notified of this reschedule request and may need to confirm the new time.
            </p>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
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
              variant="primary"
              disabled={isSubmitting || !selectedDate || !selectedTime}
              className="flex-1"
            >
              {isSubmitting ? "Rescheduling..." : "Confirm Reschedule"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
