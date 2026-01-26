"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Wallet, Heart, Calendar, Clock, Video, Eye, Search } from "lucide-react";
import { User, FavoriteTutor, TutorPublicSummary, StudentProfile } from "@/types";
import { BookingDTO } from "@/types/booking";
import TutorCard from "@/components/TutorCard";
import { favorites, tutors, students } from "@/lib/api";
import { useToast } from "@/components/ToastContainer";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

interface StudentDashboardProps {
  user: User;
  bookings: BookingDTO[];
  onAvatarChange: (url: string | null) => void;
}

// Subject icon helper
function getSubjectIcon(subjectName?: string | null): string {
  if (!subjectName) return "📚";
  const lower = subjectName.toLowerCase();
  if (lower.includes("math")) return "∫";
  if (lower.includes("physics")) return "⚛";
  if (lower.includes("chemistry")) return "🧪";
  if (lower.includes("programming") || lower.includes("code") || lower.includes("computer"))
    return "💻";
  if (lower.includes("english") || lower.includes("language")) return "📝";
  if (lower.includes("music")) return "🎵";
  if (lower.includes("art")) return "🎨";
  if (lower.includes("history")) return "📜";
  if (lower.includes("biology")) return "🧬";
  return "📚";
}

export default function StudentDashboard({
  user,
  bookings,
}: StudentDashboardProps) {
  const router = useRouter();
  const { showError } = useToast();

  const [savedTutors, setSavedTutors] = useState<TutorPublicSummary[]>([]);
  const [favoritesList, setFavoritesList] = useState<FavoriteTutor[]>([]);
  const [studentProfile, setStudentProfile] = useState<StudentProfile | null>(null);
  const [loadingSavedTutors, setLoadingSavedTutors] = useState(true);

  // Load saved tutors and student profile on component mount
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoadingSavedTutors(true);

        // Load student profile (includes balance if available)
        try {
          const profile = await students.getProfile();
          setStudentProfile(profile);
        } catch (error) {
          console.error("Error loading student profile:", error);
          // Continue without profile data
        }

        // Get user's favorites
        const userFavorites = await favorites.getFavorites();
        setFavoritesList(userFavorites);

        if (userFavorites.length > 0) {
          // Get tutor profiles for each favorite
          const tutorIds = userFavorites.map(fav => fav.tutor_profile_id);
          const tutorPromises = tutorIds.map(id => tutors.getPublic(id));
          const tutorProfiles = await Promise.all(tutorPromises);
          setSavedTutors(tutorProfiles);
        } else {
          setSavedTutors([]);
        }
      } catch (error: any) {
        console.error("Error loading dashboard data:", error);
        showError(error.response?.data?.detail || "Failed to load dashboard data");
        setSavedTutors([]);
      } finally {
        setLoadingSavedTutors(false);
      }
    };

    loadDashboardData();
  }, [showError]);

  // Filter bookings by status
  const mySessions = useMemo(
    () => bookings.filter(booking => booking.student.id === user.id),
    [bookings, user.id]
  );

  // Check if a session is joinable (within 15 minutes of start time)
  const isJoinable = (startAt: string): boolean => {
    const now = new Date();
    const start = new Date(startAt);
    const diff = start.getTime() - now.getTime();
    // Joinable if within 15 minutes before or during the session
    return diff <= 15 * 60 * 1000 && diff >= -60 * 60 * 1000;
  };

  const getUserDisplayName = (): string => {
    if (user.first_name) {
      return user.first_name;
    }
    return user.email.split("@")[0];
  };

  const handleStartSession = (booking: BookingDTO) => {
    if (booking.join_url) {
      window.open(booking.join_url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleReviewSession = (bookingId: number) => {
    router.push(`/bookings/${bookingId}/review`);
  };

  const handleViewProfile = (tutor: TutorPublicSummary) => {
    router.push(`/tutors/${tutor.id}`);
  };

  const handleToggleSave = async (e: React.MouseEvent, tutorId: number) => {
    e.stopPropagation();

    try {
      await favorites.removeFavorite(tutorId);

      // Update local state
      setFavoritesList(prev => prev.filter(fav => fav.tutor_profile_id !== tutorId));
      setSavedTutors(prev => prev.filter(tutor => tutor.id !== tutorId));

      // Show success message would be handled by toast if needed
    } catch (error: any) {
      console.error("Error removing favorite:", error);
      showError(error.response?.data?.detail || "Failed to remove from favorites");
    }
  };

  const handleBook = (e: React.MouseEvent, tutor: TutorPublicSummary) => {
    e.stopPropagation();
    router.push(`/tutors/${tutor.id}`);
  };

  const handleQuickBook = (e: React.MouseEvent, tutor: TutorPublicSummary) => {
    e.stopPropagation();
    router.push(`/tutors/${tutor.id}?quick-book=true`);
  };

  const handleSlotBook = (e: React.MouseEvent, tutor: TutorPublicSummary, slot: string) => {
    e.stopPropagation();
    router.push(`/tutors/${tutor.id}?slot=${slot}`);
  };

  const handleMessage = (e: React.MouseEvent, tutor: TutorPublicSummary) => {
    e.stopPropagation();
    router.push(`/messages?user=${tutor.user_id}`);
  };

  const handleTopUp = () => {
    // TODO: Implement wallet top-up functionality
    router.push("/wallet");
  };

  // Get balance from student profile (in cents, convert to dollars)
  const balance = studentProfile?.credit_balance_cents ? (studentProfile.credit_balance_cents / 100).toFixed(2) : "0.00";

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header/Navbar */}
      <Navbar user={user} />

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 max-w-6xl flex-grow">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Welcome, {getUserDisplayName()}</h1>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push("/profile")}
              className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-2"
            >
              <Eye size={16} /> View Profile
            </button>
            <button
              onClick={() => router.push("/tutors")}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-bold hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 dark:focus:ring-offset-slate-900 shadow-lg shadow-emerald-500/20 transition-all active:scale-[0.98] flex items-center gap-2"
            >
              <Search size={16} /> Find Tutors
            </button>
          </div>
        </div>

      <div className="grid grid-cols-1 gap-8 mb-12">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-slate-500 dark:text-slate-400 font-medium mb-1">Available Credits</h3>
            <div className="text-3xl font-bold text-slate-900 dark:text-white">${balance}</div>
          </div>
          <button
            onClick={handleTopUp}
            className="self-start text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-500 dark:hover:text-emerald-300 font-medium flex items-center gap-1 mt-4 hover:underline transition-all"
          >
            <Wallet size={16} /> Top up wallet
          </button>
        </div>
      </div>

      {!loadingSavedTutors && savedTutors.length > 0 && (
        <div className="mb-12">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-slate-900 dark:text-white"><Heart size={20} className="text-emerald-500"/> Saved Tutors</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {savedTutors.map(tutor => (
              <TutorCard
                key={tutor.id}
                tutor={tutor}
                onViewProfile={() => handleViewProfile(tutor)}
                onToggleSave={handleToggleSave}
                onBook={handleBook}
                onQuickBook={handleQuickBook}
                onSlotBook={handleSlotBook}
                onMessage={handleMessage}
                isSaved={true}
              />
            ))}
          </div>
        </div>
      )}

      <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-slate-900 dark:text-white"><Calendar size={20}/> Your Sessions</h2>
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden">
        {mySessions.length === 0 ? (
          <div className="p-8 text-center text-slate-500">No sessions booked yet.</div>
        ) : mySessions.map((booking, idx) => {
          const isUpcoming =
            booking.status === "CONFIRMED" ||
            booking.status === "confirmed" ||
            booking.status === "PENDING" ||
            booking.status === "pending";
          const isCompleted =
            booking.status === "COMPLETED" || booking.status === "completed";
          const canJoin =
            isUpcoming &&
            (booking.status === "CONFIRMED" || booking.status === "confirmed") &&
            isJoinable(booking.start_at) &&
            booking.join_url;

          return (
            <div key={booking.id} className={`p-6 flex flex-col md:flex-row md:items-center justify-between gap-4 ${idx !== mySessions.length - 1 ? 'border-b border-slate-200 dark:border-slate-800' : ''}`}>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400">
                  {getSubjectIcon(booking.subject_name)}
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white">{booking.subject_name || booking.topic || "Session"} with {booking.tutor.name}</h4>
                  <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400 mt-1">
                    <span className="flex items-center gap-1"><Calendar size={14}/> {new Date(booking.start_at).toLocaleDateString()}</span>
                    <span className="flex items-center gap-1"><Clock size={14}/> {new Date(booking.start_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  </div>
                </div>
              </div>
              <div>
                {canJoin ? (
                  <button
                    onClick={() => handleStartSession(booking)}
                    className="w-full md:w-auto bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(5,150,105,0.4)] hover:-translate-y-0.5"
                  >
                    <Video size={18} /> Join Classroom
                  </button>
                ) : isCompleted ? (
                  <button
                    onClick={() => handleReviewSession(booking.id)}
                    className="w-full md:w-auto border border-emerald-500/50 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 px-6 py-2 rounded-lg font-medium transition-colors"
                  >
                    Rate & Review
                  </button>
                ) : (
                  <span className="inline-block px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-sm">
                    {booking.status.charAt(0).toUpperCase() + booking.status.slice(1).toLowerCase()}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
}
