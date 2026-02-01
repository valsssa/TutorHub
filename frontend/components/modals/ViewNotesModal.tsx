"use client";

import { FiX, FiFileText, FiUser, FiBook } from "react-icons/fi";
import Button from "@/components/Button";
import { BookingDTO } from "@/types/booking";

interface ViewNotesModalProps {
  booking: BookingDTO | null;
  isOpen: boolean;
  onClose: () => void;
  userRole: "student" | "tutor" | "admin" | "owner";
}

export default function ViewNotesModal({
  booking,
  isOpen,
  onClose,
  userRole,
}: ViewNotesModalProps) {
  if (!isOpen || !booking) return null;

  const hasNotes = booking.notes_student || booking.notes_tutor || booking.topic;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <FiFileText className="w-6 h-6 text-primary-600" />
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Booking Notes</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
          >
            <FiX className="w-6 h-6" />
          </button>
        </div>

        {/* Booking Info */}
        <div className="p-6 bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-slate-600 dark:text-slate-400">Subject:</span>
              <span className="ml-2 font-medium text-slate-900 dark:text-white">
                {booking.subject_name || "N/A"}
              </span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Date:</span>
              <span className="ml-2 font-medium text-slate-900 dark:text-white">
                {new Date(booking.start_at).toLocaleDateString()}
              </span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Tutor:</span>
              <span className="ml-2 font-medium text-slate-900 dark:text-white">
                {booking.tutor.name}
              </span>
            </div>
            <div>
              <span className="text-slate-600 dark:text-slate-400">Student:</span>
              <span className="ml-2 font-medium text-slate-900 dark:text-white">
                {booking.student.name}
              </span>
            </div>
          </div>
        </div>

        {/* Notes Content */}
        <div className="p-6 space-y-6">
          {/* Topic */}
          {booking.topic && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <FiBook className="w-5 h-5 text-blue-600" />
                <h3 className="font-semibold text-slate-900 dark:text-white">Session Topic</h3>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">{booking.topic}</p>
              </div>
            </div>
          )}

          {/* Student Notes */}
          {booking.notes_student && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <FiUser className="w-5 h-5 text-green-600" />
                <h3 className="font-semibold text-slate-900 dark:text-white">Student Notes</h3>
                {userRole === "student" && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                    Your notes
                  </span>
                )}
              </div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                  {booking.notes_student}
                </p>
              </div>
            </div>
          )}

          {/* Tutor Notes */}
          {booking.notes_tutor && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <FiUser className="w-5 h-5 text-purple-600" />
                <h3 className="font-semibold text-slate-900 dark:text-white">Tutor Notes</h3>
                {userRole === "tutor" && (
                  <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                    Your notes
                  </span>
                )}
              </div>
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                  {booking.notes_tutor}
                </p>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!hasNotes && (
            <div className="text-center py-12">
              <FiFileText className="w-16 h-16 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">No Notes Available</h3>
              <p className="text-slate-600 dark:text-slate-400">
                No notes have been added to this booking yet.
              </p>
            </div>
          )}

          {/* Info Message */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Notes can be added when creating the booking or when the tutor confirms the session.
              {userRole === "student" && " You can add notes during booking creation."}
              {userRole === "tutor" && " You can add notes when confirming bookings."}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-200 dark:border-slate-700">
          <Button variant="primary" onClick={onClose} className="w-full">
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
