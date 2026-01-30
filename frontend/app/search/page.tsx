"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  Search,
  Filter,
  X,
  ChevronDown,
  Star,
  Clock,
  DollarSign,
  MapPin,
  SlidersHorizontal,
  Grid,
  List,
  ArrowUpDown,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import Input from "@/components/Input";
import Select from "@/components/Select";
import LoadingSpinner from "@/components/LoadingSpinner";
import EmptyState from "@/components/EmptyState";
import TutorCard from "@/components/TutorCard";
import { TutorCardSkeleton } from "@/components/SkeletonLoader";
import { tutors as tutorsApi } from "@/lib/api";
import type { TutorPublicSummary } from "@/types";
import clsx from "clsx";

const SUBJECTS = [
  "Mathematics",
  "Physics",
  "Chemistry",
  "Biology",
  "English",
  "History",
  "Computer Science",
  "Music",
  "Art",
  "Economics",
];

const PRICE_RANGES = [
  { value: "", label: "Any price" },
  { value: "0-25", label: "Under $25/hr" },
  { value: "25-50", label: "$25 - $50/hr" },
  { value: "50-100", label: "$50 - $100/hr" },
  { value: "100+", label: "$100+/hr" },
];

const SORT_OPTIONS = [
  { value: "relevance", label: "Most Relevant" },
  { value: "rating", label: "Highest Rated" },
  { value: "price_asc", label: "Price: Low to High" },
  { value: "price_desc", label: "Price: High to Low" },
  { value: "sessions", label: "Most Sessions" },
];

interface Filters {
  query: string;
  subjects: string[];
  priceRange: string;
  minRating: number;
  availability: string;
  sort: string;
}

export default function SearchPage() {
  return (
    <ProtectedRoute>
      <SearchContent />
    </ProtectedRoute>
  );
}

function SearchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [tutors, setTutors] = useState<TutorPublicSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Initialize filters from URL params
  const initialFilters = useMemo<Filters>(() => ({
    query: searchParams?.get("q") || "",
    subjects: searchParams?.get("subjects")?.split(",").filter(Boolean) || [],
    priceRange: searchParams?.get("price") || "",
    minRating: parseFloat(searchParams?.get("rating") || "0"),
    availability: searchParams?.get("availability") || "",
    sort: searchParams?.get("sort") || "relevance",
  }), [searchParams]);

  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [tempFilters, setTempFilters] = useState<Filters>(initialFilters);

  // Update URL when filters change
  const updateURL = useCallback((newFilters: Filters) => {
    const params = new URLSearchParams();

    if (newFilters.query) params.set("q", newFilters.query);
    if (newFilters.subjects.length > 0) params.set("subjects", newFilters.subjects.join(","));
    if (newFilters.priceRange) params.set("price", newFilters.priceRange);
    if (newFilters.minRating > 0) params.set("rating", newFilters.minRating.toString());
    if (newFilters.availability) params.set("availability", newFilters.availability);
    if (newFilters.sort !== "relevance") params.set("sort", newFilters.sort);

    const queryString = params.toString();
    router.push(`/search${queryString ? `?${queryString}` : ""}`, { scroll: false });
  }, [router]);

  // Load tutors
  const loadTutors = useCallback(async () => {
    setLoading(true);
    try {
      const data = await tutorsApi.search({
        query: filters.query,
        subjects: filters.subjects,
        price_range: filters.priceRange,
        min_rating: filters.minRating,
        availability: filters.availability,
        sort: filters.sort,
      });
      setTutors(data);
    } catch (error) {
      console.error("Failed to search tutors:", error);
      setTutors([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadTutors();
  }, [loadTutors]);

  // Apply filters and update URL
  const applyFilters = () => {
    setFilters(tempFilters);
    updateURL(tempFilters);
    setShowFilters(false);
  };

  // Reset filters
  const resetFilters = () => {
    const defaultFilters: Filters = {
      query: "",
      subjects: [],
      priceRange: "",
      minRating: 0,
      availability: "",
      sort: "relevance",
    };
    setTempFilters(defaultFilters);
    setFilters(defaultFilters);
    updateURL(defaultFilters);
    setShowFilters(false);
  };

  // Handle search input
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    applyFilters();
  };

  // Toggle subject filter
  const toggleSubject = (subject: string) => {
    setTempFilters((prev) => ({
      ...prev,
      subjects: prev.subjects.includes(subject)
        ? prev.subjects.filter((s) => s !== subject)
        : [...prev.subjects, subject],
    }));
  };

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.subjects.length > 0) count++;
    if (filters.priceRange) count++;
    if (filters.minRating > 0) count++;
    if (filters.availability) count++;
    return count;
  }, [filters]);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-20">
        <div className="container mx-auto px-4">
          <div className="py-4">
            <Breadcrumb items={[{ label: "Search Tutors" }]} />
          </div>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="pb-4">
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={tempFilters.query}
                  onChange={(e) => setTempFilters((prev) => ({ ...prev, query: e.target.value }))}
                  placeholder="Search by name, subject, or keyword..."
                  className="w-full pl-12 pr-4 py-3 bg-slate-100 dark:bg-slate-800 border-none rounded-xl text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
              <Button type="submit" size="lg">
                Search
              </Button>
            </div>
          </form>

          {/* Filter Bar */}
          <div className="flex items-center justify-between gap-4 pb-4">
            <div className="flex items-center gap-2 overflow-x-auto pb-2 -mb-2 scrollbar-hide">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={clsx(
                  "flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap",
                  showFilters || activeFilterCount > 0
                    ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                    : "bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700"
                )}
              >
                <SlidersHorizontal className="w-4 h-4" />
                Filters
                {activeFilterCount > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 rounded-full bg-emerald-600 text-white text-xs">
                    {activeFilterCount}
                  </span>
                )}
              </button>

              {/* Quick filter pills */}
              {filters.subjects.map((subject) => (
                <button
                  key={subject}
                  onClick={() => {
                    const newSubjects = filters.subjects.filter((s) => s !== subject);
                    const newFilters = { ...filters, subjects: newSubjects };
                    setFilters(newFilters);
                    setTempFilters(newFilters);
                    updateURL(newFilters);
                  }}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm font-medium whitespace-nowrap"
                >
                  {subject}
                  <X className="w-3 h-3" />
                </button>
              ))}

              {filters.priceRange && (
                <button
                  onClick={() => {
                    const newFilters = { ...filters, priceRange: "" };
                    setFilters(newFilters);
                    setTempFilters(newFilters);
                    updateURL(newFilters);
                  }}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-sm font-medium whitespace-nowrap"
                >
                  {PRICE_RANGES.find((p) => p.value === filters.priceRange)?.label}
                  <X className="w-3 h-3" />
                </button>
              )}

              {activeFilterCount > 0 && (
                <button
                  onClick={resetFilters}
                  className="text-sm text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 whitespace-nowrap"
                >
                  Clear all
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {/* Sort */}
              <select
                value={filters.sort}
                onChange={(e) => {
                  const newFilters = { ...filters, sort: e.target.value };
                  setFilters(newFilters);
                  setTempFilters(newFilters);
                  updateURL(newFilters);
                }}
                className="px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>

              {/* View Mode Toggle */}
              <div className="hidden sm:flex items-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-1">
                <button
                  onClick={() => setViewMode("grid")}
                  className={clsx(
                    "p-1.5 rounded",
                    viewMode === "grid"
                      ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400"
                      : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                  )}
                >
                  <Grid className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode("list")}
                  className={clsx(
                    "p-1.5 rounded",
                    viewMode === "list"
                      ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400"
                      : "text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                  )}
                >
                  <List className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 py-6">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Subjects */}
              <div>
                <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                  Subjects
                </h3>
                <div className="flex flex-wrap gap-2">
                  {SUBJECTS.map((subject) => (
                    <button
                      key={subject}
                      onClick={() => toggleSubject(subject)}
                      className={clsx(
                        "px-3 py-1.5 rounded-full text-sm font-medium transition-colors",
                        tempFilters.subjects.includes(subject)
                          ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                      )}
                    >
                      {subject}
                    </button>
                  ))}
                </div>
              </div>

              {/* Price Range */}
              <div>
                <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                  Price Range
                </h3>
                <select
                  value={tempFilters.priceRange}
                  onChange={(e) => setTempFilters((prev) => ({ ...prev, priceRange: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  {PRICE_RANGES.map((range) => (
                    <option key={range.value} value={range.value}>
                      {range.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Min Rating */}
              <div>
                <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                  Minimum Rating
                </h3>
                <div className="flex gap-2">
                  {[0, 3, 4, 4.5].map((rating) => (
                    <button
                      key={rating}
                      onClick={() => setTempFilters((prev) => ({ ...prev, minRating: rating }))}
                      className={clsx(
                        "flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                        tempFilters.minRating === rating
                          ? "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                      )}
                    >
                      {rating === 0 ? (
                        "Any"
                      ) : (
                        <>
                          <Star className="w-3 h-3 fill-current" />
                          {rating}+
                        </>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Availability */}
              <div>
                <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
                  Availability
                </h3>
                <select
                  value={tempFilters.availability}
                  onChange={(e) => setTempFilters((prev) => ({ ...prev, availability: e.target.value }))}
                  className="w-full px-3 py-2 bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-slate-700 dark:text-slate-300 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                >
                  <option value="">Any time</option>
                  <option value="today">Available today</option>
                  <option value="this_week">This week</option>
                  <option value="weekend">Weekends</option>
                  <option value="evening">Evenings (after 5 PM)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
              <Button variant="ghost" onClick={() => setShowFilters(false)}>
                Cancel
              </Button>
              <Button variant="secondary" onClick={resetFilters}>
                Reset
              </Button>
              <Button onClick={applyFilters}>
                Apply Filters
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Results */}
      <div className="container mx-auto px-4 py-8">
        {/* Results Count */}
        <div className="flex items-center justify-between mb-6">
          <p className="text-slate-600 dark:text-slate-400">
            {loading ? (
              "Searching..."
            ) : (
              <>
                <span className="font-medium text-slate-900 dark:text-white">{tutors.length}</span>
                {" "}tutors found
                {filters.query && (
                  <> for "<span className="font-medium">{filters.query}</span>"</>
                )}
              </>
            )}
          </p>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className={clsx(
            viewMode === "grid"
              ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              : "space-y-4"
          )}>
            {Array.from({ length: 6 }).map((_, i) => (
              <TutorCardSkeleton key={i} />
            ))}
          </div>
        ) : tutors.length === 0 ? (
          <EmptyState
            variant="no-results"
            title="No tutors found"
            description={
              filters.query
                ? `We couldn't find any tutors matching "${filters.query}". Try adjusting your search or filters.`
                : "Try adjusting your filters to find more tutors."
            }
            action={{
              label: "Clear Filters",
              onClick: resetFilters,
            }}
          />
        ) : (
          <div className={clsx(
            viewMode === "grid"
              ? "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
              : "space-y-4"
          )}>
            {tutors.map((tutor) => (
              <TutorCard
                key={tutor.id}
                tutor={tutor}
                onClick={() => router.push(`/tutors/${tutor.id}`)}
                variant={viewMode === "list" ? "horizontal" : "vertical"}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
