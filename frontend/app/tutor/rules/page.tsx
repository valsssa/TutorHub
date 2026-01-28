"use client";

import { useRouter } from "next/navigation";
import { ChevronLeft, Gavel, Clock, MessageSquare, Camera, AlertTriangle, Edit } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppShell from "@/components/AppShell";
import { useEffect, useState } from "react";
import { auth } from "@/lib/api";
import { User } from "@/types";
import LoadingSpinner from "@/components/LoadingSpinner";

export default function TutorRulesPage() {
  return (
    <ProtectedRoute requiredRole="tutor" showNavbar={false}>
      <TutorRulesContent />
    </ProtectedRoute>
  );
}

function TutorRulesContent() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error("Failed to load user:", error);
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [router]);

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AppShell user={user}>
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-slate-500 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors font-medium mb-8 group"
        >
          <ChevronLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
          Back
        </button>

        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-8 md:p-12 shadow-sm">
          <div className="flex items-center justify-between mb-8 pb-8 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center text-purple-600 dark:text-purple-400">
                <Gavel size={24} />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                  Tutor Code of Conduct
                </h1>
                <p className="text-slate-500 dark:text-slate-400 mt-1">
                  Guidelines to ensure a high-quality experience for everyone.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                // Example: Could navigate to edit page or show edit modal
                alert("Edit functionality would open an edit page or modal here");
              }}
              className="p-2 text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              title="Edit rules (example)"
            >
              <Edit size={20} />
            </button>
          </div>

          <div className="space-y-12">
            <section>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <Clock size={20} className="text-emerald-500" /> Attendance & Reliability
              </h3>
              <div className="prose dark:prose-invert text-slate-600 dark:text-slate-300">
                <ul className="list-disc pl-5 space-y-2">
                  <li>
                    <strong>Be Punctual:</strong> Join the classroom at least 2 minutes before the
                    scheduled start time.
                  </li>
                  <li>
                    <strong>No-Show Policy:</strong> Missing a scheduled lesson without prior notice
                    (at least 12 hours) affects your visibility and rating.
                  </li>
                  <li>
                    <strong>Rescheduling:</strong> If you must reschedule, do so as early as possible
                    and offer alternative slots.
                  </li>
                </ul>
              </div>
            </section>

            <section>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <MessageSquare size={20} className="text-blue-500" /> Communication
              </h3>
              <div className="prose dark:prose-invert text-slate-600 dark:text-slate-300">
                <ul className="list-disc pl-5 space-y-2">
                  <li>
                    <strong>Response Time:</strong> Respond to student messages within 24 hours.
                    Fast responses lead to more bookings.
                  </li>
                  <li>
                    <strong>Professionalism:</strong> Maintain a respectful and professional tone at
                    all times. Harassment or offensive language results in immediate ban.
                  </li>
                  <li>
                    <strong>Off-Platform Communication:</strong> Asking students to pay outside
                    EduConnect or move communication to other apps is strictly prohibited.
                  </li>
                </ul>
              </div>
            </section>

            <section>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <Camera size={20} className="text-amber-500" /> Profile Quality
              </h3>
              <div className="prose dark:prose-invert text-slate-600 dark:text-slate-300">
                <ul className="list-disc pl-5 space-y-2">
                  <li>
                    <strong>Photo:</strong> Use a clear, high-quality headshot. No logos, group
                    photos, or avatars.
                  </li>
                  <li>
                    <strong>Video:</strong> Your introduction video must be clear, audible, and show
                    your face.
                  </li>
                  <li>
                    <strong>Accuracy:</strong> Do not misrepresent your qualifications or
                    experience. We verify credentials.
                  </li>
                </ul>
              </div>
            </section>

            <div className="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 p-6 rounded-2xl flex gap-4">
              <AlertTriangle className="text-red-600 dark:text-red-400 shrink-0" size={24} />
              <div>
                <h4 className="font-bold text-red-900 dark:text-red-100 mb-2">
                  Zero Tolerance Policy
                </h4>
                <p className="text-red-800 dark:text-red-200 text-sm">
                  EduConnect has a zero-tolerance policy for hate speech, discrimination, sexual
                  harassment, or fraudulent activity. Violations will result in permanent account
                  suspension.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
