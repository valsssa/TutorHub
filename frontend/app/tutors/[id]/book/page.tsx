"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import Image from "next/image";
import {
  ChevronLeft,
  Star,
  Clock,
  Calendar,
  CreditCard,
  Lock,
  ArrowRight,
  User as UserIcon,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { tutors, subjects as subjectsApi, bookings, auth } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { resolveAssetUrl } from "@/lib/media";
import type { TutorProfile, User, Subject, Review } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";

export default function BookingPage() {
  return (
    <ProtectedRoute>
      <BookingPageContent />
    </ProtectedRoute>
  );
}

function BookingPageContent() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const { showSuccess, showError } = useToast();

  const [tutor, setTutor] = useState<TutorProfile | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Booking state
  const [duration, setDuration] = useState<25 | 50>(50);
  const [paymentMethod, setPaymentMethod] = useState<
    "card" | "apple" | "google" | "paypal"
  >("card");
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(
    null
  );
  const [topic, setTopic] = useState("");

  const tutorId = params?.id ? Number(params.id) : null;
  const slotParam = searchParams?.get("slot");

  // Parse slot from URL
  const slot = slotParam ? decodeURIComponent(slotParam) : null;
  const dateObj = useMemo(() => slot ? new Date(slot) : null, [slot]);

  const loadData = useCallback(async () => {
    if (!tutorId) return;

    setLoading(true);
    try {
      const [tutorData, currentUser, subjectsData, reviewsData] =
        await Promise.all([
          tutors.get(tutorId),
          auth.getCurrentUser(),
          subjectsApi.list(),
          tutors.getReviews(tutorId),
        ]);
      setTutor(tutorData);
      setUser(currentUser);
      setSubjectsList(subjectsData);
      setReviews(reviewsData);

      // Set default subject
      if (tutorData.subjects && tutorData.subjects.length > 0) {
        setSelectedSubjectId(tutorData.subjects[0].subject_id);
      } else if (subjectsData.length > 0) {
        setSelectedSubjectId(subjectsData[0].id);
      }
    } catch (error) {
      showError("Failed to load booking details");
      router.push(`/tutors/${tutorId}`);
    } finally {
      setLoading(false);
    }
  }, [router, showError, tutorId]);

  useEffect(() => {
    if (tutorId) {
      loadData();
    }
  }, [tutorId, loadData]);

  // Redirect if no slot provided or user is not a student
  useEffect(() => {
    if (!loading && (!slot || !dateObj)) {
      showError("Please select a time slot first");
      router.push(`/tutors/${tutorId}`);
    }
    if (!loading && user && !authUtils.isStudent(user)) {
      showError("Only students can book lessons");
      router.push(`/tutors/${tutorId}`);
    }
  }, [loading, slot, dateObj, user, tutorId, router, showError]);

  const handleBack = () => {
    router.push(`/tutors/${tutorId}`);
  };

  const handleConfirm = async () => {
    if (!tutor || !dateObj || !selectedSubjectId) return;

    const startDate = new Date(dateObj);
    const endDate = new Date(startDate.getTime() + duration * 60000);

    setSubmitting(true);
    try {
      await bookings.create({
        tutor_profile_id: tutor.id,
        subject_id: selectedSubjectId,
        start_at: startDate.toISOString(),
        duration_minutes: duration,
        notes_student: topic || undefined,
      });

      showSuccess("Booking confirmed! Check your email for details.");

      // Use setTimeout to ensure toast is shown before redirect
      setTimeout(() => {
        router.replace("/bookings");
      }, 100);
    } catch (error: any) {
      const errorMessage =
        error?.response?.data?.detail || "Failed to create booking";

      // Check if slot is no longer available
      if (
        errorMessage.toLowerCase().includes("not available") ||
        errorMessage.toLowerCase().includes("already booked") ||
        errorMessage.toLowerCase().includes("conflict")
      ) {
        showError(
          "This time slot is no longer available. Please select another time."
        );
        router.push(`/tutors/${tutorId}`);
      } else {
        showError(errorMessage);
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || !tutor || !dateObj) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Calculate costs
  const hourlyRate = Number(tutor.hourly_rate);
  const lessonPrice = duration === 50 ? hourlyRate : hourlyRate / 2;
  const processingFee = 0.3;
  const total = lessonPrice + processingFee;

  const formatTimeRange = (date: Date, minutes: number) => {
    const start = date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    const endDate = new Date(date.getTime() + minutes * 60000);
    const end = endDate.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
    return `${start} – ${end}`;
  };

  const averageRating = Number(tutor.average_rating);
  const firstReview = reviews[0];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-12">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-30">
        <div className="container mx-auto px-4 h-16 flex items-center">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-slate-600 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-400 font-medium transition-colors"
          >
            <ChevronLeft size={20} /> Back
          </button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Details */}
          <div className="lg:col-span-5 space-y-6">
            {/* Tutor Summary */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                Your tutor
              </h2>
              <div className="flex gap-4 items-start">
                {tutor.profile_photo_url ? (
                  <Image
                    src={resolveAssetUrl(tutor.profile_photo_url)}
                    alt={tutor.title}
                    width={64}
                    height={64}
                    className="w-16 h-16 rounded-xl object-cover border border-slate-200 dark:border-slate-700"
                    unoptimized
                  />
                ) : (
                  <div className="w-16 h-16 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                    <span className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                      {tutor.title.charAt(0)}
                    </span>
                  </div>
                )}
                <div>
                  <h3 className="font-bold text-xl text-slate-900 dark:text-white">
                    {tutor.title}
                  </h3>
                  <div className="flex items-center gap-1 text-sm text-slate-600 dark:text-slate-400 mt-1">
                    <Star
                      size={14}
                      className="text-slate-900 dark:text-white fill-slate-900 dark:fill-white"
                    />
                    <span className="font-bold text-slate-900 dark:text-white">
                      {averageRating.toFixed(1)}
                    </span>
                    <span>({tutor.total_reviews} reviews)</span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
                <div>
                  <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white">
                    <UserIcon size={16} /> {tutor.total_sessions || 0}
                  </div>
                  <div className="text-xs text-slate-500">lessons</div>
                </div>
                <div>
                  <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white">
                    <Clock size={16} /> {tutor.experience_years}
                  </div>
                  <div className="text-xs text-slate-500">years exp</div>
                </div>
                <div>
                  <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-white">
                    <Calendar size={16} /> {tutor.total_reviews}
                  </div>
                  <div className="text-xs text-slate-500">reviews</div>
                </div>
              </div>

              {tutor.subjects && tutor.subjects.length > 0 && (
                <div className="mt-6 bg-slate-50 dark:bg-slate-800/50 p-3 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white text-sm">
                      Specializes in {tutor.subjects[0].subject_name}
                    </div>
                    <div className="text-xs text-slate-500">
                      Highly rated by learners
                    </div>
                  </div>
                  <div className="text-2xl">📚</div>
                </div>
              )}
            </div>

            {/* Lesson Details */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                Lesson details
              </h2>
              <div className="flex gap-4 items-center mb-4">
                <div className="w-14 h-14 bg-slate-50 dark:bg-slate-800 rounded-xl flex flex-col items-center justify-center border border-slate-200 dark:border-slate-700">
                  <span className="text-[10px] font-bold text-slate-500 uppercase">
                    {dateObj.toLocaleDateString("en-US", { month: "short" })}
                  </span>
                  <span className="text-xl font-bold text-slate-900 dark:text-white">
                    {dateObj.getDate()}
                  </span>
                </div>
                <div>
                  <div className="font-bold text-slate-900 dark:text-white">
                    {dateObj.toLocaleDateString("en-US", { weekday: "long" })},{" "}
                    {formatTimeRange(dateObj, duration)}
                  </div>
                  <div className="text-sm text-slate-500">
                    Time is based on your location
                  </div>
                </div>
              </div>
              <div className="bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-200 text-sm p-3 rounded-lg font-medium">
                Cancel or reschedule for free until 24 hours before the lesson
              </div>
            </div>

            {/* Checkout Info */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                Checkout info
              </h2>

              {/* Duration Selection */}
              <div className="flex p-1 bg-slate-100 dark:bg-slate-800 rounded-lg mb-6">
                <button
                  onClick={() => setDuration(25)}
                  className={`flex-1 py-2 text-sm font-bold rounded-md transition-all ${duration === 25 ? "bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white" : "text-slate-500 dark:text-slate-400"}`}
                >
                  25 mins • ${(hourlyRate / 2).toFixed(0)}
                </button>
                <button
                  onClick={() => setDuration(50)}
                  className={`flex-1 py-2 text-sm font-bold rounded-md transition-all ${duration === 50 ? "bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white" : "text-slate-500 dark:text-slate-400"}`}
                >
                  50 mins • ${hourlyRate.toFixed(0)}
                </button>
              </div>

              {/* Subject Selection */}
              {subjectsList.length > 0 && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Subject
                  </label>
                  <select
                    value={selectedSubjectId || ""}
                    onChange={(e) =>
                      setSelectedSubjectId(Number(e.target.value))
                    }
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors"
                  >
                    {subjectsList.map((subject) => (
                      <option key={subject.id} value={subject.id}>
                        {subject.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Topic */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  What would you like to learn? (Optional)
                </label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., Grammar basics, conversation practice..."
                  className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>

              {/* Price Breakdown */}
              <div className="space-y-3 mb-6">
                <div className="flex justify-between text-slate-600 dark:text-slate-300">
                  <span>{duration}-min lesson</span>
                  <span>${lessonPrice.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-slate-600 dark:text-slate-300">
                  <div className="flex items-center gap-1">
                    Processing fee{" "}
                    <span className="w-4 h-4 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-[10px] text-slate-500 cursor-help">
                      ?
                    </span>
                  </div>
                  <span>${processingFee.toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold text-slate-900 dark:text-white pt-3 border-t border-slate-100 dark:border-slate-800">
                  <span>Total</span>
                  <span>${total.toFixed(2)}</span>
                </div>
              </div>

              <div className="bg-[#E0F2F1] dark:bg-emerald-900/20 p-4 rounded-xl flex gap-3">
                <div className="mt-0.5 text-emerald-600 dark:text-emerald-400">
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                    <path d="M3 3v5h5" />
                    <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                    <path d="M16 21h5v-5" />
                  </svg>
                </div>
                <div>
                  <div className="text-sm font-bold text-emerald-900 dark:text-emerald-100">
                    Free tutor replacement
                  </div>
                  <div className="text-xs text-emerald-800 dark:text-emerald-200 mt-0.5">
                    If this tutor isn&apos;t a match, try 2 more for free
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Payment */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-4">
                Choose how to pay
              </h2>

              <div className="grid grid-cols-2 gap-3 mb-6">
                <button
                  onClick={() => setPaymentMethod("card")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg border font-medium transition-all ${paymentMethod === "card" ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/10 text-emerald-700 dark:text-emerald-400" : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"}`}
                >
                  <CreditCard size={18} /> Card
                </button>
                <button
                  onClick={() => setPaymentMethod("apple")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg border font-medium transition-all ${paymentMethod === "apple" ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/10 text-emerald-700 dark:text-emerald-400" : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"}`}
                >
                  <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current">
                    <path d="M17.26 14.5c-.06 2.37 2.07 3.16 2.16 3.2-.02.06-.34 1.16-1.12 2.31-.69.98-1.4 1.96-2.52 1.98-1.1.02-1.45-.65-2.71-.65-1.27 0-1.67.63-2.73.67-1.09.04-1.92-1.09-2.61-2.1-1.43-2.06-2.52-5.85-1.05-8.41 1.05-1.83 2.92-2.98 3.96-3.02 1.05-.04 2.04.7 2.68.7.64 0 1.84-.87 3.1-.74.53.02 2.01.21 2.96 1.61-.07.05-1.76 1.03-1.76 3.09M15.39 3.9c.56-.69.94-1.64.84-2.6-1.4.11-2.55.93-3.13 1.63-.52.61-.97 1.59-.85 2.53.94.07 2.59-.87 3.14-1.56" />
                  </svg>
                  Apple Pay
                </button>
                <button
                  onClick={() => setPaymentMethod("google")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg border font-medium transition-all ${paymentMethod === "google" ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/10 text-emerald-700 dark:text-emerald-400" : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"}`}
                >
                  <svg viewBox="0 0 24 24" className="w-4 h-4">
                    <path
                      d="M12.24 10.285V14.4h6.806c-.275 1.765-2.056 5.174-6.806 5.174-4.095 0-7.439-3.389-7.439-7.574s3.345-7.574 7.439-7.574c2.33 0 3.891.989 4.785 1.849l3.254-3.138C18.189 1.186 15.479 0 12.24 0c-6.635 0-12 5.365-12 12s5.365 12 12 12c6.926 0 11.52-4.869 11.52-11.726 0-.788-.085-1.39-.189-1.989H12.24z"
                      fill="currentColor"
                    />
                  </svg>
                  Google Pay
                </button>
                <button
                  onClick={() => setPaymentMethod("paypal")}
                  className={`flex items-center justify-center gap-2 py-3 px-4 rounded-lg border font-medium transition-all ${paymentMethod === "paypal" ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/10 text-emerald-700 dark:text-emerald-400" : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"}`}
                >
                  <svg viewBox="0 0 24 24" className="w-4 h-4 fill-[#003087]">
                    <path
                      d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.946 5.05-4.336 6.794-9.067 6.794h-1.4c-.33 0-.61.26-.66.58l-1.25 7.155c-.06.34-.345.58-.688.58z"
                      fill="currentColor"
                    />
                  </svg>
                  PayPal
                </button>
              </div>

              {paymentMethod === "card" && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="1234 1234 1234 1234"
                      className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                    <CreditCard
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"
                      size={20}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <input
                      type="text"
                      placeholder="MM/YY"
                      className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                    <input
                      type="text"
                      placeholder="CVC"
                      className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-4 py-3 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 transition-colors"
                    />
                  </div>
                </div>
              )}

              <label className="flex items-center gap-3 mt-6 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-5 h-5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  defaultChecked
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  Save this card for future payments
                </span>
              </label>

              <button
                onClick={handleConfirm}
                disabled={submitting || !selectedSubjectId}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-bold py-4 rounded-xl mt-6 transition-colors shadow-sm flex items-center justify-center gap-2"
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                    Processing...
                  </>
                ) : (
                  <>Book lesson and pay • ${total.toFixed(2)}</>
                )}
              </button>

              <div className="mt-4 text-xs text-slate-500 leading-relaxed text-center">
                By pressing the &quot;Book lesson and pay&quot; button, you
                agree to our{" "}
                <a href="#" className="underline">
                  Refund and Payment Policy
                </a>
              </div>

              <div className="mt-2 flex items-center justify-center gap-1.5 text-xs text-slate-400">
                <Lock size={12} /> It&apos;s safe to pay on EduConnect. All
                transactions are protected by SSL encryption.
              </div>
            </div>

            {/* Review Snippet */}
            {firstReview && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-sm">
                <h3 className="font-bold text-slate-900 dark:text-white mb-4">
                  {tutor.title} is a great choice
                </h3>

                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-1">
                    <Star
                      size={16}
                      fill="currentColor"
                      className="text-slate-900 dark:text-white"
                    />
                    <span className="font-bold text-slate-900 dark:text-white">
                      {averageRating.toFixed(1)}
                    </span>
                    <span className="text-sm text-slate-500 ml-1">
                      {tutor.total_reviews} reviews
                    </span>
                  </div>
                  <div className="flex gap-2">
                    <button className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                      <ChevronLeft
                        size={16}
                        className="text-slate-600 dark:text-slate-400"
                      />
                    </button>
                    <button className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors">
                      <ArrowRight
                        size={16}
                        className="text-slate-600 dark:text-slate-400"
                      />
                    </button>
                  </div>
                </div>

                <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                  {firstReview.comment ||
                    "An excellent tutor who understands students needs and interests well."}
                </p>

                <button className="text-sm font-bold text-slate-900 dark:text-white underline hover:text-emerald-600 transition-colors">
                  Read more
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
