"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { User, TutorPublicSummary, StudentProfile } from "@/types";
import { BookingDTO } from "@/types/booking";
import { favorites, tutors, students } from "@/lib/api";
import { getGreetingName } from "@/lib/displayName";
import { useToast } from "@/components/ToastContainer";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import StudentHero from "./student/StudentHero";
import StudentStatsGrid from "./student/StudentStatsGrid";
import StudentSessionsList from "./student/StudentSessionsList";
import StudentSavedTutorsPanel from "./student/StudentSavedTutorsPanel";
import StudentSavedTutorsGrid from "./student/StudentSavedTutorsGrid";

interface StudentDashboardProps {
  user: User;
  bookings: BookingDTO[];
  onAvatarChange: (url: string | null) => void;
}

export default function StudentDashboard({ user, bookings, onAvatarChange: _onAvatarChange }: StudentDashboardProps) {
  const router = useRouter();
  const { showError } = useToast();

  const [savedTutors, setSavedTutors] = useState<TutorPublicSummary[]>([]);
  const [studentProfile, setStudentProfile] = useState<StudentProfile | null>(null);
  const [loadingSavedTutors, setLoadingSavedTutors] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoadingSavedTutors(true);

        try {
          const profile = await students.getProfile();
          setStudentProfile(profile);
        } catch {
          // Profile may not exist yet; continue rendering.
        }

        const userFavorites = await favorites.getFavorites();
        if (userFavorites.length === 0) {
          setSavedTutors([]);
        } else {
          const tutorProfiles = await Promise.all(
            userFavorites.map((fav) => tutors.getPublic(fav.tutor_profile_id)),
          );
          setSavedTutors(tutorProfiles);
        }
      } catch (error: any) {
        showError(error.response?.data?.detail || "Failed to load dashboard data");
        setSavedTutors([]);
      } finally {
        setLoadingSavedTutors(false);
      }
    };

    loadDashboardData();
  }, [showError]);

  const mySessions = useMemo(
    () => bookings.filter((booking) => booking.student.id === user.id),
    [bookings, user.id],
  );

  const sortedSessions = useMemo(
    () =>
      [...mySessions].sort(
        (a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime(),
      ),
    [mySessions],
  );

  const upcomingSessions = useMemo(
    () => {
      const now = new Date();
      return sortedSessions.filter((booking) => {
        // Use session_state (four-field system) with fallback to legacy status
        const sessionState = (booking.session_state || booking.status || "").toUpperCase();
        const start = new Date(booking.start_at).getTime();
        return (
          (sessionState === "REQUESTED" || sessionState === "SCHEDULED" || sessionState === "ACTIVE") &&
          start >= now.getTime() - 60 * 60 * 1000
        );
      });
    },
    [sortedSessions],
  );

  const nextSession = upcomingSessions[0];

  const monthlySessionCount = useMemo(() => {
    const now = new Date();
    const month = now.getMonth();
    const year = now.getFullYear();
    return mySessions.filter((session) => {
      const start = new Date(session.start_at);
      return start.getMonth() === month && start.getFullYear() === year;
    }).length;
  }, [mySessions]);

  const totalHours = useMemo(() => {
    return mySessions.reduce((total, session) => {
      const start = new Date(session.start_at).getTime();
      const end = new Date(session.end_at || session.start_at).getTime();
      const duration = Math.max(end - start, 0) / (1000 * 60 * 60);
      return total + duration;
    }, 0);
  }, [mySessions]);

  const balance = studentProfile?.credit_balance_cents
    ? (studentProfile.credit_balance_cents / 100).toFixed(2)
    : "0.00";

  // Use centralized display name utility for consistent greeting
  const getUserDisplayName = (): string => getGreetingName(user);

  const isJoinable = (startAt: string): boolean => {
    const now = new Date().getTime();
    const start = new Date(startAt).getTime();
    const diff = start - now;
    return diff <= 15 * 60 * 1000 && diff >= -60 * 60 * 1000;
  };

  const handleStartSession = (booking: BookingDTO) => {
    if (booking.join_url) {
      window.open(booking.join_url, "_blank", "noopener,noreferrer");
    } else {
      showError("No meeting link available");
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
      setSavedTutors((prev) => prev.filter((tutor) => tutor.id !== tutorId));
    } catch (error: any) {
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

  const handleEditProfile = () => router.push("/profile");

  const handleTopUp = () => router.push("/wallet");

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-slate-950">
      <Navbar user={user} />

      <main className="flex-grow bg-gradient-to-b from-emerald-50 via-white to-slate-50 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900">
        <div className="container mx-auto max-w-6xl px-4 pb-16 pt-10">
          <StudentHero
            name={getUserDisplayName()}
            balance={balance}
            nextSession={nextSession}
            onBookTutor={() => router.push("/tutors")}
            onViewBookings={() => router.push("/bookings")}
            onMessages={() => router.push("/messages")}
            onTopUp={handleTopUp}
            onEditProfile={handleEditProfile}
          />

          <StudentStatsGrid
            balance={balance}
            upcomingCount={upcomingSessions.length}
            monthlyCount={monthlySessionCount}
            totalHours={totalHours.toFixed(1)}
          />

          <section className="mt-10 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <StudentSessionsList
                sessions={sortedSessions}
                onJoin={handleStartSession}
                onReview={handleReviewSession}
                isJoinable={isJoinable}
                onManageAll={() => router.push("/bookings")}
              />
            </div>
            <StudentSavedTutorsPanel
              loading={loadingSavedTutors}
              savedTutors={savedTutors}
              nextSession={nextSession}
              isJoinable={isJoinable}
              onJoin={handleStartSession}
              onViewProfile={handleViewProfile}
              onViewAll={() => router.push("/saved-tutors")}
              onBookNow={() => router.push("/tutors")}
            />
          </section>

          {savedTutors.length > 0 && (
            <StudentSavedTutorsGrid
              savedTutors={savedTutors}
              onViewProfile={handleViewProfile}
              onToggleSave={handleToggleSave}
              onBook={handleBook}
              onQuickBook={handleQuickBook}
              onSlotBook={handleSlotBook}
              onMessage={handleMessage}
            />
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
