"use client";

/**
 * Modal for canceling a booking with optional reason
 */

import { useState } from "react";
import Button from "../Button";
import TextArea from "../TextArea";

interface CancelBookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => Promise<void>;
  bookingId?: number;
  tutorName?: string;
}

export default function CancelBookingModal({
  isOpen,
  onClose,
  onConfirm,
  tutorName,
}: CancelBookingModalProps) {
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      await onConfirm(reason.trim() || undefined);
      setReason("");
      onClose();
    } catch (error) {
      // Error handled by parent
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setReason("");
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
          {/* Header */}
          <div className="mb-4">
            <h3 className="text-xl font-semibold text-gray-900">
              Cancel Booking
            </h3>
            {tutorName && (
              <p className="text-sm text-gray-600 mt-1">
                Session with {tutorName}
              </p>
            )}
          </div>

          {/* Warning */}
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800">
              Are you sure you want to cancel this booking? This action cannot be undone.
            </p>
          </div>

          {/* Reason Input */}
          <div className="mb-6">
            <TextArea
              id="cancel-reason"
              label="Reason for cancellation (sent to the tutor)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="What changed? Is there a scheduling conflict? Would you like to reschedule instead?"
              minRows={3}
              maxRows={6}
              maxLength={500}
              disabled={isSubmitting}
              helperText="Optional - helps the tutor understand and potentially accommodate your needs"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1"
            >
              Keep Booking
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirm}
              disabled={isSubmitting}
              className="flex-1"
            >
              {isSubmitting ? "Canceling..." : "Cancel Booking"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
