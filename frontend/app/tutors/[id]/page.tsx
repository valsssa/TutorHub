"use client";

import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import { useRouter, useParams } from "next/navigation";
import {
  FiStar,
  FiDollarSign,
  FiBook,
  FiClock,
  FiAward,
  FiGlobe,
  FiVideo,
  FiCalendar,
  FiUser,
  FiMessageSquare,
} from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import {
  tutors,
  bookings as bookingsApi,
  subjects as subjectsApi,
} from "@/lib/api";
import { authUtils } from "@/lib/auth";
import { resolveAssetUrl } from "@/lib/media";
import type { TutorProfile, User, Subject } from "@/types";
import { useToast } from "@/components/ToastContainer";
import Button from "@/components/Button";
import LoadingSpinner from "@/components/LoadingSpinner";
import ModernBookingModal from "@/components/ModernBookingModal";
import { TutorProfileSkeleton } from "@/components/SkeletonLoader";
import { auth } from "@/lib/api";

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
  const [reviews, setReviews] = useState<any[]>([]);

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

  if (loading || !tutor) {
    return <TutorProfileSkeleton />;
  }

  const canBook = user && authUtils.isStudent(user);
  const averageRating = Number(tutor.average_rating);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="bg-white rounded-2xl shadow-soft p-6 mb-8 animate-fadeIn">
        <div className="flex flex-col md:flex-row gap-6">
          {/* Profile Photo */}
          <div className="flex-shrink-0">
            {tutor.profile_photo_url ? (
              <div className="relative group">
                <Image
                  src={resolveAssetUrl(tutor.profile_photo_url)}
                  alt={tutor.title}
                  width={128}
                  height={128}
                  className="w-32 h-32 rounded-full object-cover border-4 border-primary-100 shadow-lg transition-transform group-hover:scale-105"
                  unoptimized
                />
                <div className="absolute inset-0 rounded-full bg-gradient-to-t from-primary-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            ) : (
              <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary-100 to-pink-100 flex items-center justify-center shadow-lg">
                <FiUser className="w-16 h-16 text-primary-400" />
              </div>
            )}
          </div>

          {/* Profile Info */}
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {tutor.title}
            </h1>
            {tutor.headline && (
              <p className="text-lg text-gray-600 mb-4">{tutor.headline}</p>
            )}

            {/* Stats */}
            <div className="flex flex-wrap gap-4 mb-4">
              <div className="flex items-center gap-3 group/stat">
                <div className="bg-gradient-to-br from-yellow-50 to-amber-50 p-3 rounded-xl group-hover/stat:scale-110 transition-transform shadow-sm">
                  <FiStar className="w-5 h-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">Rating</p>
                  <p className="font-bold text-gray-900">
                    {averageRating.toFixed(1)} <span className="text-sm font-normal text-gray-600">({tutor.total_reviews} reviews)</span>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 group/stat">
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-3 rounded-xl group-hover/stat:scale-110 transition-transform shadow-sm">
                  <FiDollarSign className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">Lesson Price</p>
                  <p className="font-bold text-gray-900">
                    ${tutor.hourly_rate} / 50 min
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 group/stat">
                <div className="bg-gradient-to-br from-blue-50 to-sky-50 p-3 rounded-xl group-hover/stat:scale-110 transition-transform shadow-sm">
                  <FiBook className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">Sessions</p>
                  <p className="font-bold text-gray-900">
                    {tutor.total_sessions}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 group/stat">
                <div className="bg-gradient-to-br from-purple-50 to-violet-50 p-3 rounded-xl group-hover/stat:scale-110 transition-transform shadow-sm">
                  <FiClock className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-xs text-gray-500 font-medium">Experience</p>
                  <p className="font-bold text-gray-900">
                    {tutor.experience_years} years
                  </p>
                </div>
              </div>
            </div>

            {/* Languages */}
            {tutor.languages && tutor.languages.length > 0 && (
              <div className="flex items-center gap-2 mb-4">
                <FiGlobe className="w-5 h-5 text-primary-500" />
                <span className="text-sm text-gray-700 font-medium">
                  Speaks: <span className="text-gray-900">{tutor.languages.join(", ")}</span>
                </span>
              </div>
            )}

            {/* Action Button */}
            {canBook && (
              <div className="flex flex-col sm:flex-row gap-3 mt-6">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={() => setShowBookingModal(true)}
                  className="shadow-lg hover:shadow-xl animate-pulse-soft flex items-center justify-center gap-2"
                >
                  <FiCalendar className="w-5 h-5" />
                  Book a Session
                </Button>
                <Button
                  variant="secondary"
                  size="lg"
                  onClick={() => router.push(`/messages?tutor=${tutorId}`)}
                  className="flex items-center justify-center gap-2"
                >
                  <FiMessageSquare className="w-5 h-5" />
                  Send Message
                </Button>
                <Button
                  variant="ghost"
                  size="lg"
                  onClick={() => {/* Add to favorites */}}
                  className="border-2 border-gray-200 hover:border-primary-300"
                >
                  <span className="flex items-center justify-center gap-2">
                    💝 Save Tutor
                  </span>
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* About */}
          {tutor.bio && (
            <div className="bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-shadow">
              <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FiUser className="w-6 h-6 text-primary-500" />
                About Me
              </h2>
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">{tutor.bio}</p>
            </div>
          )}

          {/* Detailed Description */}
          {tutor.description && (
            <div className="bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-shadow">
              <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FiBook className="w-6 h-6 text-primary-500" />
                Teaching Approach
              </h2>
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                {tutor.description}
              </p>
            </div>
          )}

          {/* Video Introduction */}
          {tutor.video_url && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FiVideo /> Introduction Video
              </h2>
              <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
                <a
                  href={tutor.video_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-600 hover:text-primary-700 underline flex items-center gap-2"
                >
                  <FiVideo className="w-5 h-5" />
                  Watch Introduction Video
                </a>
              </div>
            </div>
          )}

          {/* Reviews */}
          <div className="bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-shadow">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <FiStar className="w-6 h-6 text-yellow-500" />
              Student Reviews
            </h2>
            {reviews.length > 0 ? (
              <div className="space-y-6">
                {reviews.map((review) => (
                  <div
                    key={review.id}
                    className="border-l-4 border-primary-200 pl-4 pb-4 last:pb-0 hover:border-primary-400 transition-colors"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="flex items-center bg-gradient-to-r from-yellow-50 to-amber-50 px-3 py-1.5 rounded-full">
                        {[...Array(5)].map((_, i) => (
                          <FiStar
                            key={i}
                            className={`w-4 h-4 ${
                              i < review.rating
                                ? "text-yellow-500 fill-current"
                                : "text-gray-300"
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-sm text-gray-500 font-medium">
                        {new Date(review.created_at).toLocaleDateString('en-US', { 
                          month: 'short', 
                          day: 'numeric', 
                          year: 'numeric' 
                        })}
                      </span>
                    </div>
                    {review.comment && (
                      <p className="text-gray-700 leading-relaxed italic">&ldquo;{review.comment}&rdquo;</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <FiStar className="w-8 h-8 text-gray-400" />
                </div>
                <p className="text-gray-500 font-medium">No reviews yet</p>
                <p className="text-sm text-gray-400 mt-1">Be the first to review this tutor!</p>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Subjects */}
          {tutor.subjects && tutor.subjects.length > 0 && (
            <div className="bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-shadow">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FiBook className="w-5 h-5 text-primary-500" /> 
                Subjects
              </h3>
              <div className="space-y-3">
                {tutor.subjects.map((subject) => (
                  <div
                    key={subject.id}
                    className="bg-gradient-to-r from-primary-50 to-pink-50 border-l-4 border-primary-500 rounded-r-xl pl-4 py-3 hover:shadow-sm transition-shadow"
                  >
                    <p className="font-semibold text-gray-900">
                      {subject.subject_name}
                    </p>
                    <p className="text-sm text-gray-600 capitalize font-medium">
                      {subject.proficiency_level} • {subject.years_experience}{" "}
                      years exp.
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Certifications */}
          {tutor.certifications && tutor.certifications.length > 0 && (
            <div className="bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-shadow">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FiAward className="w-5 h-5 text-accent-500" /> 
                Certifications
              </h3>
              <div className="space-y-3">
                {tutor.certifications.map((cert) => (
                  <div key={cert.id} className="bg-gradient-to-r from-accent-50 to-amber-50 rounded-xl p-3 hover:shadow-sm transition-shadow">
                    <p className="font-semibold text-gray-900 flex items-center gap-2">
                      🏆 {cert.name}
                    </p>
                    {cert.issuing_organization && (
                      <p className="text-sm text-gray-600 mt-1 font-medium">
                        {cert.issuing_organization}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {tutor.educations && tutor.educations.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Education
              </h3>
              <div className="space-y-3">
                {tutor.educations.map((edu) => (
                  <div key={edu.id}>
                    <p className="font-medium text-gray-900">
                      {edu.institution}
                    </p>
                    {edu.degree && (
                      <p className="text-sm text-gray-600">{edu.degree}</p>
                    )}
                    {(edu.start_year || edu.end_year) && (
                      <p className="text-xs text-gray-500">
                        {edu.start_year} - {edu.end_year || "Present"}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pricing Options */}
          {tutor.pricing_options && tutor.pricing_options.length > 0 && (
            <div className="bg-white rounded-2xl shadow-soft p-6 hover:shadow-soft-lg transition-shadow">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <FiDollarSign className="w-5 h-5 text-green-600" />
                Lesson Packages
              </h3>
              <div className="space-y-3">
                {tutor.pricing_options.map((option) => (
                  <div
                    key={option.id}
                    className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl p-4 hover:border-green-300 hover:shadow-md transition-all"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <p className="font-bold text-gray-900">
                        {option.title}
                      </p>
                      <p className="font-bold text-green-600 text-lg">
                        ${option.price}
                      </p>
                    </div>
                    <p className="text-sm text-gray-700 font-medium flex items-center gap-1">
                      <FiClock className="w-3 h-3" />
                      {option.duration_minutes} minutes
                    </p>
                    {option.description && (
                      <p className="text-sm text-gray-600 mt-2 leading-relaxed">
                        {option.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Booking Modal */}
      {showBookingModal && (
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
    </div>
  );
}
