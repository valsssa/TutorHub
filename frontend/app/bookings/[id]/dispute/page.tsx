"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  AlertTriangle,
  Upload,
  FileText,
  X,
  Clock,
  CheckCircle,
  XCircle,
  MessageSquare,
  Calendar,
  User,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import TextArea from "@/components/TextArea";
import Select from "@/components/Select";
import LoadingSpinner from "@/components/LoadingSpinner";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { bookings } from "@/lib/api";
import { useToast } from "@/components/ToastContainer";
import type { BookingDTO } from "@/types/booking";
import clsx from "clsx";

const DISPUTE_REASONS = [
  { value: "tutor_no_show", label: "Tutor did not show up" },
  { value: "session_quality", label: "Poor session quality" },
  { value: "technical_issues", label: "Technical issues prevented session" },
  { value: "incorrect_charge", label: "Incorrect charge amount" },
  { value: "unauthorized_charge", label: "Unauthorized charge" },
  { value: "service_not_as_described", label: "Service was not as described" },
  { value: "other", label: "Other (please specify)" },
];

interface DisputeEvidence {
  id: string;
  name: string;
  size: number;
  type: string;
  file: File;
}

export default function DisputePage() {
  return (
    <ProtectedRoute>
      <DisputeContent />
    </ProtectedRoute>
  );
}

function DisputeContent() {
  const params = useParams();
  const router = useRouter();
  const { showSuccess, showError } = useToast();

  const bookingId = params?.id ? Number(params.id) : null;

  const [booking, setBooking] = useState<BookingDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [reason, setReason] = useState("");
  const [description, setDescription] = useState("");
  const [evidence, setEvidence] = useState<DisputeEvidence[]>([]);
  const [agreeTerms, setAgreeTerms] = useState(false);

  // Existing dispute state
  const [existingDispute, setExistingDispute] = useState<{
    status: string;
    reason: string;
    description: string;
    created_at: string;
    resolution?: string;
  } | null>(null);

  const loadBooking = useCallback(async () => {
    if (!bookingId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await bookings.get(bookingId);
      setBooking(data);

      // Check if there's an existing dispute
      if (data.dispute_state && data.dispute_state !== "none") {
        setExistingDispute({
          status: data.dispute_state,
          reason: data.dispute_reason || "",
          description: data.dispute_description || "",
          created_at: data.dispute_filed_at || data.updated_at,
          resolution: data.dispute_resolution,
        });
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load booking");
    } finally {
      setLoading(false);
    }
  }, [bookingId]);

  useEffect(() => {
    loadBooking();
  }, [loadBooking]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newEvidence: DisputeEvidence[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        showError(`File "${file.name}" is too large. Maximum size is 10MB.`);
        continue;
      }

      // Validate file type
      const allowedTypes = ["image/jpeg", "image/png", "image/gif", "application/pdf", "text/plain"];
      if (!allowedTypes.includes(file.type)) {
        showError(`File "${file.name}" has an unsupported format.`);
        continue;
      }

      newEvidence.push({
        id: `${Date.now()}-${i}`,
        name: file.name,
        size: file.size,
        type: file.type,
        file,
      });
    }

    setEvidence((prev) => [...prev, ...newEvidence]);
    e.target.value = ""; // Reset input
  };

  const removeEvidence = (id: string) => {
    setEvidence((prev) => prev.filter((e) => e.id !== id));
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!booking || !reason || !description.trim()) {
      showError("Please fill in all required fields");
      return;
    }

    if (!agreeTerms) {
      showError("Please agree to the dispute terms");
      return;
    }

    setSubmitting(true);

    try {
      // Combine reason and description for the dispute
      const disputeReason = `[${DISPUTE_REASONS.find(r => r.value === reason)?.label || reason}]\n\n${description}`;

      await bookings.fileDispute(bookingId!, disputeReason);

      showSuccess("Dispute submitted successfully. We'll review it within 3-5 business days.");
      router.push(`/bookings/${bookingId}`);
    } catch (err: any) {
      showError(err?.response?.data?.detail || "Failed to submit dispute");
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4">
        <div className="container mx-auto max-w-2xl">
          <EmptyState
            variant="error"
            title="Booking Not Found"
            description={error || "We couldn't find this booking."}
            action={{
              label: "Go to Bookings",
              onClick: () => router.push("/bookings"),
            }}
          />
        </div>
      </div>
    );
  }

  // Show existing dispute status
  if (existingDispute) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        {/* Header */}
        <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
          <div className="container mx-auto px-4 py-4">
            <Breadcrumb
              items={[
                { label: "Bookings", href: "/bookings" },
                { label: `#${bookingId}`, href: `/bookings/${bookingId}` },
                { label: "Dispute" },
              ]}
            />
          </div>
        </div>

        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <Link href={`/bookings/${bookingId}`}>
            <Button variant="ghost" size="sm" className="mb-6">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Booking
            </Button>
          </Link>

          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
            {/* Status Header */}
            <div className={clsx(
              "px-6 py-8 text-center",
              existingDispute.status === "resolved_student_favor" && "bg-emerald-50 dark:bg-emerald-900/20",
              existingDispute.status === "resolved_tutor_favor" && "bg-amber-50 dark:bg-amber-900/20",
              existingDispute.status === "under_review" && "bg-blue-50 dark:bg-blue-900/20",
              existingDispute.status === "filed" && "bg-slate-50 dark:bg-slate-800/50"
            )}>
              <div className={clsx(
                "w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4",
                existingDispute.status === "resolved_student_favor" && "bg-emerald-100 dark:bg-emerald-900/30",
                existingDispute.status === "resolved_tutor_favor" && "bg-amber-100 dark:bg-amber-900/30",
                existingDispute.status === "under_review" && "bg-blue-100 dark:bg-blue-900/30",
                existingDispute.status === "filed" && "bg-slate-100 dark:bg-slate-800"
              )}>
                {existingDispute.status === "resolved_student_favor" && (
                  <CheckCircle className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
                )}
                {existingDispute.status === "resolved_tutor_favor" && (
                  <XCircle className="w-8 h-8 text-amber-600 dark:text-amber-400" />
                )}
                {(existingDispute.status === "under_review" || existingDispute.status === "filed") && (
                  <Clock className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                )}
              </div>

              <StatusBadge status={existingDispute.status} type="dispute" className="mb-3" />

              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                {existingDispute.status === "resolved_student_favor" && "Dispute Resolved in Your Favor"}
                {existingDispute.status === "resolved_tutor_favor" && "Dispute Resolved"}
                {existingDispute.status === "under_review" && "Dispute Under Review"}
                {existingDispute.status === "filed" && "Dispute Filed"}
              </h1>

              <p className="text-slate-500 dark:text-slate-400">
                Filed on {formatDate(existingDispute.created_at)}
              </p>
            </div>

            {/* Dispute Details */}
            <div className="p-6 space-y-6">
              <div>
                <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Reason
                </h3>
                <p className="text-slate-900 dark:text-white">
                  {DISPUTE_REASONS.find((r) => r.value === existingDispute.reason)?.label || existingDispute.reason}
                </p>
              </div>

              <div>
                <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Description
                </h3>
                <p className="text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
                  {existingDispute.description}
                </p>
              </div>

              {existingDispute.resolution && (
                <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
                  <h3 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                    Resolution
                  </h3>
                  <p className="text-slate-700 dark:text-slate-300">
                    {existingDispute.resolution}
                  </p>
                </div>
              )}

              {(existingDispute.status === "filed" || existingDispute.status === "under_review") && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    <Clock className="w-4 h-4 inline mr-2" />
                    We typically review disputes within 3-5 business days. You'll receive an email when there's an update.
                  </p>
                </div>
              )}

              <div className="pt-4">
                <Button
                  variant="secondary"
                  onClick={() => router.push(`/messages?user=${booking.tutor.id}`)}
                  className="w-full"
                >
                  <MessageSquare className="w-4 h-4 mr-2" />
                  Contact Support
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // New dispute form
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb
            items={[
              { label: "Bookings", href: "/bookings" },
              { label: `#${bookingId}`, href: `/bookings/${bookingId}` },
              { label: "File Dispute" },
            ]}
          />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Link href={`/bookings/${bookingId}`}>
          <Button variant="ghost" size="sm" className="mb-6">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Booking
          </Button>
        </Link>

        {/* Warning Banner */}
        <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 mb-6">
          <div className="flex gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-amber-800 dark:text-amber-200 mb-1">
                Before filing a dispute
              </h3>
              <p className="text-sm text-amber-700 dark:text-amber-300">
                We recommend trying to resolve the issue directly with your tutor first.
                Disputes are reviewed manually and may take 3-5 business days to resolve.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
          {/* Header */}
          <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-800">
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">
              File a Dispute
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Session with {booking.tutor.name} on {new Date(booking.start_at).toLocaleDateString()}
            </p>
          </div>

          {/* Session Summary */}
          <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                <User className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-900 dark:text-white truncate">
                  {booking.subject_name || "Session"} with {booking.tutor.name}
                </p>
                <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {new Date(booking.start_at).toLocaleDateString()}
                  </span>
                  <span>
                    ${((booking.rate_cents + booking.platform_fee_cents) / 100).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Reason */}
            <Select
              label="Reason for dispute"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            >
              <option value="">Select a reason</option>
              {DISPUTE_REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </Select>

            {/* Description */}
            <TextArea
              label="Describe the issue"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Please provide details about what happened and why you're filing this dispute..."
              rows={5}
              required
              minLength={50}
              maxLength={2000}
              helperText={`${description.length}/2000 characters (minimum 50)`}
            />

            {/* Evidence Upload */}
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Supporting evidence (optional)
              </label>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-3">
                Upload screenshots, emails, or other documents that support your claim.
              </p>

              <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-xl p-6 text-center hover:border-emerald-500 dark:hover:border-emerald-500 transition-colors">
                <input
                  type="file"
                  id="evidence-upload"
                  className="hidden"
                  multiple
                  accept="image/*,.pdf,.txt"
                  onChange={handleFileUpload}
                />
                <label
                  htmlFor="evidence-upload"
                  className="cursor-pointer"
                >
                  <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    <span className="text-emerald-600 dark:text-emerald-400 font-medium">Click to upload</span>
                    {" "}or drag and drop
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    PNG, JPG, PDF up to 10MB each
                  </p>
                </label>
              </div>

              {/* Uploaded Files */}
              {evidence.length > 0 && (
                <ul className="mt-4 space-y-2">
                  {evidence.map((file) => (
                    <li
                      key={file.id}
                      className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <FileText className="w-5 h-5 text-slate-400 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
                            {file.name}
                          </p>
                          <p className="text-xs text-slate-400">
                            {formatFileSize(file.size)}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeEvidence(file.id)}
                        className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Terms Agreement */}
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="agree-terms"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                className="mt-1 w-4 h-4 text-emerald-600 border-slate-300 rounded focus:ring-emerald-500"
              />
              <label
                htmlFor="agree-terms"
                className="text-sm text-slate-600 dark:text-slate-400"
              >
                I confirm that the information provided is accurate and understand that filing
                false disputes may result in account suspension.
              </label>
            </div>

            {/* Submit */}
            <div className="flex flex-col-reverse sm:flex-row gap-3 pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={() => router.back()}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                isLoading={submitting}
                disabled={!reason || description.length < 50 || !agreeTerms}
                className="flex-1"
              >
                Submit Dispute
              </Button>
            </div>
          </form>
        </div>

        {/* Help Text */}
        <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-6">
          Need help?{" "}
          <Link
            href="/help/disputes"
            className="text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 font-medium"
          >
            Learn about our dispute process
          </Link>
        </p>
      </div>
    </div>
  );
}
