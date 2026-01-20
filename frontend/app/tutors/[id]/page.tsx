"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import ProtectedRoute from "@/components/ProtectedRoute";
import {
  tutors,
  subjects as subjectsApi,
  auth,
} from "@/lib/api";
import { authUtils } from "@/lib/auth";
import type { TutorProfile, User, Subject, Review } from "@/types";
import { useToast } from "@/components/ToastContainer";
import ModernBookingModal from "@/components/ModernBookingModal";
import { TutorProfileSkeleton } from "@/components/SkeletonLoader";
import TutorProfileView from "@/components/TutorProfileView";

export default function TutorDetailPage() {
  return (
    <ProtectedRoute>
      <TutorDetailContent />
    </ProtectedRoute>
  );
}

function TutorDetailContent() {
  const router = useRouter();
  const params = useParams();
  const { showSuccess, showError } = useToast();
  const [tutor, setTutor] = useState<TutorProfile | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isSaved, setIsSaved] = useState(false);

  const tutorId = params?.id ? Number(params.id) : null;

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

  const handleToggleSave = (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    setIsSaved(!isSaved);
    // TODO: Implement save to favorites API
    if (!isSaved) {
      showSuccess("Tutor saved to favorites");
    }
  };

  const handleMessage = () => {
    if (tutorId) {
      router.push(`/messages?tutor=${tutorId}`);
    }
  };

  if (loading || !tutor) {
    return <TutorProfileSkeleton />;
  }

  const canBook = user && authUtils.isStudent(user);
  const isOwnProfile = !!(user && authUtils.isTutor(user) && tutor.user_id === user.id);

  return (
    <>
      <TutorProfileView
        tutor={tutor}
        reviews={reviews}
        subjects={subjectsList}
        onBook={() => canBook && setShowBookingModal(true)}
        onMessage={handleMessage}
        isOwnProfile={isOwnProfile}
        onEdit={() => router.push("/tutor/profile")}
        onToggleSave={canBook ? handleToggleSave : undefined}
        isSaved={isSaved}
        backHref="/tutors"
        backLabel="Back to Marketplace"
      />

      {/* Booking Modal */}
      {showBookingModal && canBook && (
        <ModernBookingModal
          tutor={tutor}
          subjects={subjectsList}
          onClose={() => setShowBookingModal(false)}
          onSuccess={() => {
            setShowBookingModal(false);
            showSuccess("Booking request submitted successfully");
            router.push("/bookings");
          }}
        />
      )}
    </>
  );
}
