"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import Cookies from "js-cookie";
import { FiHeart, FiSearch, FiArrowRight, FiBook } from "react-icons/fi";
import { auth, favorites, tutors } from "@/lib/api";
import { User, FavoriteTutor, TutorPublicSummary } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Button from "@/components/Button";
import TutorCard from "@/components/TutorCard";

export default function SavedTutorsPage() {
  return <SavedTutorsContent />;
}

function SavedTutorsContent() {
  const router = useRouter();
  const { showError, showSuccess } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [favoritesList, setFavoritesList] = useState<FavoriteTutor[]>([]);
  const [favoriteTutors, setFavoriteTutors] = useState<TutorPublicSummary[]>([]);
  const [tutorsLoading, setTutorsLoading] = useState(false);

  const loadFavorites = async (currentUser: User) => {
    try {
      setTutorsLoading(true);

      // Get user's favorites
      const userFavorites = await favorites.getFavorites();
      setFavoritesList(userFavorites);

      if (userFavorites.length > 0) {
        // Get tutor profiles for each favorite
        const tutorIds = userFavorites.map(fav => fav.tutor_profile_id);
        const tutorPromises = tutorIds.map(id => tutors.getPublic(id));
        const tutorProfiles = await Promise.all(tutorPromises);
        setFavoriteTutors(tutorProfiles);
      } else {
        setFavoriteTutors([]);
      }
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to load favorite tutors");
      setFavoriteTutors([]);
    } finally {
      setTutorsLoading(false);
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = Cookies.get("token");
        if (!token) {
          router.push("/login");
          return;
        }

        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);

        // Load favorites after authentication
        await loadFavorites(currentUser);
      } catch (error) {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  const handleRemoveFavorite = async (e: React.MouseEvent, tutorId: number) => {
    e.stopPropagation();

    if (!user) return;

    try {
      await favorites.removeFavorite(tutorId);

      // Update local state
      setFavoritesList(prev => prev.filter(fav => fav.tutor_profile_id !== tutorId));
      setFavoriteTutors(prev => prev.filter(tutor => tutor.id !== tutorId));

      showSuccess("Tutor removed from favorites");
    } catch (error: any) {
      showError(error.response?.data?.detail || "Failed to remove from favorites");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200 flex flex-col">
        {/* Simple loading header */}
        <div className="sticky top-0 z-40 w-full border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md transition-colors duration-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shadow-sm">
                <FiBook className="text-white w-5 h-5" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-emerald-500 to-emerald-700 dark:from-emerald-400 dark:to-emerald-600 bg-clip-text text-transparent hidden sm:inline">
                EduConnect
              </span>
            </div>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect to login
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200 flex flex-col">
      <Navbar user={user} />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-8 pb-12">
        <div className="container mx-auto px-4 max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            {/* Gradient Blur Background */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[400px] h-[400px] bg-emerald-400/20 rounded-full blur-[100px] -z-10" />

            {/* Heart Icon */}
            <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-100 dark:bg-emerald-900/30 rounded-full mb-6">
              <FiHeart className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
            </div>

            {/* Main Heading */}
            <h1 className="text-4xl md:text-5xl font-black text-slate-900 dark:text-white mb-4 tracking-tight">
              Your Saved Tutors
            </h1>

            {/* Subheading */}
            <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
              Keep track of tutors you&apos;re interested in and easily access them later. Save tutors while browsing to build your personalized list.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Content Section */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {tutorsLoading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <LoadingSpinner />
              <p className="text-slate-600 mt-4">Loading your favorite tutors...</p>
            </div>
          ) : favoriteTutors.length > 0 ? (
            <>
              {/* Results Header */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
                className="mb-8"
              >
                <div className="flex items-center gap-3 mb-2">
                  <FiHeart className="w-6 h-6 text-emerald-500" />
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
                    Your Saved Tutors ({favoriteTutors.length})
                  </h2>
                </div>
                <p className="text-slate-600 dark:text-slate-400">
                  Keep track of tutors you&apos;re interested in and easily access them later.
                </p>
              </motion.div>

              {/* Tutors Grid */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              >
                {favoriteTutors.map((tutor) => (
                  <TutorCard
                    key={tutor.id}
                    tutor={tutor}
                    isSaved={true}
                    onToggleSave={handleRemoveFavorite}
                  />
                ))}
              </motion.div>
            </>
          ) : (
            /* Empty State */
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-center py-20 bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-sm"
            >
              {/* Large Heart Icon */}
              <div className="text-8xl mb-6 text-slate-300 dark:text-slate-600">
                <FiHeart />
              </div>

              {/* Title */}
              <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
                No Saved Tutors Yet
              </h2>

              {/* Description */}
              <p className="text-slate-600 dark:text-slate-400 mb-8 max-w-md mx-auto leading-relaxed">
                Start exploring tutors and save the ones you&apos;re interested in. They&apos;ll appear here for easy access.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  onClick={() => router.push("/tutors")}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-8 py-3 rounded-xl font-bold shadow-lg shadow-emerald-500/20"
                >
                  <FiSearch className="w-5 h-5 mr-2" />
                  Browse Tutors
                </Button>
                <Button
                  onClick={() => router.push("/dashboard")}
                  variant="outline"
                  className="px-8 py-3 rounded-xl font-bold"
                >
                  Go to Dashboard
                  <FiArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </div>

              {/* Tip */}
              <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800 max-w-md mx-auto">
                <p className="text-sm text-blue-800 dark:text-blue-300">
                  💡 <strong>Tip:</strong> Look for the heart icon on tutor profiles to save them to your list.
                </p>
              </div>
            </motion.div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}