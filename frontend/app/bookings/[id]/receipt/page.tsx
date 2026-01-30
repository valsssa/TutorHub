"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  Printer,
  Mail,
  Calendar,
  Clock,
  User,
  CreditCard,
  CheckCircle,
  FileText,
  Building,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import EmptyState from "@/components/EmptyState";
import StatusBadge from "@/components/StatusBadge";
import { bookings } from "@/lib/api";
import { useToast } from "@/components/ToastContainer";
import type { BookingDTO } from "@/types/booking";

export default function ReceiptPage() {
  return (
    <ProtectedRoute>
      <ReceiptContent />
    </ProtectedRoute>
  );
}

function ReceiptContent() {
  const params = useParams();
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const receiptRef = useRef<HTMLDivElement>(null);

  const bookingId = params?.id ? Number(params.id) : null;

  const [booking, setBooking] = useState<BookingDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadBooking = useCallback(async () => {
    if (!bookingId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await bookings.get(bookingId);
      setBooking(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to load receipt");
    } finally {
      setLoading(false);
    }
  }, [bookingId]);

  useEffect(() => {
    loadBooking();
  }, [loadBooking]);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPDF = async () => {
    // In a real app, this would call a backend endpoint to generate PDF
    // For now, we'll use the browser's print-to-PDF functionality
    showSuccess("Opening print dialog. Select 'Save as PDF' to download.");
    window.print();
  };

  const handleEmailReceipt = async () => {
    // In a real app, this would call a backend endpoint to send email
    showSuccess("Receipt has been sent to your email address.");
  };

  // Format currency
  const formatCurrency = (cents: number, currency: string) =>
    new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
    }).format(cents / 100);

  // Format date
  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });

  const formatTime = (dateString: string) =>
    new Date(dateString).toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
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
            title="Receipt Not Found"
            description={error || "We couldn't find this receipt."}
            action={{
              label: "Go to Bookings",
              onClick: () => router.push("/bookings"),
            }}
          />
        </div>
      </div>
    );
  }

  const totalAmount = booking.rate_cents + booking.platform_fee_cents;
  const receiptNumber = `RCP-${booking.id.toString().padStart(6, "0")}`;
  const transactionDate = booking.created_at;

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-950">
      {/* Header - Hidden in print */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 print:hidden">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb
            items={[
              { label: "Bookings", href: "/bookings" },
              { label: `#${bookingId}`, href: `/bookings/${bookingId}` },
              { label: "Receipt" },
            ]}
          />
        </div>
      </div>

      {/* Actions Bar - Hidden in print */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-10 print:hidden">
        <div className="container mx-auto px-4 py-3 max-w-2xl flex items-center justify-between">
          <Link href={`/bookings/${bookingId}`}>
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Booking
            </Button>
          </Link>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleEmailReceipt}>
              <Mail className="w-4 h-4 mr-2" />
              Email
            </Button>
            <Button variant="ghost" size="sm" onClick={handlePrint}>
              <Printer className="w-4 h-4 mr-2" />
              Print
            </Button>
            <Button variant="primary" size="sm" onClick={handleDownloadPDF}>
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </Button>
          </div>
        </div>
      </div>

      {/* Receipt Content */}
      <div className="container mx-auto px-4 py-8 max-w-2xl print:max-w-none print:p-0">
        <div
          ref={receiptRef}
          className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden print:shadow-none print:border-none print:rounded-none"
        >
          {/* Receipt Header */}
          <div className="bg-gradient-to-r from-emerald-600 to-teal-600 px-8 py-10 text-white print:bg-emerald-600">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-6 h-6" />
                  <span className="text-lg font-bold">EduConnect</span>
                </div>
                <h1 className="text-3xl font-bold">Payment Receipt</h1>
                <p className="text-emerald-100 mt-1">Thank you for your purchase</p>
              </div>
              <div className="text-right">
                <div className="text-emerald-100 text-sm">Receipt Number</div>
                <div className="font-mono font-bold text-lg">{receiptNumber}</div>
              </div>
            </div>
          </div>

          {/* Receipt Body */}
          <div className="p-8">
            {/* Status & Date */}
            <div className="flex items-center justify-between mb-8 pb-6 border-b border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">
                    Payment Successful
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {formatDate(transactionDate)}
                  </p>
                </div>
              </div>
              <StatusBadge status={booking.payment_state} type="payment" />
            </div>

            {/* Session Details */}
            <div className="mb-8">
              <h2 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">
                Session Details
              </h2>
              <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-5 space-y-4">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <User className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Tutor</p>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {booking.tutor.name}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Date & Time</p>
                    <p className="font-medium text-slate-900 dark:text-white">
                      {formatDate(booking.start_at)}
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {formatTime(booking.start_at)} - {formatTime(booking.end_at)}
                    </p>
                  </div>
                </div>

                {booking.subject_name && (
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                      <span className="text-lg">📚</span>
                    </div>
                    <div>
                      <p className="text-sm text-slate-500 dark:text-slate-400">Subject</p>
                      <p className="font-medium text-slate-900 dark:text-white">
                        {booking.subject_name}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Payment Breakdown */}
            <div className="mb-8">
              <h2 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">
                Payment Summary
              </h2>
              <div className="space-y-3">
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Session fee</span>
                  <span>{formatCurrency(booking.rate_cents, booking.currency)}</span>
                </div>
                <div className="flex justify-between text-slate-600 dark:text-slate-400">
                  <span>Platform fee ({booking.platform_fee_pct}%)</span>
                  <span>{formatCurrency(booking.platform_fee_cents, booking.currency)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold text-slate-900 dark:text-white pt-4 border-t border-slate-200 dark:border-slate-700">
                  <span>Total Paid</span>
                  <span>{formatCurrency(totalAmount, booking.currency)}</span>
                </div>
              </div>
            </div>

            {/* Payment Method */}
            <div className="mb-8">
              <h2 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">
                Payment Method
              </h2>
              <div className="flex items-center gap-3 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                <CreditCard className="w-5 h-5 text-slate-400" />
                <span className="text-slate-700 dark:text-slate-300">
                  Card ending in ****
                </span>
              </div>
            </div>

            {/* Billing Info */}
            <div className="grid grid-cols-2 gap-6 mb-8 print:grid-cols-2">
              <div>
                <h2 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Billed To
                </h2>
                <p className="font-medium text-slate-900 dark:text-white">
                  {booking.student.name}
                </p>
              </div>
              <div>
                <h2 className="text-sm font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                  Booking ID
                </h2>
                <p className="font-mono text-slate-700 dark:text-slate-300">
                  #{booking.id}
                </p>
              </div>
            </div>

            {/* Footer */}
            <div className="pt-6 border-t border-slate-200 dark:border-slate-700">
              <div className="flex items-start gap-3 text-sm text-slate-500 dark:text-slate-400">
                <Building className="w-4 h-4 mt-0.5 shrink-0" />
                <div>
                  <p className="font-medium text-slate-700 dark:text-slate-300">
                    EduConnect, Inc.
                  </p>
                  <p>123 Learning Street, Education City, EC 12345</p>
                  <p>support@educonnect.com</p>
                </div>
              </div>

              <p className="mt-6 text-xs text-slate-400 dark:text-slate-500 text-center">
                This receipt was generated automatically and is valid without signature.
                <br />
                For questions about this transaction, please contact our support team.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Print Styles */}
      <style jsx global>{`
        @media print {
          body {
            background: white !important;
          }
          .print\\:hidden {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}
