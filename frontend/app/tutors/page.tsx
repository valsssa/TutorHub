"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { motion } from "framer-motion";
import Cookies from "js-cookie";
import { FiStar, FiUsers, FiBookOpen, FiAward, FiTrendingUp, FiCheck, FiArrowRight } from "react-icons/fi";
import { tutors, subjects, auth } from "@/lib/api";
import { TutorPublicSummary, Subject, PaginatedResponse, User } from "@/types";
import { useToast } from "@/components/ToastContainer";
import { useDebounce } from "@/hooks/useDebounce";
import LoadingSpinner from "@/components/LoadingSpinner";
import TutorCard from "@/components/TutorCard";
import TutorSearchSection from "@/components/TutorSearchSection";
import Pagination from "@/components/Pagination";
import PublicHeader from "@/components/PublicHeader";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Button from "@/components/Button";
import { DEFAULT_FILTERS, SORT_OPTIONS, PRICE_LIMITS } from "@/types/filters";

export default function TutorsPage() {
  return <TutorsContent />;
}

function TutorsContent(): JSX.Element {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showError } = useToast();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [paginatedData, setPaginatedData] = useState<PaginatedResponse<TutorPublicSummary> | null>(null);
  const [subjectsList, setSubjectsList] = useState<Subject[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSubject, setSelectedSubject] = useState<number | undefined>();
  const [priceRange, setPriceRange] = useState<[number, number]>([
    PRICE_LIMITS.min,
    PRICE_LIMITS.max,
  ]);
  const [minRating, setMinRating] = useState<number | undefined>();
  const [minExperience, setMinExperience] = useState<number | undefined>();
  const [sortBy, setSortBy] = useState<string>("rating");
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 20; // Show 20 tutors per page

  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  // Check authentication status
  useEffect(() => {
    const token = Cookies.get("token");
    if (token) {
      auth.getCurrentUser()
        .then(setCurrentUser)
        .catch(() => setCurrentUser(null));
    } else {
      setCurrentUser(null);
    }
  }, []);

  const activeFiltersCount = useMemo(() => {
    return (
      (selectedSubject ? 1 : 0) +
      (priceRange[0] !== PRICE_LIMITS.min || priceRange[1] !== PRICE_LIMITS.max
        ? 1
        : 0) +
      (minRating ? 1 : 0) +
      (minExperience ? 1 : 0)
    );
  }, [selectedSubject, priceRange, minRating, minExperience]);

  useEffect(() => {
    let mounted = true;
    subjects
      .list()
      .then((data) => {
        if (mounted) setSubjectsList(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (mounted) {
          showError("Failed to load subjects");
          setSubjectsList([]);
        }
      });
    return () => {
      mounted = false;
    };
  }, [showError]);

  const fetchTutors = useCallback(async () => {
    setLoading(true);
    try {
      const data = await tutors.list({
        subject_id: selectedSubject,
        min_rate: priceRange[0],
        max_rate: priceRange[1],
        min_rating: minRating,
        min_experience: minExperience,
        search_query: debouncedSearchTerm || undefined,
        sort_by: sortBy,
        page: currentPage,
        page_size: PAGE_SIZE,
      });
      setPaginatedData(data);
    } catch (error) {
      showError("Failed to load tutors");
      setPaginatedData(null);
    } finally {
      setLoading(false);
    }
  }, [
    selectedSubject,
    priceRange,
    minRating,
    minExperience,
    debouncedSearchTerm,
    sortBy,
    currentPage,
    showError,
  ]);

  useEffect(() => {
    fetchTutors();
  }, [fetchTutors]);

  const clearFilters = () => {
    setSearchTerm("");
    setSelectedSubject(undefined);
    setPriceRange([PRICE_LIMITS.min, PRICE_LIMITS.max]);
    setMinRating(undefined);
    setMinExperience(undefined);
    setCurrentPage(1); // Reset to first page when clearing filters
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // Scroll to top when changing pages
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedSubject, priceRange, minRating, minExperience, debouncedSearchTerm, sortBy]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200 flex flex-col">
      {/* Navigation Header */}
      {currentUser ? <Navbar user={currentUser} /> : <PublicHeader />}

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="container mx-auto px-4 py-8 md:py-12 lg:py-16 max-w-7xl">
          <div className="grid lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center lg:text-left relative z-10"
            >
              {/* Gradient Blur Background */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 lg:left-0 lg:translate-x-0 w-[300px] h-[300px] bg-emerald-400/20 rounded-full blur-[80px] -z-10" />

              {/* Trust Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-300 text-xs font-bold mb-6 border border-emerald-200 dark:border-emerald-800">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Over 30,000 trusted tutors
              </div>

              {/* Main Heading */}
              <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black text-slate-900 dark:text-white mb-4 sm:mb-6 tracking-tight leading-[1.1]">
                Find the <span className="text-emerald-600 dark:text-emerald-400">perfect tutor</span> for your goals
              </h1>

              {/* Subheading */}
              <p className="text-base sm:text-lg text-slate-600 dark:text-slate-400 max-w-xl mx-auto lg:mx-0 mb-6 sm:mb-8 leading-relaxed px-4 sm:px-0">
                Book 1-on-1 lessons with verified experts. Master any subject from the comfort of your home.
              </p>

              {/* Subject Pills */}
              <div className="flex flex-wrap justify-center lg:justify-start gap-2 mb-2 lg:mb-0">
                {['English', 'Mathematics', 'Spanish', 'Physics', 'Piano', 'Computer Science'].map((topic) => (
                  <button
                    key={topic}
                    onClick={() => setSearchTerm(topic)}
                    className="px-4 py-2 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 text-sm font-bold hover:border-emerald-500 hover:text-emerald-600 dark:hover:text-emerald-400 dark:hover:border-emerald-500 transition-all shadow-sm active:scale-95"
                  >
                    {topic}
                  </button>
                ))}
              </div>

              {/* CTA Buttons */}
              {!currentUser && (
                <div className="flex flex-col sm:flex-row flex-wrap gap-3 sm:gap-4 justify-center lg:justify-start mt-6 lg:mt-8">
                  <Button
                    onClick={() => router.push("/register")}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-bold text-base sm:text-lg shadow-lg shadow-emerald-500/20 w-full sm:w-auto"
                  >
                    Get Started Free
                  </Button>
                  <Button
                    onClick={() => router.push("/tutors")}
                    variant="outline"
                    className="px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-bold text-base sm:text-lg w-full sm:w-auto"
                  >
                    Browse Tutors
                  </Button>
                </div>
              )}

              {currentUser && (
                <Button
                  onClick={() => router.push(currentUser.role === 'admin' ? '/admin' : '/dashboard')}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 sm:px-8 py-3 sm:py-4 rounded-xl font-bold text-base sm:text-lg mt-6 lg:mt-8 w-full sm:w-auto"
                >
                  Go to Dashboard <FiArrowRight className="w-5 h-5" />
                </Button>
              )}
            </motion.div>

            {/* Right Image with Floating Cards */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="relative hidden lg:block"
            >
              {/* Background Gradient Shape */}
              <div className="absolute inset-0 bg-gradient-to-tr from-emerald-100 to-blue-100 dark:from-emerald-900/20 dark:to-blue-900/20 rounded-[40px] transform rotate-3 scale-95" />

              {/* Main Image */}
              <div className="relative w-full h-[300px] md:h-[400px] lg:h-[500px]">
                <Image
                  src="https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=1000&auto=format&fit=crop"
                  alt="Students learning together"
                  fill
                  className="rounded-[20px] lg:rounded-[40px] shadow-2xl object-cover border-4 lg:border-8 border-white dark:border-slate-800 transform -rotate-1 lg:-rotate-2 hover:rotate-0 transition-transform duration-700"
                  unoptimized
                />
              </div>

              {/* Floating Card - Bottom Left: Satisfaction Guaranteed */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
                className="absolute -bottom-4 -left-2 lg:-bottom-8 lg:-left-8 bg-white dark:bg-slate-800 p-3 lg:p-4 rounded-xl lg:rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700 flex items-center gap-3 lg:gap-4 max-w-[200px] lg:max-w-none"
              >
                <div className="bg-emerald-100 dark:bg-emerald-900/30 p-3 rounded-full text-emerald-600 dark:text-emerald-400">
                  <FiCheck className="w-6 h-6" strokeWidth={3} />
                </div>
                <div>
                  <p className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">Satisfaction</p>
                  <p className="text-lg font-black text-slate-900 dark:text-white">Guaranteed</p>
                </div>
              </motion.div>

              {/* Floating Card - Top Right: Average Rating */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.8 }}
                className="absolute top-8 -right-2 lg:top-12 lg:-right-8 bg-white dark:bg-slate-800 p-3 lg:p-4 rounded-xl lg:rounded-2xl shadow-xl border border-slate-100 dark:border-slate-700"
              >
                <div className="flex items-center gap-1 text-amber-400 mb-1">
                  {[1,2,3,4,5].map(i => (
                    <FiStar key={i} className="w-4 h-4 fill-current" />
                  ))}
                </div>
                <p className="text-sm font-bold text-slate-900 dark:text-white">4.9/5 Average Rating</p>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      <main className="flex-1">
        {/* Integrated Search Section */}
        <TutorSearchSection
          subjects={subjectsList}
          selectedSubject={selectedSubject}
          priceRange={priceRange}
          minRating={minRating}
          minExperience={minExperience}
          sortBy={sortBy}
          searchTerm={searchTerm}
          resultsCount={paginatedData?.total || 0}
          onSubjectChange={setSelectedSubject}
          onPriceChange={setPriceRange}
          onMinRatingChange={setMinRating}
          onMinExperienceChange={setMinExperience}
          onSortChange={setSortBy}
          onSearchChange={setSearchTerm}
          onUpdate={fetchTutors}
        />

        <div className="max-w-7xl mx-auto px-4 py-6 md:py-8">

          {/* Results Section */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <LoadingSpinner />
              <p className="text-slate-600 mt-4">Finding the best tutors for you...</p>
            </div>
          ) : paginatedData && paginatedData.items.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {paginatedData.items.map((tutor) => (
                  <TutorCard key={tutor.id} tutor={tutor} />
                ))}
              </div>

              {/* Pagination */}
              {paginatedData.total_pages > 1 && (
                <Pagination
                  currentPage={paginatedData.page}
                  totalPages={paginatedData.total_pages}
                  onPageChange={handlePageChange}
                  hasNext={paginatedData.has_next}
                  hasPrev={paginatedData.has_prev}
                  totalItems={paginatedData.total}
                />
              )}
            </>
          ) : (
            <div className="text-center py-16 bg-gradient-to-br from-slate-50 to-slate-100 rounded-2xl border border-slate-200">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-2xl font-bold text-slate-900 mb-2">
                No Tutors Found
              </h3>
              <p className="text-slate-600 mb-6 max-w-md mx-auto">
                {activeFiltersCount > 0
                  ? "Try adjusting your filters to see more results"
                  : "No tutors match your search"}
              </p>
              {activeFiltersCount > 0 && (
                <button
                  onClick={clearFilters}
                  className="px-6 py-3 bg-gradient-to-r from-sky-500 to-blue-500 text-white rounded-xl font-semibold hover:shadow-lg transition-all"
                >
                  Clear All Filters
                </button>
              )}
              <p className="text-sm text-slate-500 mt-6">
                💡 Tip: Try broadening your search criteria
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
