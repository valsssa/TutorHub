"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import {
  X,
  MessageSquare,
  Calendar,
  FileText,
  MoreHorizontal,
  User as UserIcon,
  SlidersHorizontal,
  ChevronLeft,
  Check,
  Clock,
  Archive,
  ArchiveRestore,
} from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppShell from "@/components/AppShell";
import { auth, bookings } from "@/lib/api";
import { User } from "@/types";
import { BookingDTO } from "@/types/booking";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useToast } from "@/components/ToastContainer";

interface TutorStudent {
  id: string;
  name: string;
  avatar?: string;
  type: "All" | "Subscription" | "Trial" | "Cancelled";
  lessonsTotal?: number;
  lessonsCompleted?: number;
  nextLessonAt?: string;
  suggestedAction?: string;
}

export default function TutorStudentsPage() {
  return (
    <ProtectedRoute requiredRole="tutor" showNavbar={false}>
      <TutorStudentsContent />
    </ProtectedRoute>
  );
}

function TutorStudentsContent() {
  const router = useRouter();
  const { showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [bookingsData, setBookingsData] = useState<BookingDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<"All" | "Subscription" | "Trial" | "Cancelled">(
    "All"
  );
  const [isFilterMenuOpen, setIsFilterMenuOpen] = useState(false);
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [archivedStudentIds, setArchivedStudentIds] = useState<Set<string>>(new Set());
  const [showArchived, setShowArchived] = useState(false);

  useEffect(() => {
    // Load archived student IDs from localStorage
    const stored = localStorage.getItem('archived_students');
    if (stored) {
      try {
        const ids = JSON.parse(stored);
        setArchivedStudentIds(new Set(ids));
      } catch {
        // Invalid stored data, ignore
      }
    }

    const loadData = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);

        // Load all bookings for tutor
        const bookingResponse = await bookings.list({
          role: "tutor",
          page: 1,
          page_size: 1000,
        });
        setBookingsData(bookingResponse.bookings || []);
      } catch {
        showError("Failed to load students data");
        router.replace("/dashboard");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [router, showError]);

  // Transform bookings into students list
  const students = useMemo(() => {
    const studentMap = new Map<string, TutorStudent>();
    const studentBookings = new Map<string, BookingDTO[]>();

    // Group bookings by student
    bookingsData.forEach((booking) => {
      const studentId = booking.student.id.toString();
      if (!studentBookings.has(studentId)) {
        studentBookings.set(studentId, []);
      }
      studentBookings.get(studentId)!.push(booking);
    });

    // Process each student
    studentBookings.forEach((bookings, studentId) => {
      const studentName = bookings[0].student.name || `Student ${studentId}`;
      
      // Determine type: use most recent non-cancelled booking, or most common type
      let type: "Subscription" | "Trial" | "Cancelled" = "Subscription";
      const sortedBookings = [...bookings].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      
      // Helper to check if booking is cancelled (using four-field system with fallback)
      const isCancelled = (b: typeof bookings[0]) => {
        const sessionState = (b.session_state || "").toUpperCase();
        return sessionState === "CANCELLED" || sessionState === "EXPIRED" ||
          b.status === "CANCELLED_BY_STUDENT" || b.status === "CANCELLED_BY_TUTOR" || b.status === "cancelled";
      };

      // Check for cancelled status first
      const hasCancelled = bookings.some(isCancelled);

      if (hasCancelled && bookings.every(isCancelled)) {
        type = "Cancelled";
      } else {
        // Use most recent booking's lesson type
        const mostRecent = sortedBookings.find((b) => !isCancelled(b)) || sortedBookings[0];
        
        if (mostRecent?.lesson_type === "TRIAL") {
          type = "Trial";
        } else {
          type = "Subscription";
        }
      }

      studentMap.set(studentId, {
        id: studentId,
        name: studentName,
        avatar: bookings[0].student.avatar_url || undefined,
        type,
        lessonsTotal: 0,
        lessonsCompleted: 0,
        nextLessonAt: undefined,
        suggestedAction: undefined,
      });

      const student = studentMap.get(studentId)!;
      student.lessonsTotal = bookings.length;

      // Count completed lessons (using four-field system with fallback)
      const completedCount = bookings.filter((b) => {
        const sessionState = (b.session_state || "").toUpperCase();
        const sessionOutcome = (b.session_outcome || "").toUpperCase();
        return sessionState === "ENDED" ||
          sessionOutcome === "COMPLETED" || sessionOutcome === "NO_SHOW_STUDENT" || sessionOutcome === "NO_SHOW_TUTOR" ||
          b.status === "COMPLETED" || b.status === "completed" || b.status === "NO_SHOW_STUDENT" || b.status === "NO_SHOW_TUTOR";
      }).length;
      student.lessonsCompleted = completedCount;

      // Find next upcoming lesson (earliest future lesson)
      const upcomingBookings = bookings
        .filter((b) => {
          const bookingStart = new Date(b.start_at);
          const now = new Date();
          return bookingStart > now && !isCancelled(b);
        })
        .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime());

      if (upcomingBookings.length > 0) {
        student.nextLessonAt = upcomingBookings[0].start_at;
      }

      // Set suggested action for pending bookings (using four-field system with fallback)
      const hasPending = bookings.some((b) => {
        const sessionState = (b.session_state || "").toUpperCase();
        return sessionState === "REQUESTED" || b.status === "PENDING" || b.status === "pending";
      });
      if (hasPending) {
        student.suggestedAction = "Respond to request";
      }
    });

    return Array.from(studentMap.values());
  }, [bookingsData]);

  const filteredStudents = useMemo(() => {
    let filtered = students;

    // Filter by type
    if (filterType !== "All") {
      filtered = filtered.filter((student) => student.type === filterType);
    }

    // Filter by archived status
    filtered = filtered.filter((student) => {
      const isArchived = archivedStudentIds.has(student.id);
      return showArchived ? isArchived : !isArchived;
    });

    return filtered;
  }, [students, filterType, archivedStudentIds, showArchived]);

  const handleFilterClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsFilterMenuOpen(!isFilterMenuOpen);
  };

  const handleSelectFilter = (type: "All" | "Subscription" | "Trial" | "Cancelled") => {
    setFilterType(type);
    setIsFilterMenuOpen(false);
  };

  const toggleMenu = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setOpenMenuId(openMenuId === id ? null : id);
  };

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setOpenMenuId(null);
      setIsFilterMenuOpen(false);
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  const formatDate = (isoString?: string) => {
    if (!isoString) return "-";
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const handleMessage = (studentId: string, name: string) => {
    router.push(`/messages?user=${studentId}`);
  };

  const handleSchedule = (studentId: string) => {
    router.push(`/bookings?student=${studentId}`);
  };

  const handleViewProfile = (studentId: string) => {
    // Navigate to student profile or booking details
    router.push(`/bookings?student=${studentId}`);
  };

  const handleViewHistory = (studentId: string) => {
    router.push(`/bookings?student=${studentId}&status=completed`);
  };

  const handleArchive = (studentId: string) => {
    const newArchivedIds = new Set(archivedStudentIds);
    if (newArchivedIds.has(studentId)) {
      // Unarchive
      newArchivedIds.delete(studentId);
    } else {
      // Archive
      newArchivedIds.add(studentId);
    }
    setArchivedStudentIds(newArchivedIds);
    // Persist to localStorage
    localStorage.setItem('archived_students', JSON.stringify(Array.from(newArchivedIds)));
    setOpenMenuId(null);
  };

  const handleNotes = (studentId: string, name: string) => {
    router.push(`/tutor/students/edit-notes?studentId=${studentId}&name=${encodeURIComponent(name)}`);
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AppShell user={user}>
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-6 group"
        >
          <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
          Back to Dashboard
        </button>

        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">My students</h1>

        {/* Filter Toolbar */}
        <div className="flex items-center gap-3 mb-6 relative z-[10000]">
          <div className="relative">
            <button
              onClick={handleFilterClick}
              className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-bold transition-all active:scale-95 ${
                isFilterMenuOpen
                  ? "bg-slate-100 dark:bg-slate-800 border-slate-400 dark:border-slate-500 text-slate-900 dark:text-white"
                  : "bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
              }`}
            >
              <SlidersHorizontal size={16} />
              Filters
            </button>

            {isFilterMenuOpen && (
              <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-slate-900 rounded-lg shadow-xl border border-slate-200 dark:border-slate-800 py-2 z-[10001] animate-in fade-in zoom-in-95 duration-200">
                <div className="px-4 py-2 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                  Filter by Type
                </div>
                {(["All", "Subscription", "Trial", "Cancelled"] as const).map((type) => (
                  <button
                    key={type}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectFilter(type);
                    }}
                    className={`w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center justify-between ${
                      filterType === type
                        ? "bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 font-medium"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                    }`}
                  >
                    {type}
                    {filterType === type && (
                      <Check size={16} className="text-emerald-600 dark:text-emerald-400" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Show Archived Toggle */}
          <button
            onClick={() => setShowArchived(!showArchived)}
            className={`flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-bold transition-all active:scale-95 ${
              showArchived
                ? "bg-slate-700 dark:bg-slate-600 border-slate-700 dark:border-slate-600 text-white"
                : "bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
            }`}
          >
            {showArchived ? <ArchiveRestore size={16} /> : <Archive size={16} />}
            {showArchived ? "Show Active" : "Show Archived"}
          </button>

          {filterType !== "All" && (
            <div className="flex items-center gap-2 px-3 py-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-100 dark:border-emerald-800/50 animate-in fade-in zoom-in-95 duration-200">
              <span className="text-sm font-medium text-emerald-700 dark:text-emerald-300">
                Type: {filterType}
              </span>
              <button
                onClick={() => setFilterType("All")}
                className="text-emerald-600 hover:text-emerald-800 dark:text-emerald-400 dark:hover:text-emerald-200 p-0.5 rounded-full hover:bg-emerald-100 dark:hover:bg-emerald-800/50 transition-colors"
              >
                <X size={14} />
              </button>
            </div>
          )}
        </div>

        {/* Desktop Table View */}
        <div className="hidden md:block bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-visible shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800">
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Name
                  </th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Type
                  </th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Lessons
                  </th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Next lesson
                  </th>
                  <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                    Suggested action
                  </th>
                  <th className="px-6 py-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredStudents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 dark:text-slate-400">
                      No students found matching your filter.
                    </td>
                  </tr>
                ) : (
                  filteredStudents.map((student) => (
                    <tr
                      key={student.id}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group"
                    >
                      <td
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => handleViewProfile(student.id)}
                      >
                        <div className="flex items-center gap-3">
                          {student.avatar ? (
                            <Image
                              src={student.avatar}
                              alt={student.name}
                              width={36}
                              height={36}
                              className="w-9 h-9 rounded-md object-cover bg-slate-200"
                            />
                          ) : (
                            <div className="w-9 h-9 rounded-md bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400">
                              <UserIcon size={16} />
                            </div>
                          )}
                          <span className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-emerald-600 transition-colors">
                            {student.name}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                            student.type === "Subscription"
                              ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                              : student.type === "Trial"
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                              : "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300"
                          }`}
                        >
                          {student.type}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {student.lessonsTotal !== undefined ? (
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-slate-900 dark:bg-white rounded-full"
                                style={{
                                  width: `${
                                    student.lessonsTotal > 0
                                      ? (student.lessonsCompleted! / student.lessonsTotal) * 100
                                      : 0
                                  }%`,
                                }}
                              ></div>
                            </div>
                            <span className="text-xs font-medium text-slate-600 dark:text-slate-400">
                              {student.lessonsCompleted}/{student.lessonsTotal}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 text-sm">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                        {formatDate(student.nextLessonAt)}
                      </td>
                      <td className="px-6 py-4">
                        {student.suggestedAction ? (
                          <button
                            onClick={() => handleMessage(student.id, student.name)}
                            className="text-sm font-bold text-slate-900 dark:text-white underline decoration-slate-300 dark:decoration-slate-600 hover:decoration-slate-900 dark:hover:decoration-white underline-offset-2 transition-all"
                          >
                            {student.suggestedAction}
                          </button>
                        ) : (
                          <span className="text-slate-400 text-sm">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 relative">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => handleMessage(student.id, student.name)}
                            className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                            title="Message"
                          >
                            <MessageSquare size={18} />
                          </button>
                          <button
                            onClick={() => handleSchedule(student.id)}
                            className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                            title="Schedule Lesson"
                          >
                            <Calendar size={18} />
                          </button>
                          <button
                            onClick={() => handleNotes(student.id, student.name)}
                            className="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                            title="Notes"
                          >
                            <FileText size={18} />
                          </button>
                          <div className="relative">
                            <button
                              onClick={(e) => toggleMenu(student.id, e)}
                              className={`p-2 rounded-lg transition-colors ${
                                openMenuId === student.id
                                  ? "text-slate-900 dark:text-white bg-slate-100 dark:bg-slate-800"
                                  : "text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800"
                              }`}
                            >
                              <MoreHorizontal size={18} />
                            </button>
                            {openMenuId === student.id && (
                              <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-slate-900 rounded-lg shadow-xl border border-slate-200 dark:border-slate-800 py-1 z-[10001] animate-in fade-in zoom-in-95 duration-200">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleViewProfile(student.id);
                                    setOpenMenuId(null);
                                  }}
                                  className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                >
                                  View Profile
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleViewHistory(student.id);
                                    setOpenMenuId(null);
                                  }}
                                  className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                                >
                                  History
                                </button>
                                <div className="h-px bg-slate-100 dark:bg-slate-800 my-1"></div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleArchive(student.id);
                                    setOpenMenuId(null);
                                  }}
                                  className="w-full text-left px-4 py-2 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2"
                                >
                                  {archivedStudentIds.has(student.id) ? (
                                    <>
                                      <ArchiveRestore className="w-4 h-4" />
                                      Unarchive Student
                                    </>
                                  ) : (
                                    <>
                                      <Archive className="w-4 h-4" />
                                      Archive Student
                                    </>
                                  )}
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Mobile Card View */}
        <div className="md:hidden space-y-4">
          {filteredStudents.length === 0 ? (
            <div className="p-8 text-center text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800">
              No students found matching your filter.
            </div>
          ) : (
            filteredStudents.map((student) => (
              <div
                key={student.id}
                className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col gap-4"
              >
                <div className="flex justify-between items-start">
                  <div
                    className="flex items-center gap-3"
                    onClick={() => handleViewProfile(student.id)}
                  >
                    {student.avatar ? (
                      <Image
                        src={student.avatar}
                        alt={student.name}
                        width={40}
                        height={40}
                        className="w-10 h-10 rounded-full object-cover bg-slate-200"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400">
                        <UserIcon size={20} />
                      </div>
                    )}
                    <div>
                      <div className="font-bold text-slate-900 dark:text-white text-base">
                        {student.name}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                        {formatDate(student.nextLessonAt)}
                        {student.nextLessonAt && (
                          <>
                            <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                            Next Lesson
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <span
                    className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                      student.type === "Subscription"
                        ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                        : student.type === "Trial"
                        ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
                        : "bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300"
                    }`}
                  >
                    {student.type}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-100 dark:border-slate-800">
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">
                      Lessons
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden max-w-[60px]">
                        <div
                          className="h-full bg-slate-900 dark:bg-white rounded-full"
                          style={{
                            width: student.lessonsTotal
                              ? `${(student.lessonsCompleted! / student.lessonsTotal) * 100}%`
                              : "0%",
                          }}
                        ></div>
                      </div>
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                        {student.lessonsCompleted || 0}/{student.lessonsTotal || 0}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] uppercase font-bold text-slate-400 mb-1">Action</div>
                    {student.suggestedAction ? (
                      <button
                        onClick={() => handleMessage(student.id, student.name)}
                        className="text-xs font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
                      >
                        {student.suggestedAction}
                      </button>
                    ) : (
                      <span className="text-xs text-slate-500 italic">None</span>
                    )}
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    onClick={() => handleMessage(student.id, student.name)}
                    className="flex-1 py-2.5 bg-slate-100 dark:bg-slate-800 rounded-lg text-sm font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors flex items-center justify-center gap-2"
                  >
                    <MessageSquare size={16} /> Message
                  </button>
                  <button
                    onClick={() => handleSchedule(student.id)}
                    className="flex-1 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-bold hover:bg-emerald-500 transition-colors flex items-center justify-center gap-2"
                  >
                    <Calendar size={16} /> Schedule
                  </button>
                  <button
                    onClick={(e) => toggleMenu(student.id, e)}
                    className="p-2.5 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-500 hover:text-slate-900 dark:hover:text-white"
                  >
                    <MoreHorizontal size={20} />
                  </button>
                </div>

                {openMenuId === student.id && (
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-2 mt-2 space-y-1 animate-in slide-in-from-top-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewProfile(student.id);
                        setOpenMenuId(null);
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 rounded hover:bg-white dark:hover:bg-slate-700 transition-colors"
                    >
                      View Profile
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewHistory(student.id);
                        setOpenMenuId(null);
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 rounded hover:bg-white dark:hover:bg-slate-700 transition-colors"
                    >
                      History
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleNotes(student.id, student.name);
                        setOpenMenuId(null);
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 rounded hover:bg-white dark:hover:bg-slate-700 transition-colors"
                    >
                      Notes
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleArchive(student.id);
                        setOpenMenuId(null);
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-slate-700 dark:text-slate-300 rounded hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2"
                    >
                      {archivedStudentIds.has(student.id) ? (
                        <>
                          <ArchiveRestore className="w-4 h-4" />
                          Unarchive
                        </>
                      ) : (
                        <>
                          <Archive className="w-4 h-4" />
                          Archive
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
}
