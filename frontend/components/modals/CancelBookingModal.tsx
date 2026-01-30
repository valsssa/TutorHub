"use client";

/**
 * Modal for canceling a booking with optional reason
 * Uses base Modal component for consistent UX
 */

import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import Modal from "../Modal";
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

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Cancel Booking"
      size="md"
      closeOnBackdropClick={!isSubmitting}
      footer={
        <div className="flex flex-col-reverse sm:flex-row gap-3">
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
            isLoading={isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? "Canceling..." : "Cancel Booking"}
          </Button>
        </div>
      }
    >
      {/* Session Info */}
      {tutorName && (
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
          Session with <span className="font-medium text-slate-900 dark:text-white">{tutorName}</span>
        </p>
      )}

      {/* Warning */}
      <div className="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl flex gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
            Are you sure you want to cancel?
          </p>
          <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
            This action cannot be undone. Refund eligibility depends on timing.
          </p>
        </div>
      </div>

      {/* Reason Input */}
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
    </Modal>
  );
}
