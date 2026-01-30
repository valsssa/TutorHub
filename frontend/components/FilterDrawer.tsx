"use client";

import { useState, useEffect } from "react";
import {
  FiX,
  FiBookOpen,
  FiDollarSign,
  FiStar,
  FiClock,
  FiCheck,
} from "react-icons/fi";
import { Subject } from "@/types";
import {
  PRICE_LIMITS,
  RATING_OPTIONS,
  EXPERIENCE_OPTIONS,
} from "@/types/filters";

interface FilterPanelProps {
  isOpen: boolean;
  onClose: () => void;
  subjects: Subject[];
  selectedSubject?: number;
  priceRange: [number, number];
  minRating?: number;
  minExperience?: number;
  onSubjectChange: (id?: number) => void;
  onPriceChange: (range: [number, number]) => void;
  onMinRatingChange: (rating?: number) => void;
  onMinExperienceChange: (years?: number) => void;
  onClearAll: () => void;
  resultsCount: number;
}

export default function FilterPanel({
  isOpen,
  onClose,
  subjects,
  selectedSubject,
  priceRange,
  minRating,
  minExperience,
  onSubjectChange,
  onPriceChange,
  onMinRatingChange,
  onMinExperienceChange,
  onClearAll,
  resultsCount,
}: FilterPanelProps) {
  const [tempPrice, setTempPrice] = useState<[number, number]>(priceRange);

  useEffect(() => {
    setTempPrice(priceRange);
  }, [priceRange]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  const handleApply = () => {
    onPriceChange(tempPrice);
    onClose();
  };

  const activeFiltersCount =
    (selectedSubject ? 1 : 0) +
    (priceRange[0] !== PRICE_LIMITS.min || priceRange[1] !== PRICE_LIMITS.max
      ? 1
      : 0) +
    (minRating ? 1 : 0) +
    (minExperience ? 1 : 0);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 animate-fade-in"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed inset-x-0 bottom-0 bg-white z-50 rounded-t-3xl max-h-[85vh] overflow-hidden flex flex-col animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 bg-white sticky top-0 z-10">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Filters</h2>
            <p className="text-sm text-slate-500 mt-0.5">
              {resultsCount} tutors available
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-full transition-colors"
            aria-label="Close filters"
          >
            <FiX className="w-5 h-5 text-slate-700" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Subject */}
          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white mb-3">
              <FiBookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              Subject
            </label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              <button
                onClick={() => onSubjectChange(undefined)}
                className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all min-h-[44px] touch-manipulation ${
                  !selectedSubject
                    ? "bg-emerald-600 text-white shadow-md"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                All Subjects
              </button>
              {subjects.map((subject) => (
                <button
                  key={subject.id}
                  onClick={() => onSubjectChange(subject.id)}
                  className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all text-left min-h-[44px] touch-manipulation ${
                    selectedSubject === subject.id
                      ? "bg-emerald-600 text-white shadow-md"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  {subject.name}
                </button>
              ))}
            </div>
          </div>

          {/* Price */}
          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-900 mb-3">
              <FiDollarSign className="w-4 h-4 text-sky-600" />
              Price Range ($/hour)
            </label>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  value={tempPrice[0]}
                  onChange={(e) =>
                    setTempPrice([
                      Math.min(
                        Number(e.target.value),
                        tempPrice[1] - PRICE_LIMITS.step
                      ),
                      tempPrice[1],
                    ])
                  }
                  className="flex-1 px-4 py-2.5 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  min={PRICE_LIMITS.min}
                  max={tempPrice[1] - PRICE_LIMITS.step}
                />
                <span className="text-slate-500 font-medium">to</span>
                <input
                  type="number"
                  value={tempPrice[1]}
                  onChange={(e) =>
                    setTempPrice([
                      tempPrice[0],
                      Math.max(
                        Number(e.target.value),
                        tempPrice[0] + PRICE_LIMITS.step
                      ),
                    ])
                  }
                  className="flex-1 px-4 py-2.5 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  min={tempPrice[0] + PRICE_LIMITS.step}
                  max={PRICE_LIMITS.max}
                />
              </div>

              <div className="space-y-2">
                <input
                  type="range"
                  min={PRICE_LIMITS.min}
                  max={PRICE_LIMITS.max}
                  step={PRICE_LIMITS.step}
                  value={tempPrice[1]}
                  onChange={(e) =>
                    setTempPrice([
                      tempPrice[0],
                      Math.max(
                        Number(e.target.value),
                        tempPrice[0] + PRICE_LIMITS.step
                      ),
                    ])
                  }
                  className="w-full h-2 bg-gradient-to-r from-emerald-200 to-emerald-500 rounded-full appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-slate-500 font-medium">
                  <span>${PRICE_LIMITS.min}</span>
                  <span>${PRICE_LIMITS.max}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Rating */}
          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white mb-3">
              <FiStar className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              Minimum Rating
            </label>
            <div className="space-y-2">
              <button
                onClick={() => onMinRatingChange(undefined)}
                className={`w-full px-4 py-2.5 rounded-xl text-sm font-medium text-left flex items-center justify-between transition-all min-h-[44px] touch-manipulation ${
                  !minRating
                    ? "bg-emerald-600 text-white shadow-md"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                <span>Any Rating</span>
                {!minRating && <FiCheck className="w-4 h-4" />}
              </button>
              {RATING_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => onMinRatingChange(option.value)}
                  className={`w-full px-4 py-2.5 rounded-xl text-sm font-medium text-left flex items-center justify-between transition-all min-h-[44px] touch-manipulation ${
                    minRating === option.value
                      ? "bg-emerald-600 text-white shadow-md"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  <span>{option.label}</span>
                  {minRating === option.value && <FiCheck className="w-4 h-4" />}
                </button>
              ))}
            </div>
          </div>

          {/* Experience */}
          <div>
            <label className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white mb-3">
              <FiClock className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              Minimum Experience
            </label>
            <div className="space-y-2">
              <button
                onClick={() => onMinExperienceChange(undefined)}
                className={`w-full px-4 py-2.5 rounded-xl text-sm font-medium text-left flex items-center justify-between transition-all min-h-[44px] touch-manipulation ${
                  !minExperience
                    ? "bg-emerald-600 text-white shadow-md"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
                }`}
              >
                <span>Any Experience</span>
                {!minExperience && <FiCheck className="w-4 h-4" />}
              </button>
              {EXPERIENCE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => onMinExperienceChange(option.value)}
                  className={`w-full px-4 py-2.5 rounded-xl text-sm font-medium text-left flex items-center justify-between transition-all min-h-[44px] touch-manipulation ${
                    minExperience === option.value
                      ? "bg-emerald-600 text-white shadow-md"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  <span>{option.label}</span>
                  {minExperience === option.value && (
                    <FiCheck className="w-4 h-4" />
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-200 bg-white space-y-3">
          {activeFiltersCount > 0 && (
            <button
              onClick={onClearAll}
              className="w-full py-3 border-2 border-slate-300 text-slate-700 rounded-xl font-semibold hover:bg-slate-50 transition-all"
            >
              Clear All Filters ({activeFiltersCount})
            </button>
          )}
          <button
            onClick={handleApply}
            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white py-3 rounded-xl font-bold hover:shadow-lg transition-all min-h-[44px] touch-manipulation"
          >
            Show {resultsCount} Results
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes fade-in {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }
        @keyframes slide-up {
          from {
            transform: translateY(100%);
          }
          to {
            transform: translateY(0);
          }
        }
        .animate-fade-in {
          animation: fade-in 0.2s ease-out;
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
      `}</style>
    </>
  );
}
