"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  X,
  Plus,
  Star,
  Clock,
  DollarSign,
  Users,
  Calendar,
  Video,
  MessageSquare,
  Check,
  Minus,
  ArrowRight,
  Search,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Breadcrumb from "@/components/Breadcrumb";
import Button from "@/components/Button";
import Avatar from "@/components/Avatar";
import LoadingSpinner from "@/components/LoadingSpinner";
import EmptyState from "@/components/EmptyState";
import { tutors as tutorsApi } from "@/lib/api";
import type { TutorPublicSummary } from "@/types";
import clsx from "clsx";

const MAX_COMPARE = 3;

export default function ComparePage() {
  return (
    <ProtectedRoute>
      <CompareContent />
    </ProtectedRoute>
  );
}

function CompareContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [allTutors, setAllTutors] = useState<TutorPublicSummary[]>([]);
  const [selectedTutors, setSelectedTutors] = useState<TutorPublicSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Get initial tutor IDs from URL
  const initialIds = useMemo(() => {
    const ids = searchParams?.get("ids");
    return ids ? ids.split(",").map(Number).filter(Boolean) : [];
  }, [searchParams]);

  // Load tutors
  const loadTutors = useCallback(async () => {
    setLoading(true);
    try {
      const data = await tutorsApi.list();
      setAllTutors(data);

      // Load initially selected tutors from URL
      if (initialIds.length > 0) {
        const selected = data.filter((t) => initialIds.includes(t.id));
        setSelectedTutors(selected.slice(0, MAX_COMPARE));
      }
    } catch {
      // Failed to load tutors data
    } finally {
      setLoading(false);
    }
  }, [initialIds]);

  useEffect(() => {
    loadTutors();
  }, [loadTutors]);

  // Update URL when selection changes
  const updateURL = useCallback((tutors: TutorPublicSummary[]) => {
    const ids = tutors.map((t) => t.id).join(",");
    const url = ids ? `/compare?ids=${ids}` : "/compare";
    router.push(url, { scroll: false });
  }, [router]);

  // Add tutor to comparison
  const addTutor = (tutor: TutorPublicSummary) => {
    if (selectedTutors.length >= MAX_COMPARE) return;
    if (selectedTutors.some((t) => t.id === tutor.id)) return;

    const newSelection = [...selectedTutors, tutor];
    setSelectedTutors(newSelection);
    updateURL(newSelection);
    setShowAddModal(false);
  };

  // Remove tutor from comparison
  const removeTutor = (tutorId: number) => {
    const newSelection = selectedTutors.filter((t) => t.id !== tutorId);
    setSelectedTutors(newSelection);
    updateURL(newSelection);
  };

  // Filter tutors for add modal
  const availableTutors = useMemo(() => {
    const selectedIds = selectedTutors.map((t) => t.id);
    return allTutors
      .filter((t) => !selectedIds.includes(t.id))
      .filter((t) => {
        if (!searchQuery.trim()) return true;
        const query = searchQuery.toLowerCase();
        const name = `${t.first_name || ""} ${t.last_name || ""}`.toLowerCase();
        return name.includes(query) || t.subjects?.some((s) => s.toLowerCase().includes(query));
      });
  }, [allTutors, selectedTutors, searchQuery]);

  // Comparison metrics
  const getComparisonValue = (
    tutor: TutorPublicSummary,
    metric: string
  ): { value: string | number; highlight: boolean } => {
    const values = selectedTutors.map((t) => {
      switch (metric) {
        case "rating":
          return t.average_rating || 0;
        case "price":
          return (t.hourly_rate_cents || 0) / 100;
        case "sessions":
          return t.total_sessions || 0;
        case "reviews":
          return t.review_count || 0;
        default:
          return 0;
      }
    });

    const tutorValue = (() => {
      switch (metric) {
        case "rating":
          return tutor.average_rating || 0;
        case "price":
          return (tutor.hourly_rate_cents || 0) / 100;
        case "sessions":
          return tutor.total_sessions || 0;
        case "reviews":
          return tutor.review_count || 0;
        default:
          return 0;
      }
    })();

    const isBest =
      metric === "price"
        ? tutorValue === Math.min(...values)
        : tutorValue === Math.max(...values);

    return {
      value: metric === "price" ? `$${tutorValue}` : tutorValue,
      highlight: isBest && values.filter((v) => v === tutorValue).length === 1,
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-4 py-4">
          <Breadcrumb
            items={[
              { label: "Tutors", href: "/tutors" },
              { label: "Compare" },
            ]}
          />
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Compare Tutors
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Compare up to {MAX_COMPARE} tutors side by side
            </p>
          </div>

          {selectedTutors.length < MAX_COMPARE && (
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Tutor
            </Button>
          )}
        </div>

        {selectedTutors.length === 0 ? (
          <EmptyState
            variant="no-data"
            title="No tutors to compare"
            description="Add tutors to compare their profiles, ratings, and pricing side by side."
            action={{
              label: "Add Tutors",
              onClick: () => setShowAddModal(true),
            }}
          />
        ) : (
          <div className="space-y-6">
            {/* Tutor Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {selectedTutors.map((tutor) => (
                <div
                  key={tutor.id}
                  className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 relative"
                >
                  {/* Remove button */}
                  <button
                    onClick={() => removeTutor(tutor.id)}
                    className="absolute top-4 right-4 p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <X className="w-4 h-4 text-slate-400" />
                  </button>

                  {/* Avatar and Name */}
                  <div className="flex flex-col items-center text-center mb-4">
                    <Avatar
                      name={`${tutor.first_name || ""} ${tutor.last_name || ""}`}
                      avatarUrl={tutor.avatar_url}
                      userId={tutor.id}
                      size="lg"
                    />
                    <h3 className="font-bold text-slate-900 dark:text-white mt-3">
                      {tutor.first_name} {tutor.last_name}
                    </h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      {tutor.title || "Tutor"}
                    </p>
                  </div>

                  {/* Quick Actions */}
                  <div className="flex gap-2 mt-4">
                    <Link href={`/tutors/${tutor.id}`} className="flex-1">
                      <Button variant="secondary" size="sm" className="w-full">
                        View Profile
                      </Button>
                    </Link>
                    <Link href={`/tutors/${tutor.id}?book=true`} className="flex-1">
                      <Button size="sm" className="w-full">
                        Book
                      </Button>
                    </Link>
                  </div>
                </div>
              ))}

              {/* Add Slot */}
              {selectedTutors.length < MAX_COMPARE && (
                <button
                  onClick={() => setShowAddModal(true)}
                  className="bg-slate-100 dark:bg-slate-800/50 rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-700 p-6 flex flex-col items-center justify-center min-h-[280px] hover:border-emerald-500 dark:hover:border-emerald-500 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors group"
                >
                  <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center mb-3 group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/30 transition-colors">
                    <Plus className="w-6 h-6 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors" />
                  </div>
                  <span className="text-sm font-medium text-slate-500 dark:text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                    Add tutor to compare
                  </span>
                </button>
              )}
            </div>

            {/* Comparison Table */}
            <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {/* Rating */}
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-slate-600 dark:text-slate-400 w-40">
                        <div className="flex items-center gap-2">
                          <Star className="w-4 h-4" />
                          Rating
                        </div>
                      </td>
                      {selectedTutors.map((tutor) => {
                        const { value, highlight } = getComparisonValue(tutor, "rating");
                        return (
                          <td
                            key={tutor.id}
                            className={clsx(
                              "px-6 py-4 text-center",
                              highlight && "bg-emerald-50 dark:bg-emerald-900/20"
                            )}
                          >
                            <div className="flex items-center justify-center gap-1">
                              <Star className={clsx(
                                "w-4 h-4",
                                highlight ? "text-amber-500 fill-amber-500" : "text-slate-300 fill-slate-300"
                              )} />
                              <span className={clsx(
                                "font-bold",
                                highlight ? "text-emerald-600 dark:text-emerald-400" : "text-slate-900 dark:text-white"
                              )}>
                                {value}
                              </span>
                            </div>
                          </td>
                        );
                      })}
                    </tr>

                    {/* Price */}
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-2">
                          <DollarSign className="w-4 h-4" />
                          Hourly Rate
                        </div>
                      </td>
                      {selectedTutors.map((tutor) => {
                        const { value, highlight } = getComparisonValue(tutor, "price");
                        return (
                          <td
                            key={tutor.id}
                            className={clsx(
                              "px-6 py-4 text-center",
                              highlight && "bg-emerald-50 dark:bg-emerald-900/20"
                            )}
                          >
                            <span className={clsx(
                              "font-bold",
                              highlight ? "text-emerald-600 dark:text-emerald-400" : "text-slate-900 dark:text-white"
                            )}>
                              {value}/hr
                            </span>
                          </td>
                        );
                      })}
                    </tr>

                    {/* Sessions */}
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4" />
                          Total Sessions
                        </div>
                      </td>
                      {selectedTutors.map((tutor) => {
                        const { value, highlight } = getComparisonValue(tutor, "sessions");
                        return (
                          <td
                            key={tutor.id}
                            className={clsx(
                              "px-6 py-4 text-center",
                              highlight && "bg-emerald-50 dark:bg-emerald-900/20"
                            )}
                          >
                            <span className={clsx(
                              "font-bold",
                              highlight ? "text-emerald-600 dark:text-emerald-400" : "text-slate-900 dark:text-white"
                            )}>
                              {value}
                            </span>
                          </td>
                        );
                      })}
                    </tr>

                    {/* Reviews */}
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-4 h-4" />
                          Reviews
                        </div>
                      </td>
                      {selectedTutors.map((tutor) => {
                        const { value, highlight } = getComparisonValue(tutor, "reviews");
                        return (
                          <td
                            key={tutor.id}
                            className={clsx(
                              "px-6 py-4 text-center",
                              highlight && "bg-emerald-50 dark:bg-emerald-900/20"
                            )}
                          >
                            <span className={clsx(
                              "font-bold",
                              highlight ? "text-emerald-600 dark:text-emerald-400" : "text-slate-900 dark:text-white"
                            )}>
                              {value}
                            </span>
                          </td>
                        );
                      })}
                    </tr>

                    {/* Subjects */}
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-2">
                          <Users className="w-4 h-4" />
                          Subjects
                        </div>
                      </td>
                      {selectedTutors.map((tutor) => (
                        <td key={tutor.id} className="px-6 py-4">
                          <div className="flex flex-wrap gap-1 justify-center">
                            {tutor.subjects?.slice(0, 3).map((subject, i) => (
                              <span
                                key={i}
                                className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 rounded text-xs"
                              >
                                {subject}
                              </span>
                            ))}
                            {(tutor.subjects?.length || 0) > 3 && (
                              <span className="text-xs text-slate-400">
                                +{(tutor.subjects?.length || 0) - 3} more
                              </span>
                            )}
                          </div>
                        </td>
                      ))}
                    </tr>

                    {/* Video Intro */}
                    <tr>
                      <td className="px-6 py-4 text-sm font-medium text-slate-600 dark:text-slate-400">
                        <div className="flex items-center gap-2">
                          <Video className="w-4 h-4" />
                          Video Intro
                        </div>
                      </td>
                      {selectedTutors.map((tutor) => (
                        <td key={tutor.id} className="px-6 py-4 text-center">
                          {tutor.intro_video_url ? (
                            <Check className="w-5 h-5 text-emerald-500 mx-auto" />
                          ) : (
                            <Minus className="w-5 h-5 text-slate-300 mx-auto" />
                          )}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Tutor Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50 dark:bg-black/70"
            onClick={() => setShowAddModal(false)}
          />
          <div className="relative bg-white dark:bg-slate-900 rounded-2xl shadow-xl max-w-lg w-full max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <h2 className="font-bold text-lg text-slate-900 dark:text-white">
                Add Tutor to Compare
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <div className="p-4 border-b border-slate-200 dark:border-slate-800">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search tutors..."
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-100 dark:bg-slate-800 border-none rounded-lg text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {availableTutors.length === 0 ? (
                <p className="text-center text-slate-500 dark:text-slate-400 py-8">
                  No tutors available to add
                </p>
              ) : (
                <div className="space-y-2">
                  {availableTutors.map((tutor) => (
                    <button
                      key={tutor.id}
                      onClick={() => addTutor(tutor)}
                      className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-left"
                    >
                      <Avatar
                        name={`${tutor.first_name || ""} ${tutor.last_name || ""}`}
                        avatarUrl={tutor.avatar_url}
                        userId={tutor.id}
                        size="md"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-slate-900 dark:text-white truncate">
                          {tutor.first_name} {tutor.last_name}
                        </p>
                        <p className="text-sm text-slate-500 dark:text-slate-400 truncate">
                          {tutor.subjects?.slice(0, 2).join(", ")}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-1 text-sm">
                          <Star className="w-3 h-3 text-amber-500 fill-amber-500" />
                          <span className="font-medium text-slate-900 dark:text-white">
                            {tutor.average_rating?.toFixed(1) || "N/A"}
                          </span>
                        </div>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          ${((tutor.hourly_rate_cents || 0) / 100).toFixed(0)}/hr
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
