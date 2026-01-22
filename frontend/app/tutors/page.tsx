"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Cookies from "js-cookie";
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
              {paginatedData.pages > 1 && (
                <Pagination
                  currentPage={paginatedData.page}
                  totalPages={paginatedData.pages}
                  onPageChange={handlePageChange}
                  hasNext={paginatedData.page < paginatedData.pages}
                  hasPrev={paginatedData.page > 1}
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
