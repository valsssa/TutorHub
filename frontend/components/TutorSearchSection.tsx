"use client";

import { useState } from "react";
import { FiSearch, FiRefreshCw } from "react-icons/fi";
import { Subject } from "@/types";
import {
  PRICE_LIMITS,
  RATING_OPTIONS,
  EXPERIENCE_OPTIONS,
  SORT_OPTIONS,
} from "@/types/filters";

interface TutorSearchSectionProps {
  subjects: Subject[];
  selectedSubject?: number;
  priceRange: [number, number];
  minRating?: number;
  minExperience?: number;
  sortBy: string;
  searchTerm: string;
  resultsCount: number;
  onSubjectChange: (id?: number) => void;
  onPriceChange: (range: [number, number]) => void;
  onMinRatingChange: (rating?: number) => void;
  onMinExperienceChange: (years?: number) => void;
  onSortChange: (sort: string) => void;
  onSearchChange: (term: string) => void;
  onUpdate: () => void;
}

export default function TutorSearchSection({
  subjects,
  selectedSubject,
  priceRange,
  minRating,
  minExperience,
  sortBy,
  searchTerm,
  resultsCount,
  onSubjectChange,
  onPriceChange,
  onMinRatingChange,
  onMinExperienceChange,
  onSortChange,
  onSearchChange,
  onUpdate,
}: TutorSearchSectionProps) {
  const getSelectedSubjectName = () => {
    if (!selectedSubject) return "All Subjects";
    return subjects.find((s) => s.id === selectedSubject)?.name || "Subject";
  };

  const getSelectedRatingLabel = () => {
    if (!minRating) return "Any Rating";
    const option = RATING_OPTIONS.find((o) => o.value === minRating);
    return option?.label || `${minRating}+ Stars`;
  };

  const getSelectedExperienceLabel = () => {
    if (!minExperience) return "Any Experience";
    const option = EXPERIENCE_OPTIONS.find((o) => o.value === minExperience);
    return option?.label || `${minExperience}+ Years`;
  };

  const getSelectedSortLabel = () => {
    const option = SORT_OPTIONS.find((o) => o.value === sortBy);
    return option?.label || "Best Match";
  };

  return (
    <section className="bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-slate-900 mb-2">
            Find Your Perfect Tutor
          </h2>
          <p className="text-slate-600">
            {resultsCount} {resultsCount === 1 ? "tutor" : "tutors"} match your criteria • Sorted by: {getSelectedSortLabel()}
          </p>
        </div>

        {/* Search & Filters Container */}
        <div className="bg-gradient-to-br from-slate-50 to-blue-50/30 rounded-xl p-6 mb-6 border border-slate-200">
          {/* Smart Search Bar */}
          <div className="relative mb-4">
            <FiSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <input
              type="text"
              placeholder="What do you want to learn? (Try 'AP Calculus' or 'Python for Data Science')"
              className="w-full pl-12 pr-4 py-3 text-lg border-2 border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 bg-white transition-all"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
            />
          </div>

          {/* Filters Grid */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Subject Filter */}
            <select
              className="px-4 py-2.5 border-2 border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 bg-white font-medium text-slate-700 transition-all hover:border-slate-300 cursor-pointer"
              value={selectedSubject || ""}
              onChange={(e) =>
                onSubjectChange(e.target.value ? Number(e.target.value) : undefined)
              }
            >
              <option value="">All Subjects</option>
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>

            {/* Rating Filter */}
            <select
              className="px-4 py-2.5 border-2 border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 bg-white font-medium text-slate-700 transition-all hover:border-slate-300 cursor-pointer"
              value={minRating || ""}
              onChange={(e) =>
                onMinRatingChange(e.target.value ? Number(e.target.value) : undefined)
              }
            >
              <option value="">Any Rating</option>
              {RATING_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Experience Filter */}
            <select
              className="px-4 py-2.5 border-2 border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 bg-white font-medium text-slate-700 transition-all hover:border-slate-300 cursor-pointer"
              value={minExperience || ""}
              onChange={(e) =>
                onMinExperienceChange(
                  e.target.value ? Number(e.target.value) : undefined
                )
              }
            >
              <option value="">Any Experience</option>
              {EXPERIENCE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Sort Filter */}
            <select
              className="px-4 py-2.5 border-2 border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 bg-white font-medium text-slate-700 transition-all hover:border-slate-300 cursor-pointer"
              value={sortBy}
              onChange={(e) => onSortChange(e.target.value)}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>

            {/* Update Button */}
            <button
              onClick={onUpdate}
              className="bg-gradient-to-r from-sky-500 to-blue-600 text-white px-4 py-2.5 rounded-lg font-semibold hover:from-sky-600 hover:to-blue-700 transition-all shadow-md hover:shadow-lg flex items-center justify-center gap-2"
            >
              <FiRefreshCw className="w-4 h-4" />
              Update
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
