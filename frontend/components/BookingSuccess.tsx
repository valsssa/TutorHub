"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  CheckCircle,
  Calendar,
  Clock,
  User,
  Mail,
  ArrowRight,
  Copy,
  Check,
} from "lucide-react";
import Modal from "./Modal";
import Button from "./Button";
import { useState } from "react";

interface BookingDetails {
  bookingId: number | string;
  tutorName: string;
  tutorAvatar?: string;
  subject: string;
  date: Date;
  duration: number; // in minutes
  price: number;
  currency?: string;
}

interface BookingSuccessProps {
  isOpen: boolean;
  onClose: () => void;
  booking: BookingDetails;
  onViewBookings?: () => void;
  onBookAnother?: () => void;
}

export default function BookingSuccess({
  isOpen,
  onClose,
  booking,
  onViewBookings,
  onBookAnother,
}: BookingSuccessProps) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);

  const {
    bookingId,
    tutorName,
    subject,
    date,
    duration,
    price,
    currency = "USD",
  } = booking;

  // Format date and time
  const formattedDate = date.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  const formattedTime = date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  const endTime = new Date(date.getTime() + duration * 60000);
  const formattedEndTime = endTime.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });

  // Copy booking ID
  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(String(bookingId));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textArea = document.createElement("textarea");
      textArea.value = String(bookingId);
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand("copy");
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleViewBookings = () => {
    if (onViewBookings) {
      onViewBookings();
    } else {
      router.push("/bookings");
    }
    onClose();
  };

  const handleBookAnother = () => {
    if (onBookAnother) {
      onBookAnother();
    } else {
      router.push("/tutors");
    }
    onClose();
  };

  // Add to calendar (generates ICS data)
  const handleAddToCalendar = () => {
    const event = {
      title: `Lesson with ${tutorName} - ${subject}`,
      start: date,
      end: endTime,
      description: `Booking ID: ${bookingId}\nSubject: ${subject}\nTutor: ${tutorName}`,
    };

    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//EduConnect//Booking//EN
BEGIN:VEVENT
UID:${bookingId}@educonnect.com
DTSTAMP:${formatICSDate(new Date())}
DTSTART:${formatICSDate(event.start)}
DTEND:${formatICSDate(event.end)}
SUMMARY:${event.title}
DESCRIPTION:${event.description.replace(/\n/g, "\\n")}
END:VEVENT
END:VCALENDAR`;

    const blob = new Blob([icsContent], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `lesson-${bookingId}.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Booking Confirmed!"
      size="md"
      footer={
        <div className="flex flex-col sm:flex-row gap-3">
          <Button
            variant="primary"
            onClick={handleViewBookings}
            className="flex-1"
          >
            View My Bookings
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
          <Button
            variant="secondary"
            onClick={handleBookAnother}
            className="flex-1"
          >
            Book Another Lesson
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center animate-in zoom-in-50 duration-300">
            <CheckCircle className="w-10 h-10 text-emerald-500" />
          </div>
        </div>

        {/* Booking Reference */}
        <div className="text-center">
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
            Booking Reference
          </p>
          <div className="inline-flex items-center gap-2 bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded-lg">
            <code className="text-lg font-mono font-bold text-slate-900 dark:text-white">
              #{bookingId}
            </code>
            <button
              onClick={handleCopyId}
              className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors"
              aria-label="Copy booking ID"
            >
              {copied ? (
                <Check className="w-4 h-4 text-emerald-500" />
              ) : (
                <Copy className="w-4 h-4 text-slate-400" />
              )}
            </button>
          </div>
        </div>

        {/* Booking Details Card */}
        <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 space-y-4">
          {/* Tutor */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
              <User className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Tutor</p>
              <p className="font-semibold text-slate-900 dark:text-white">
                {tutorName}
              </p>
            </div>
          </div>

          {/* Subject */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <span className="text-lg">📚</span>
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Subject</p>
              <p className="font-semibold text-slate-900 dark:text-white">
                {subject}
              </p>
            </div>
          </div>

          {/* Date & Time */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
              <Calendar className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-slate-500 dark:text-slate-400">Date & Time</p>
              <p className="font-semibold text-slate-900 dark:text-white">
                {formattedDate}
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-300">
                {formattedTime} - {formattedEndTime} ({duration} min)
              </p>
            </div>
          </div>

          {/* Price */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-200 dark:border-slate-700">
            <span className="text-slate-600 dark:text-slate-400">Total Paid</span>
            <span className="text-lg font-bold text-slate-900 dark:text-white">
              {new Intl.NumberFormat("en-US", {
                style: "currency",
                currency,
              }).format(price)}
            </span>
          </div>
        </div>

        {/* What's Next Section */}
        <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4">
          <h4 className="font-semibold text-emerald-900 dark:text-emerald-100 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            What happens next?
          </h4>
          <ul className="space-y-2 text-sm text-emerald-800 dark:text-emerald-200">
            <li className="flex items-start gap-2">
              <Mail className="w-4 h-4 mt-0.5 shrink-0" />
              <span>
                A confirmation email has been sent to your inbox with lesson details
              </span>
            </li>
            <li className="flex items-start gap-2">
              <Calendar className="w-4 h-4 mt-0.5 shrink-0" />
              <span>
                You&apos;ll receive a meeting link 15 minutes before your lesson
              </span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>
                You can reschedule or cancel for free up to 24 hours before
              </span>
            </li>
          </ul>
        </div>

        {/* Add to Calendar */}
        <button
          onClick={handleAddToCalendar}
          className="w-full flex items-center justify-center gap-2 py-3 text-sm font-medium text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg transition-colors"
        >
          <Calendar className="w-4 h-4" />
          Add to Calendar
        </button>
      </div>
    </Modal>
  );
}

// Helper function to format date for ICS file
function formatICSDate(date: Date): string {
  return date
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d{3}/, "");
}
