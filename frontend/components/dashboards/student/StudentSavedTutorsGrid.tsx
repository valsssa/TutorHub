"use client";

import React from "react";
import { Heart } from "lucide-react";
import TutorCard from "@/components/TutorCard";
import { TutorPublicSummary } from "@/types";

interface StudentSavedTutorsGridProps {
  savedTutors: TutorPublicSummary[];
  onViewProfile: (tutor: TutorPublicSummary) => void;
  onToggleSave: (e: React.MouseEvent, tutorId: number) => void;
  onBook: (e: React.MouseEvent, tutor: TutorPublicSummary) => void;
  onQuickBook: (e: React.MouseEvent, tutor: TutorPublicSummary) => void;
  onSlotBook: (e: React.MouseEvent, tutor: TutorPublicSummary, slot: string) => void;
  onMessage: (e: React.MouseEvent, tutor: TutorPublicSummary) => void;
}

export default function StudentSavedTutorsGrid({
  savedTutors,
  onViewProfile,
  onToggleSave,
  onBook,
  onQuickBook,
  onSlotBook,
  onMessage,
}: StudentSavedTutorsGridProps) {
  return (
    <section className="mt-10">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-slate-900 dark:text-white">
          <Heart size={20} className="text-emerald-500" /> Saved tutors
        </h2>
        <span className="text-sm text-slate-500 dark:text-slate-400">
          {savedTutors.length} saved
        </span>
      </div>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-3">
        {savedTutors.map((tutor) => (
          <TutorCard
            key={tutor.id}
            tutor={tutor}
            onViewProfile={() => onViewProfile(tutor)}
            onToggleSave={(e) => onToggleSave(e, tutor.id)}
            onBook={(e) => onBook(e, tutor)}
            onQuickBook={(e) => onQuickBook(e, tutor)}
            onSlotBook={(e: React.MouseEvent, tutorParam: TutorPublicSummary, slot: string) => onSlotBook(e, tutorParam, slot)}
            onMessage={(e) => onMessage(e, tutor)}
            isSaved
          />
        ))}
      </div>
    </section>
  );
}
