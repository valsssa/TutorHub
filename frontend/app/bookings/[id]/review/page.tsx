"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { FiStar, FiArrowLeft } from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { bookings, reviews as reviewsApi } from "@/lib/api";
import type { Booking } from "@/types";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";

export default function BookingReviewPage() {
  return (
    <ProtectedRoute requiredRole="student">
      <BookingReviewContent />
    </ProtectedRoute>
  );
}

function BookingReviewContent() {
  const router = useRouter();
  const params = useParams();
  const { showSuccess, showError } = useToast();
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [hoveredRating, setHoveredRating] = useState(0);

  const bookingId = params?.id ? Number(params.id) : null;

  const loadBooking = useCallback(async () => {
    if (!bookingId) return;

    setLoading(true);
    try {
      const bookingData = await bookings.get(bookingId);

      if (!bookingData) {
        showError("Booking not found");
        router.push("/bookings");
        return;
      }

      if (bookingData.status !== "completed" && bookingData.status !== "COMPLETED") {
        showError("Can only review completed bookings");
        router.push("/bookings");
        return;
      }

      // Convert BookingDTO to legacy Booking type for compatibility
      const legacyBooking: Booking = {
        ...bookingData,
        student_id: bookingData.student.id,
        tutor_profile_id: bookingData.tutor.id,
        start_time: bookingData.start_at,
        end_time: bookingData.end_at,
        status: bookingData.status as any,
        tutor_name: bookingData.tutor.name,
        student_name: bookingData.student.name,
        topic: bookingData.topic || "",
        notes: bookingData.notes_student || "",
        total_amount: bookingData.rate_cents / 100,
        hourly_rate: bookingData.rate_cents / 100,
      } as any;

      setBooking(legacyBooking);
    } catch (error) {
      showError("Failed to load booking");
      router.push("/bookings");
    } finally {
      setLoading(false);
    }
  }, [bookingId, router, showError]);

  useEffect(() => {
    if (bookingId) {
      loadBooking();
    }
  }, [bookingId, loadBooking]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!booking) return;

    if (rating < 1 || rating > 5) {
      showError("Please select a rating");
      return;
    }

    setSubmitting(true);
    try {
      await reviewsApi.create(booking.id, rating, comment.trim() || undefined);
      showSuccess("Review submitted successfully");
      router.push("/bookings");
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      showError(err.response?.data?.detail || "Failed to submit review");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !booking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <button
        onClick={() => router.push("/bookings")}
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <FiArrowLeft className="w-5 h-5" />
        Back to Bookings
      </button>

      <div className="bg-white rounded-lg shadow-sm p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Leave a Review
        </h1>
        <p className="text-gray-600 mb-8">
          Share your experience with this tutoring session
        </p>

        {/* Booking Info */}
        <div className="bg-gray-50 rounded-lg p-6 mb-8">
          <h3 className="font-semibold text-gray-900 mb-3">Session Details</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Topic:</span>
              <span className="font-medium text-gray-900">
                {booking.topic || "Tutoring Session"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Date:</span>
              <span className="font-medium text-gray-900">
                {new Date(booking.start_time).toLocaleDateString("en-US", {
                  weekday: "long",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Duration:</span>
              <span className="font-medium text-gray-900">
                {Math.round(
                  (new Date(booking.end_time).getTime() -
                    new Date(booking.start_time).getTime()) /
                    60000,
                )}{" "}
                minutes
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Amount Paid:</span>
              <span className="font-medium text-gray-900">
                ${booking.total_amount}
              </span>
            </div>
          </div>
        </div>

        {/* Review Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Rating */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-3">
              How would you rate this session? *
            </label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setRating(value)}
                  onMouseEnter={() => setHoveredRating(value)}
                  onMouseLeave={() => setHoveredRating(0)}
                  className="focus:outline-none transition-transform hover:scale-110"
                >
                  <FiStar
                    className={`w-12 h-12 ${
                      value <= (hoveredRating || rating)
                        ? "text-yellow-500 fill-current"
                        : "text-gray-300"
                    }`}
                  />
                </button>
              ))}
              <span className="ml-4 text-sm font-medium text-gray-700">
                {rating === 1 && "Poor"}
                {rating === 2 && "Fair"}
                {rating === 3 && "Good"}
                {rating === 4 && "Very Good"}
                {rating === 5 && "Excellent"}
              </span>
            </div>
          </div>

          {/* Comment */}
          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Share your experience (optional)
            </label>
            <textarea
              rows={6}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="What did you like about this session? How did the tutor help you? Any suggestions for improvement?"
              maxLength={2000}
            />
            <p className="text-sm text-gray-500 mt-1">
              {comment.length}/2000 characters
            </p>
          </div>

          {/* Privacy Notice */}
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              <strong>Note:</strong> Your review will be publicly visible to
              help other students make informed decisions. Please be respectful
              and constructive in your feedback.
            </p>
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={() => router.push("/bookings")}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              className="flex-1"
              disabled={submitting || rating < 1}
            >
              {submitting ? "Submitting..." : "Submit Review"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
