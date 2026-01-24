"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import { auth, bookings, tutors } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { User, TutorProfile } from "@/types";
import { BookingDTO } from "@/types/booking";
import { useToast } from "@/components/ToastContainer";
import StudentDashboard from "@/components/dashboards/StudentDashboard";
import TutorDashboard from "@/components/dashboards/TutorDashboard";
import AdminDashboard from "@/components/dashboards/AdminDashboard";

export default function DashboardPage() {
  return (
    <ProtectedRoute showNavbar={false}>
      <DashboardContent />
    </ProtectedRoute>
  );
}

function DashboardContent() {
  const router = useRouter();
  const { showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [userBookings, setUserBookings] = useState<BookingDTO[]>([]);
  const [tutorProfile, setTutorProfile] = useState<TutorProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const handleAvatarChange = (url: string | null) => {
    setUser((prev) =>
      prev
        ? {
            ...prev,
            avatarUrl: url,
            avatar_url: url ?? null,
          }
        : prev,
    );
  };

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        // Parallel API calls for faster loading
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);

        // Load tutor profile only if needed
        if (authUtils.isTutor(currentUser)) {
          try {
            const profile = await tutors.getMyProfile();
            setTutorProfile(profile);
          } catch (error) {
            // Tutor might not have profile yet
          }
        }

        // Load actual bookings for dashboard
        try {
          const bookingData = await bookings.list({
            role: currentUser.role as "student" | "tutor",
            page: 1,
            page_size: 20,
          });
          setUserBookings(bookingData.bookings || []);
        } catch (error) {
          console.error("Failed to load bookings:", error);
          setUserBookings([]);
        }
      } catch (error) {
        showError("Failed to load dashboard data");
        setUserBookings([]);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [showError]);

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-emerald-200 dark:border-emerald-800 border-t-emerald-600 dark:border-t-emerald-400"></div>
      </div>
    );
  }

  if (authUtils.isStudent(user)) {
    return (
      <StudentDashboard
        user={user}
        bookings={userBookings}
        onAvatarChange={handleAvatarChange}
      />
    );
  }

  if (authUtils.isTutor(user)) {
    return (
      <TutorDashboard
        user={user}
        bookings={userBookings}
        profile={tutorProfile}
        verificationStatus={tutorProfile?.is_approved ? 'verified' : tutorProfile?.profile_status === 'pending_approval' ? 'pending' : 'unverified'}
        onAvatarChange={handleAvatarChange}
        onProfileUpdate={(updated) => setTutorProfile(updated)}
        onEditProfile={() => router.push("/tutor/profile")}
        onViewProfile={() => router.push("/tutor/profile")}
        onUpdateSchedule={(mode) => router.push("/tutor/availability")}
        onViewCalendar={() => router.push("/bookings")}
        onManageVerification={() => router.push("/tutor/profile")}
        onViewEarnings={() => router.push("/bookings")}
        onViewStudents={() => router.push("/bookings")}
      />
    );
  }

  if (authUtils.isAdmin(user)) {
    return <AdminDashboard user={user} onAvatarChange={handleAvatarChange} />;
  }

  return null;
}
