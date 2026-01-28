"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { tutors, subjects as subjectsApi, auth, favorites } from "@/lib/api";
import { authUtils } from "@/lib/auth";
import type { TutorProfile, User, Subject, Review } from "@/types";
import { useToast } from "@/components/ToastContainer";
import { TutorProfileSkeleton } from "@/components/SkeletonLoader";
import TutorProfileView from "@/components/TutorProfileView";
import Cookies from "js-cookie";
import PublicHeader from "@/components/PublicHeader";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function TutorDetailPage() {
  return <TutorDetailContent />;
}

function TutorDetailContent() {
  const router = useRouter();
  const params = useParams();
  const { showSuccess, showError } = useToast();
  const [tutor, setTutor] = useState<TutorProfile | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isSaved, setIsSaved] = useState(false);

  const tutorId = params?.id ? Number(params.id) : null;

  const loadData = useCallback(async () => {
    if (!tutorId) return;

    setLoading(true);
    try {
      // Load tutor data and subjects (always available)
      const [tutorData, subjectsData, reviewsData] = await Promise.all([
        tutors.get(tutorId),
        subjectsApi.list(),
        tutors.getReviews(tutorId),
      ]);

      setTutor(tutorData);
      setSubjectsList(subjectsData);
      setReviews(reviewsData);

      // Try to get current user (optional for public access)
      try {
        const token = Cookies.get("token");
        if (token) {
          const currentUser = await auth.getCurrentUser();
          setUser(currentUser);

          // Check if tutor is favorited by current user (only for students)
          if (authUtils.isStudent(currentUser)) {
            try {
              const favorite = await favorites.checkFavorite(tutorId);
              setIsSaved(Boolean(favorite));
            } catch (favoriteError: any) {
              // If 404, tutor is not favorited (normal case)
              // If 403, user is not a student (also normal)
              if (favoriteError.response?.status !== 404 && favoriteError.response?.status !== 403) {
                console.error("Error checking favorite:", favoriteError);
              }
              setIsSaved(false);
            }
          } else {
            setIsSaved(false);
          }
        }
      } catch (authError) {
        // User is not authenticated, which is fine for public access
        setUser(null);
        setIsSaved(false);
      }
    } catch (error) {
      showError("Failed to load tutor profile");
      router.push("/tutors");
    } finally {
      setLoading(false);
    }
  }, [router, showError, tutorId]);

  useEffect(() => {
    if (tutorId) {
      loadData();
    }
  }, [tutorId, loadData]);

  const handleToggleSave = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();

    // Check if user is authenticated
    if (!user) {
      router.push("/login");
      return;
    }

    // Only students can save favorites
    if (!authUtils.isStudent(user)) {
      showError("Only students can save tutors to favorites");
      return;
    }

    try {
      if (isSaved) {
        await favorites.removeFavorite(id);
        setIsSaved(false);
        showSuccess("Tutor removed from favorites");
      } else {
        await favorites.addFavorite(id);
        setIsSaved(true);
        showSuccess("Tutor saved to favorites");
      }
    } catch (error: any) {
      console.error("Error toggling favorite:", error);
      const errorMessage = error.response?.data?.detail || "Failed to update favorites";
      showError(errorMessage);
      
      // If error is 403, user might not be a student
      if (error.response?.status === 403) {
        setIsSaved(false);
      }
    }
  };

  const handleMessage = () => {
    // Check if user is authenticated
    if (!user) {
      // Redirect to login page
      router.push("/login");
      return;
    }

    if (tutor?.user_id) {
      router.push(`/messages?user=${tutor.user_id}`);
    }
  };

  // When a time slot is selected, navigate to the booking page
  const handleBookSlot = (slotIso: string) => {
    if (!tutorId) return;

    // Check if user is authenticated
    if (!user) {
      // Redirect to login page
      router.push("/login");
      return;
    }

    // Only students can book
    if (!authUtils.isStudent(user)) {
      showError("Only students can book lessons");
      return;
    }

    // Navigate to booking page with selected slot
    const encodedSlot = encodeURIComponent(slotIso);
    router.push(`/tutors/${tutorId}/book?slot=${encodedSlot}`);
  };

  if (loading || !tutor) {
    return <TutorProfileSkeleton />;
  }

  const canBook = user && authUtils.isStudent(user);
  const isOwnProfile = !!(
    user &&
    authUtils.isTutor(user) &&
    tutor.user_id === user.id
  );

  // Show save button to all authenticated users (handler will check if they're a student)
  const canSave = !!user && !isOwnProfile;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col transition-colors duration-200">
      {/* Navigation Header */}
      {user ? <Navbar user={user} /> : <PublicHeader />}

      <main className="flex-1">
        <TutorProfileView
          tutor={tutor}
          reviews={reviews}
          subjects={subjectsList}
          onBookSlot={handleBookSlot}
          onMessage={handleMessage}
          isOwnProfile={isOwnProfile}
          onEdit={() => router.push("/tutor/profile")}
          onToggleSave={canSave ? handleToggleSave : undefined}
          isSaved={isSaved}
          backHref="/tutors"
          backLabel="Back to Marketplace"
        />
      </main>

      <Footer />
    </div>
  );
}
