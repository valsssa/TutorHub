"use client";

import { useState, useEffect, useRef } from "react";
import {
  FiBookOpen,
  FiDollarSign,
  FiStar,
  FiClock,
  FiX,
  FiCheck,
} from "react-icons/fi";
import { Subject } from "@/types";
import {
  PRICE_LIMITS,
  RATING_OPTIONS,
  EXPERIENCE_OPTIONS,
} from "@/types/filters";

interface FilterBarProps {
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
  activeFiltersCount?: number;
}

type FilterDropdown = "subject" | "price" | "rating" | "experience" | null;

export default function FilterBar({
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
  activeFiltersCount = 0,
}: FilterBarProps) {
  const [activeDropdown, setActiveDropdown] = useState<FilterDropdown>(null);
  const [tempPrice, setTempPrice] = useState<[number, number]>(priceRange);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTempPrice(priceRange);
  }, [priceRange]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setActiveDropdown(null);
      }
    };

    if (activeDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [activeDropdown]);

  const toggleDropdown = (dropdown: FilterDropdown) => {
    setActiveDropdown((prev) => (prev === dropdown ? null : dropdown));
  };

  const closeDropdown = () => {
    setActiveDropdown(null);
  };

  const handlePriceApply = () => {
    onPriceChange(tempPrice);
    closeDropdown();
  };

  const isFilterActive = (type: FilterDropdown): boolean => {
    switch (type) {
      case "subject":
        return selectedSubject !== undefined;
      case "price":
        return (
          priceRange[0] !== PRICE_LIMITS.min ||
          priceRange[1] !== PRICE_LIMITS.max
        );
      case "rating":
        return minRating !== undefined;
      case "experience":
        return minExperience !== undefined;
      default:
        return false;
    }
  };

  const getFilterLabel = (type: FilterDropdown): string => {
    switch (type) {
      case "subject":
        return (
          subjects.find((s) => s.id === selectedSubject)?.name || "Subject"
        );
      case "price":
        return priceRange[0] === PRICE_LIMITS.min &&
          priceRange[1] === PRICE_LIMITS.max
          ? "Price"
          : `$${priceRange[0]}-$${priceRange[1]}`;
      case "rating":
        return minRating ? `${minRating}+ ⭐` : "Rating";
      case "experience":
        return minExperience ? `${minExperience}+ Years` : "Experience";
      default:
        return "";
    }
  };

  const FilterButton = ({
    type,
    icon: Icon,
  }: {
    type: FilterDropdown;
    icon: typeof FiBookOpen;
  }) => {
    const active = isFilterActive(type);
    const isOpen = activeDropdown === type;

    return (
      <button
        onClick={() => toggleDropdown(type)}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium tap-target
          transition-all duration-200 whitespace-nowrap
          ${
            active
              ? "bg-gradient-to-r from-sky-500 to-blue-500 text-white shadow-md"
              : "bg-white text-slate-700 border border-slate-200 hover:border-sky-300 hover:bg-sky-50"
          }
        `}
      >
        <Icon className="w-4 h-4 flex-shrink-0" />
        <span>{getFilterLabel(type)}</span>
        <span
          className={`text-xs transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        >
          ▼
        </span>
      </button>
    );
  };

  return (
    <div
      ref={dropdownRef}
      className="sticky top-0 bg-white border-b border-slate-200 shadow-sm z-[10000]"
    >
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
          <FilterButton type="subject" icon={FiBookOpen} />
          <FilterButton type="price" icon={FiDollarSign} />
          <FilterButton type="rating" icon={FiStar} />
          <FilterButton type="experience" icon={FiClock} />

          {activeFiltersCount > 0 && (
            <button
              onClick={onClearAll}
              className="ml-auto flex items-center gap-2 px-4 py-2 text-sm font-medium text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition-all"
            >
              <FiX className="w-4 h-4" />
              Clear All ({activeFiltersCount})
            </button>
          )}
        </div>

        {/* Dropdowns */}
        {activeDropdown && (
          <div className="relative mt-2">
            <div className="absolute top-0 left-0 right-0 bg-white border border-slate-200 rounded-xl shadow-lg p-4 z-[10001] max-w-md">
              {/* Subject Dropdown */}
              {activeDropdown === "subject" && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">
                    Select Subject
                  </h3>
                  <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
                    <button
                      onClick={() => {
                        onSubjectChange(undefined);
                        closeDropdown();
                      }}
                      className={`px-3 py-2 rounded-lg text-sm font-medium text-left transition-all ${
                        !selectedSubject
                          ? "bg-sky-100 text-sky-700"
                          : "bg-slate-50 hover:bg-slate-100 text-slate-700"
                      }`}
                    >
                      All Subjects
                    </button>
                    {subjects.map((subject) => (
                      <button
                        key={subject.id}
                        onClick={() => {
                          onSubjectChange(subject.id);
                          closeDropdown();
                        }}
                        className={`px-3 py-2 rounded-lg text-sm font-medium text-left transition-all ${
                          selectedSubject === subject.id
                            ? "bg-sky-100 text-sky-700"
                            : "bg-slate-50 hover:bg-slate-100 text-slate-700"
                        }`}
                      >
                        {subject.name}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Price Dropdown */}
              {activeDropdown === "price" && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">
                    Price Range ($/hour)
                  </h3>
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
                        className="w-24 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                        min={PRICE_LIMITS.min}
                        max={tempPrice[1] - PRICE_LIMITS.step}
                      />
                      <span className="text-slate-500">to</span>
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
                        className="w-24 px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
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
                        className="w-full h-2 bg-gradient-to-r from-sky-200 to-sky-500 rounded-full appearance-none cursor-pointer"
                      />
                      <div className="flex justify-between text-xs text-slate-500">
                        <span>${PRICE_LIMITS.min}</span>
                        <span>${PRICE_LIMITS.max}</span>
                      </div>
                    </div>

                    <button
                      onClick={handlePriceApply}
                      className="w-full py-2 bg-gradient-to-r from-sky-500 to-blue-500 text-white rounded-lg font-medium hover:shadow-md transition-all"
                    >
                      Apply
                    </button>
                  </div>
                </div>
              )}

              {/* Rating Dropdown */}
              {activeDropdown === "rating" && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">
                    Minimum Rating
                  </h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => {
                        onMinRatingChange(undefined);
                        closeDropdown();
                      }}
                      className={`w-full px-3 py-2 rounded-lg text-sm font-medium text-left flex items-center justify-between transition-all ${
                        !minRating
                          ? "bg-sky-100 text-sky-700"
                          : "bg-slate-50 hover:bg-slate-100 text-slate-700"
                      }`}
                    >
                      <span>Any Rating</span>
                      {!minRating && <FiCheck className="w-4 h-4" />}
                    </button>
                    {RATING_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => {
                          onMinRatingChange(option.value);
                          closeDropdown();
                        }}
                        className={`w-full px-3 py-2 rounded-lg text-sm font-medium text-left flex items-center justify-between transition-all ${
                          minRating === option.value
                            ? "bg-sky-100 text-sky-700"
                            : "bg-slate-50 hover:bg-slate-100 text-slate-700"
                        }`}
                      >
                        <span>{option.label}</span>
                        {minRating === option.value && (
                          <FiCheck className="w-4 h-4" />
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience Dropdown */}
              {activeDropdown === "experience" && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-700 mb-3">
                    Minimum Experience
                  </h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => {
                        onMinExperienceChange(undefined);
                        closeDropdown();
                      }}
                      className={`w-full px-3 py-2 rounded-lg text-sm font-medium text-left flex items-center justify-between transition-all ${
                        !minExperience
                          ? "bg-sky-100 text-sky-700"
                          : "bg-slate-50 hover:bg-slate-100 text-slate-700"
                      }`}
                    >
                      <span>Any Experience</span>
                      {!minExperience && <FiCheck className="w-4 h-4" />}
                    </button>
                    {EXPERIENCE_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => {
                          onMinExperienceChange(option.value);
                          closeDropdown();
                        }}
                        className={`w-full px-3 py-2 rounded-lg text-sm font-medium text-left flex items-center justify-between transition-all ${
                          minExperience === option.value
                            ? "bg-sky-100 text-sky-700"
                            : "bg-slate-50 hover:bg-slate-100 text-slate-700"
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
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
