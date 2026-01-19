"use client";

import { useState, useEffect } from "react";
import confetti from "canvas-confetti";
import {
  FiX,
  FiCalendar,
  FiClock,
  FiDollarSign,
  FiBook,
  FiMessageSquare,
  FiCheckCircle,
  FiHeart,
} from "react-icons/fi";
import TimeSlotPicker from "./TimeSlotPicker";
import Button from "./Button";
import Input from "./Input";
import { TutorProfile, Subject } from "@/types";
import { useToast } from "./ToastContainer";

interface ModernBookingModalProps {
  tutor: TutorProfile;
  subjects: Subject[];
  onClose: () => void;
  onSuccess: () => void;
}

type BookingStep = "select-time" | "details" | "confirm" | "success";

export default function ModernBookingModal({
  tutor,
  subjects,
  onClose,
  onSuccess,
}: ModernBookingModalProps) {
  const { showError } = useToast();
  const [step, setStep] = useState<BookingStep>("select-time");
  const [submitting, setSubmitting] = useState(false);
  const [showStickyButton, setShowStickyButton] = useState(false);

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

      if (timeLeft <= 0) {
        return clearInterval(interval);
      }

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

  // Detect scroll for sticky button
  useEffect(() => {
    if (step !== "select-time" && step !== "details" && step !== "confirm") return;
    
    const handleScroll = (e: Event) => {
      const target = e.target as HTMLElement;
      if (target.scrollTop > 100) {
        setShowStickyButton(true);
      } else {
        setShowStickyButton(false);
      }
    };

    const contentEl = document.querySelector('.modal-content');
    contentEl?.addEventListener('scroll', handleScroll);
    return () => contentEl?.removeEventListener('scroll', handleScroll);
  }, [step]);

  const [duration, setDuration] = useState(50); // 25 or 50 minutes only
  const [bookingData, setBookingData] = useState({
    subject_id: tutor.subjects?.[0]?.subject_id || subjects[0]?.id || 0,
    start_time: "",
    end_time: "",
    topic: "",
    notes: "",
  });

  const handleSelectSlot = (startTime: string, endTime: string) => {
    // Calculate end time based on selected duration
    const start = new Date(startTime);
    const calculatedEnd = new Date(start.getTime() + duration * 60000);
    setBookingData((prev) => ({
      ...prev,
      start_time: startTime,
      end_time: calculatedEnd.toISOString()
    }));
  };

  const handleNextStep = () => {
    if (step === "select-time") {
      if (!bookingData.start_time || !bookingData.end_time) {
        showError("Please select a time slot");
        return;
      }
      setStep("details");
    } else if (step === "details") {
      setStep("confirm");
    }
  };

  const handleBack = () => {
    if (step === "details") {
      setStep("select-time");
    } else if (step === "confirm") {
      setStep("details");
    }
  };

  const handleSubmit = async () => {
    const startDate = new Date(bookingData.start_time);
    const endDate = new Date(bookingData.end_time);

    if (startDate >= endDate) {
      showError("End time must be after start time");
      return;
    }

    if (startDate < new Date()) {
      showError("Start time must be in the future");
      return;
    }

    setSubmitting(true);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL;
      if (!API_URL) {
        showError('API configuration error');
        return;
      }
      const token = document.cookie
        .split("; ")
        .find((row) => row.startsWith("token="))
        ?.split("=")[1];

      const response = await fetch(`${API_URL}/api/bookings`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          tutor_profile_id: tutor.id,
          subject_id: bookingData.subject_id,
          start_time: startDate.toISOString(),
          end_time: endDate.toISOString(),
          topic: bookingData.topic || undefined,
          notes: bookingData.notes || undefined,
        }),
      });

      if (response.ok) {
        setStep("success");
        triggerConfetti();
        setTimeout(() => {
          onSuccess();
        }, 2000);
      } else {
        const errorData = await response.json();
        showError(errorData.detail || "Failed to create booking");
      }
    } catch (error) {
      showError("Failed to create booking");
    } finally {
      setSubmitting(false);
    }
  };

  const formatDateTime = (timeString: string) => {
    const date = new Date(timeString);
    return {
      date: date.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
      }),
      time: date.toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      }),
    };
  };

  const calculateDuration = () => {
    if (!bookingData.start_time || !bookingData.end_time) return 0;
    const start = new Date(bookingData.start_time);
    const end = new Date(bookingData.end_time);
    return (end.getTime() - start.getTime()) / (1000 * 60); // minutes
  };

  const calculateTotal = () => {
    const durationHours = calculateDuration() / 60;
    return (Number(tutor.hourly_rate) * durationHours).toFixed(2);
  };

  const selectedSubject = subjects.find((s) => s.id === bookingData.subject_id);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl animate-slideUp">
        {/* Header */}
        <div className="bg-gradient-to-r from-primary-500 to-pink-600 px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-white">Book a Session</h2>
              <p className="text-primary-100 text-sm mt-1">with {tutor.title}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 p-2 rounded-full transition-colors"
              type="button"
            >
              <FiX className="w-6 h-6" />
            </button>
          </div>

          {/* Progress Steps */}
          <div className="flex items-center gap-2 mt-6">
            {[
              { key: "select-time", label: "Select Time" },
              { key: "details", label: "Details" },
              { key: "confirm", label: "Confirm" },
            ].map((stepItem, index) => (
              <div key={stepItem.key} className="flex items-center flex-1">
                <div
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg flex-1 ${
                    step === stepItem.key
                      ? "bg-white/20 text-white"
                      : step === "details" && stepItem.key === "select-time"
                        ? "bg-white/10 text-white/70"
                        : step === "confirm" &&
                            (stepItem.key === "select-time" ||
                              stepItem.key === "details")
                          ? "bg-white/10 text-white/70"
                          : "text-white/50"
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                      step === stepItem.key
                        ? "bg-white text-primary-600"
                        : "bg-white/20"
                    }`}
                  >
                    {index + 1}
                  </div>
                  <span className="text-sm font-medium hidden sm:block">
                    {stepItem.label}
                  </span>
                </div>
                {index < 2 && (
                  <div className="w-8 h-0.5 bg-white/20 mx-1 hidden sm:block" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="modal-content p-6 overflow-y-auto max-h-[calc(90vh-16rem)] scroll-smooth">
          {step === "select-time" && (
            <div className="space-y-4 animate-fadeIn">
              <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-xl p-4 mb-4">
                <p className="text-sm text-blue-900 flex items-center gap-2 font-medium">
                  <FiClock className="w-4 h-4" />
                  Choose your session length: 25 or 50 min
                </p>
                <p className="text-xs text-blue-700 mt-2">
                  💡 All sessions last 25 or 50 minutes only.
                </p>
              </div>

              {/* Duration Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Session Duration
                </label>
                <div className="flex gap-3">
                  <Button
                    variant={duration === 25 ? "primary" : "ghost"}
                    onClick={() => setDuration(25)}
                    className="flex-1 py-4 border-2"
                    type="button"
                  >
                    <div className="flex flex-col items-center">
                      <span className="text-lg font-bold">25 minutes</span>
                      <span className="text-xs opacity-75">Quick Session</span>
                    </div>
                  </Button>
                  <Button
                    variant={duration === 50 ? "primary" : "ghost"}
                    onClick={() => setDuration(50)}
                    className="flex-1 py-4 border-2"
                    type="button"
                  >
                    <div className="flex flex-col items-center">
                      <span className="text-lg font-bold">50 minutes</span>
                      <span className="text-xs opacity-75">Full Lesson</span>
                    </div>
                  </Button>
                </div>
              </div>

              <TimeSlotPicker
                tutorId={tutor.id}
                onSelectSlot={handleSelectSlot}
                selectedStartTime={bookingData.start_time}
              />
            </div>
          )}

          {step === "success" && (
            <div className="space-y-6 animate-scaleIn text-center py-8">
              <div className="relative">
                <div className="w-24 h-24 bg-gradient-to-br from-green-100 to-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce-soft">
                  <FiCheckCircle className="w-12 h-12 text-green-600" />
                </div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-32 h-32 bg-green-200 rounded-full opacity-20 animate-ping" />
                </div>
              </div>
              
              <div>
                <h3 className="text-3xl font-bold text-gray-900 mb-3">
                  🎉 Booking Successful!
                </h3>
                <p className="text-lg text-gray-600 mb-2">
                  Your session with <span className="font-semibold text-primary-600">{tutor.title}</span> has been requested
                </p>
                <p className="text-sm text-gray-500">
                  You&apos;ll receive a notification once the tutor confirms your booking
                </p>
              </div>

              <div className="bg-gradient-to-br from-primary-50 to-pink-50 rounded-2xl p-6 border border-primary-100">
                <div className="flex items-center justify-center gap-2 mb-3">
                  <FiHeart className="w-5 h-5 text-primary-500 animate-pulse" />
                  <p className="text-sm font-semibold text-gray-900">What&apos;s Next?</p>
                </div>
                <ul className="text-sm text-gray-700 space-y-2 text-left max-w-md mx-auto">
                  <li className="flex items-start gap-2">
                    <span className="text-primary-500 font-bold">1.</span>
                    <span>Check your email for booking confirmation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary-500 font-bold">2.</span>
                    <span>Tutor will review and confirm within 24 hours</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-primary-500 font-bold">3.</span>
                    <span>Prepare any questions or materials for your session</span>
                  </li>
                </ul>
              </div>
            </div>
          )}

          {step === "details" && (
            <div className="space-y-6 animate-fadeIn">
              {/* Selected Time Display */}
              {bookingData.start_time && (
                <div className="bg-gradient-to-br from-primary-50 to-blue-50 rounded-lg p-4 border border-primary-200">
                  <div className="flex items-center gap-3">
                    <div className="bg-primary-600 p-3 rounded-lg">
                      <FiCalendar className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Selected Time</p>
                      <p className="font-semibold text-gray-900">
                        {formatDateTime(bookingData.start_time).date}
                      </p>
                      <p className="text-sm text-primary-600 font-medium">
                        {formatDateTime(bookingData.start_time).time} -{" "}
                        {formatDateTime(bookingData.end_time).time} ({calculateDuration()} min)
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Subject Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <FiBook className="w-4 h-4" />
                  Subject
                </label>
                <select
                  value={bookingData.subject_id}
                  onChange={(e) =>
                    setBookingData({
                      ...bookingData,
                      subject_id: Number(e.target.value),
                    })
                  }
                  className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 focus:outline-none focus:border-primary-500 transition-colors"
                  required
                >
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Topic */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <FiMessageSquare className="w-4 h-4" />
                  Session Topic
                </label>
                <input
                  type="text"
                  placeholder="What would you like to learn?"
                  value={bookingData.topic}
                  onChange={(e) =>
                    setBookingData({ ...bookingData, topic: e.target.value })
                  }
                  className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 focus:outline-none focus:border-primary-500 transition-colors"
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <FiMessageSquare className="w-4 h-4" />
                  Additional Notes (Optional)
                </label>
                <textarea
                  rows={4}
                  value={bookingData.notes}
                  onChange={(e) =>
                    setBookingData({ ...bookingData, notes: e.target.value })
                  }
                  className="w-full rounded-lg border-2 border-gray-200 px-4 py-3 focus:outline-none focus:border-primary-500 transition-colors resize-none"
                  placeholder="Any specific requirements, questions, or learning goals?"
                />
              </div>
            </div>
          )}

          {step === "confirm" && (
            <div className="space-y-6 animate-fadeIn">
              {/* Success Icon */}
              <div className="text-center py-6">
                <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FiCheckCircle className="w-10 h-10 text-green-600" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Review Your Booking
                </h3>
                <p className="text-gray-600">
                  Please review the details before confirming
                </p>
              </div>

              {/* Booking Summary */}
              <div className="bg-gray-50 rounded-lg p-6 space-y-4">
                <div className="flex items-start justify-between pb-4 border-b border-gray-200">
                  <div>
                    <p className="text-sm text-gray-600">Tutor</p>
                    <p className="font-semibold text-gray-900">{tutor.title}</p>
                  </div>
                </div>

                <div className="flex items-start justify-between pb-4 border-b border-gray-200">
                  <div>
                    <p className="text-sm text-gray-600 flex items-center gap-2">
                      <FiCalendar className="w-4 h-4" />
                      Date & Time
                    </p>
                    <p className="font-medium text-gray-900 mt-1">
                      {formatDateTime(bookingData.start_time).date}
                    </p>
                    <p className="text-sm text-primary-600 font-medium">
                      {formatDateTime(bookingData.start_time).time} -{" "}
                      {formatDateTime(bookingData.end_time).time}
                    </p>
                  </div>
                  <span className="text-sm font-medium text-gray-600">
                    {calculateDuration()} min
                  </span>
                </div>

                <div className="flex items-start justify-between pb-4 border-b border-gray-200">
                  <div>
                    <p className="text-sm text-gray-600 flex items-center gap-2">
                      <FiBook className="w-4 h-4" />
                      Subject
                    </p>
                    <p className="font-medium text-gray-900 mt-1">
                      {selectedSubject?.name}
                    </p>
                  </div>
                </div>

                {bookingData.topic && (
                  <div className="pb-4 border-b border-gray-200">
                    <p className="text-sm text-gray-600 mb-1">Topic</p>
                    <p className="text-gray-900">{bookingData.topic}</p>
                  </div>
                )}

                {bookingData.notes && (
                  <div className="pb-4 border-b border-gray-200">
                    <p className="text-sm text-gray-600 mb-1">Notes</p>
                    <p className="text-gray-700 text-sm">{bookingData.notes}</p>
                  </div>
                )}

                {/* Pricing */}
                <div className="bg-white rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">
                      Session Rate (${tutor.hourly_rate} / 50 min)
                    </span>
                    <span className="text-gray-900">${tutor.hourly_rate}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">
                      Session Duration
                    </span>
                    <span className="text-gray-900">
                      {calculateDuration()} minutes
                    </span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-gray-200">
                    <span className="font-semibold text-gray-900 flex items-center gap-2">
                      <FiDollarSign className="w-5 h-5" />
                      Total Amount
                    </span>
                    <span className="text-2xl font-bold text-primary-600">
                      ${calculateTotal()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  💡 Your booking will be pending until the tutor confirms. You&apos;ll be
                  notified once confirmed.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        {step !== "success" && (
          <>
            <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-200">
              <div>
                {step !== "select-time" && (
                  <Button variant="ghost" onClick={handleBack} disabled={submitting}>
                    Back
                  </Button>
                )}
              </div>
              <div className="flex gap-3">
                <Button variant="ghost" onClick={onClose} disabled={submitting}>
                  Cancel
                </Button>
                {step === "confirm" ? (
                  <Button
                    variant="primary"
                    onClick={handleSubmit}
                    disabled={submitting}
                    className="px-8 shadow-lg hover:shadow-xl"
                  >
                    {submitting ? "Booking..." : "✨ Confirm Booking"}
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    onClick={handleNextStep}
                    disabled={
                      step === "select-time" &&
                      (!bookingData.start_time || !bookingData.end_time)
                    }
                    className="px-8"
                  >
                    Next →
                  </Button>
                )}
              </div>
            </div>

            {/* Mobile Sticky CTA */}
            {showStickyButton && (
              <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-lg z-50 animate-slideUp">
                <Button
                  variant="primary"
                  onClick={step === "confirm" ? handleSubmit : handleNextStep}
                  disabled={
                    submitting ||
                    (step === "select-time" &&
                      (!bookingData.start_time || !bookingData.end_time))
                  }
                  className="w-full shadow-lg"
                >
                  {step === "confirm" 
                    ? (submitting ? "Booking..." : "✨ Confirm Booking")
                    : "Next →"
                  }
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      <style jsx global>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }

        .animate-slideUp {
          animation: slideUp 0.4s ease-out;
        }
      `}</style>
    </div>
  );
}
