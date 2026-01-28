"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { X, Save } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppShell from "@/components/AppShell";
import { auth } from "@/lib/api";
import { User } from "@/types";
import LoadingSpinner from "@/components/LoadingSpinner";
import TextArea from "@/components/TextArea";
import { useToast } from "@/components/ToastContainer";

export default function EditStudentNotesPage() {
  return (
    <ProtectedRoute requiredRole="tutor" showNavbar={false}>
      <Suspense fallback={
        <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
          <LoadingSpinner />
        </div>
      }>
        <EditStudentNotesContent />
      </Suspense>
    </ProtectedRoute>
  );
}

function EditStudentNotesContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notes, setNotes] = useState("");

  const studentId = searchParams?.get("studentId") || null;
  const studentName = searchParams?.get("name") || "Student";

  useEffect(() => {
    if (!studentId) {
      showError("Student ID is required");
      router.replace("/tutor/students");
      return;
    }

    const loadUser = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);

        // TODO: Load existing notes from API
        // For now, load from localStorage as example
        const savedNotes = localStorage.getItem(`student_notes_${studentId}`);
        if (savedNotes) {
          setNotes(savedNotes);
        }
      } catch (error) {
        console.error("Failed to load user:", error);
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [router, studentId, showError]);

  const handleSave = async () => {
    if (!studentId) return;

    setSaving(true);
    try {
      // TODO: Save notes via API
      // For now, save to localStorage as example
      localStorage.setItem(`student_notes_${studentId}`, notes);
      
      showSuccess("Notes saved successfully");
      router.back();
    } catch (error) {
      console.error("Failed to save notes:", error);
      showError("Failed to save notes");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.back();
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
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Edit Notes
            </h1>
            <p className="text-slate-500 dark:text-slate-400">
              Add private notes about {studentName}
            </p>
          </div>
          <button
            onClick={handleCancel}
            className="p-2 text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Edit Form */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6">
          <div className="mb-6">
            <TextArea
              label="Private notes about this student (only visible to you)"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What's their learning style? What topics have you covered? What areas need more work? What motivates them?"
              minRows={10}
              maxRows={15}
              maxLength={3000}
              helperText="Track progress, preferences, and important details to personalize future lessons"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
            <button
              onClick={handleCancel}
              className="flex-1 px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save size={18} />
                  Save Notes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
