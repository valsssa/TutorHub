"use client";

import { useState, useRef, useEffect } from "react";
import { Search, ChevronDown, SlidersHorizontal, X, Check, Star } from "lucide-react";
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

type FilterDropdown = "subject" | "price" | "rating" | "experience" | "sort" | null;

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
  const [activeDropdown, setActiveDropdown] = useState<FilterDropdown>(null);
  const [tempPrice, setTempPrice] = useState<[number, number]>(priceRange);
  const [isMobileFilterOpen, setIsMobileFilterOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTempPrice(priceRange);
  }, [priceRange]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setActiveDropdown(null);
      }
    };

    if (activeDropdown) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [activeDropdown]);

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

  const getPriceLabel = () => {
    if (priceRange[0] === PRICE_LIMITS.min && priceRange[1] === PRICE_LIMITS.max) {
      return "Any price";
    }
    return `$${priceRange[0]} - $${priceRange[1]}`;
  };

  const clearAllFilters = () => {
    onSubjectChange(undefined);
    onPriceChange([PRICE_LIMITS.min, PRICE_LIMITS.max]);
    onMinRatingChange(undefined);
    onMinExperienceChange(undefined);
    onSearchChange("");
  };

  const activeFiltersCount = 
    (selectedSubject ? 1 : 0) +
    (priceRange[0] !== PRICE_LIMITS.min || priceRange[1] !== PRICE_LIMITS.max ? 1 : 0) +
    (minRating ? 1 : 0) +
    (minExperience ? 1 : 0);

  return (
    <section className="bg-slate-50 dark:bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 py-2" ref={dropdownRef}>


        {/* --- MOBILE: Search Bar & Filter Toggle --- */}
        <div className="md:hidden mb-6">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input 
                type="text"
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search name or subject..."
                className="w-full h-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl py-3 pl-10 pr-4 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 shadow-sm"
              />
            </div>
            <button 
              onClick={() => setIsMobileFilterOpen(true)}
              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-white px-4 rounded-xl shadow-sm flex items-center justify-center hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors relative"
            >
              <SlidersHorizontal size={20} />
              {activeFiltersCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-emerald-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {activeFiltersCount}
                </span>
              )}
            </button>
          </div>
          {/* Active Filter Chips */}
          {activeFiltersCount > 0 && (
            <div className="flex gap-2 mt-3 overflow-x-auto pb-1 scrollbar-hide">
              {selectedSubject && (
                <span className="px-3 py-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 text-xs font-bold rounded-full whitespace-nowrap">
                  {getSelectedSubjectName()}
                </span>
              )}
              {(priceRange[0] !== PRICE_LIMITS.min || priceRange[1] !== PRICE_LIMITS.max) && (
                <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-full whitespace-nowrap">
                  {getPriceLabel()}
                </span>
              )}
              {minRating && (
                <span className="px-3 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 text-xs font-bold rounded-full whitespace-nowrap">
                  {getSelectedRatingLabel()}
                </span>
              )}
              {minExperience && (
                <span className="px-3 py-1 bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold rounded-full whitespace-nowrap">
                  {getSelectedExperienceLabel()}
                </span>
              )}
            </div>
          )}
        </div>

        {/* --- DESKTOP: Full Filter Grid --- */}
        <div className="hidden md:block space-y-4">
          {/* Row 1: Primary Filters */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
            
            {/* Subject Filter */}
            <div className="relative z-30">
              <button 
                onClick={() => setActiveDropdown(activeDropdown === 'subject' ? null : 'subject')}
                className={`w-full h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'subject' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-pointer text-left relative z-20 flex flex-col justify-center`}
              >
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">I want to learn</label>
                <div className="flex items-center justify-between w-full">
                  <span className="text-slate-900 dark:text-white font-bold text-sm truncate pr-2">
                    {getSelectedSubjectName()}
                  </span>
                  <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 flex-shrink-0 ${activeDropdown === 'subject' ? 'rotate-180' : ''}`} />
                </div>
              </button>

              {activeDropdown === 'subject' && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                  <div className="absolute top-[calc(100%+8px)] left-0 right-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 max-h-[350px] overflow-y-auto py-2">
                    <button
                      onClick={() => {
                        onSubjectChange(undefined);
                        setActiveDropdown(null);
                      }}
                      className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium flex items-center justify-between ${
                        !selectedSubject ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-700 dark:text-slate-200'
                      }`}
                    >
                      <span>All Subjects</span>
                      {!selectedSubject && <Check size={16} className="text-emerald-500" />}
                    </button>
                    {subjects.map(subject => (
                      <button
                        key={subject.id}
                        onClick={() => {
                          onSubjectChange(subject.id);
                          setActiveDropdown(null);
                        }}
                        className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium flex items-center justify-between ${
                          selectedSubject === subject.id ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-700 dark:text-slate-200'
                        }`}
                      >
                        <span>{subject.name}</span>
                        {selectedSubject === subject.id && <Check size={16} className="text-emerald-500" />}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Price Filter */}
            <div className="relative z-20">
              <button 
                onClick={() => setActiveDropdown(activeDropdown === 'price' ? null : 'price')}
                className={`w-full h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'price' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-pointer text-left relative z-20 flex flex-col justify-center`}
              >
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">Price per lesson</label>
                <div className="flex items-center justify-between w-full">
                  <span className="text-slate-900 dark:text-white font-bold text-sm truncate">
                    {getPriceLabel()}
                  </span>
                  <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 flex-shrink-0 ${activeDropdown === 'price' ? 'rotate-180' : ''}`} />
                </div>
              </button>

              {activeDropdown === 'price' && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                  <div className="absolute top-[calc(100%+8px)] left-0 right-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl p-6 z-30">
                    <div className="text-center font-bold text-2xl text-slate-900 dark:text-white mb-6">
                      {tempPrice[0] === PRICE_LIMITS.min && tempPrice[1] === PRICE_LIMITS.max 
                        ? 'Any price' 
                        : `$${tempPrice[0]} - $${tempPrice[1]}`}
                    </div>
                    
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <input
                          type="number"
                          value={tempPrice[0]}
                          onChange={(e) =>
                            setTempPrice([
                              Math.min(Number(e.target.value), tempPrice[1] - PRICE_LIMITS.step),
                              tempPrice[1],
                            ])
                          }
                          className="w-24 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
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
                              Math.max(Number(e.target.value), tempPrice[0] + PRICE_LIMITS.step),
                            ])
                          }
                          className="w-24 px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white dark:bg-slate-800 text-slate-900 dark:text-white"
                          min={tempPrice[0] + PRICE_LIMITS.step}
                          max={PRICE_LIMITS.max}
                        />
                      </div>

                      <div className="relative h-8 flex items-center px-2">
                        <div className="absolute left-0 right-0 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                        <div 
                          className="absolute left-0 h-1.5 bg-emerald-500 rounded-full" 
                          style={{ width: `${((tempPrice[1] - PRICE_LIMITS.min) / (PRICE_LIMITS.max - PRICE_LIMITS.min)) * 100}%` }}
                        ></div>
                        <input 
                          type="range"
                          min={PRICE_LIMITS.min}
                          max={PRICE_LIMITS.max}
                          step={PRICE_LIMITS.step}
                          value={tempPrice[1]}
                          onChange={(e) =>
                            setTempPrice([
                              tempPrice[0],
                              Math.max(Number(e.target.value), tempPrice[0] + PRICE_LIMITS.step),
                            ])
                          }
                          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                        />
                        <div 
                          className="absolute w-6 h-6 bg-white border-2 border-emerald-500 rounded-full shadow-sm z-10 pointer-events-none"
                          style={{ 
                            left: `calc(${((tempPrice[1] - PRICE_LIMITS.min) / (PRICE_LIMITS.max - PRICE_LIMITS.min)) * 100}% - 12px)` 
                          }}
                        ></div>
                      </div>
                      
                      <div className="flex justify-between text-xs text-slate-500 font-medium">
                        <span>${PRICE_LIMITS.min}</span>
                        <span>${PRICE_LIMITS.max}+</span>
                      </div>

                      <button
                        onClick={() => {
                          onPriceChange(tempPrice);
                          setActiveDropdown(null);
                        }}
                        className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-bold transition-all"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Rating Filter */}
            <div className="relative z-10">
              <button 
                onClick={() => setActiveDropdown(activeDropdown === 'rating' ? null : 'rating')}
                className={`w-full h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'rating' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-pointer text-left relative z-20 flex flex-col justify-center`}
              >
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">Minimum rating</label>
                <div className="flex items-center justify-between w-full">
                  <span className="text-slate-900 dark:text-white font-bold text-sm truncate pr-2 flex items-center gap-1">
                    {minRating && <Star size={14} className="text-amber-400 fill-amber-400" />}
                    {getSelectedRatingLabel()}
                  </span>
                  <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 flex-shrink-0 ${activeDropdown === 'rating' ? 'rotate-180' : ''}`} />
                </div>
              </button>

              {activeDropdown === 'rating' && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                  <div className="absolute top-[calc(100%+8px)] left-0 w-full md:w-[280px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 py-2">
                    <button
                      onClick={() => {
                        onMinRatingChange(undefined);
                        setActiveDropdown(null);
                      }}
                      className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium flex items-center justify-between ${
                        !minRating ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-700 dark:text-slate-200'
                      }`}
                    >
                      <span>Any Rating</span>
                      {!minRating && <Check size={16} className="text-emerald-500" />}
                    </button>
                    {RATING_OPTIONS.map(option => (
                      <button
                        key={option.value}
                        onClick={() => {
                          onMinRatingChange(option.value);
                          setActiveDropdown(null);
                        }}
                        className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium flex items-center justify-between ${
                          minRating === option.value ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-700 dark:text-slate-200'
                        }`}
                      >
                        <span className="flex items-center gap-1">
                          <Star size={14} className="text-amber-400 fill-amber-400" />
                          {option.label}
                        </span>
                        {minRating === option.value && <Check size={16} className="text-emerald-500" />}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Experience Filter */}
            <div className="relative z-0">
              <button 
                onClick={() => setActiveDropdown(activeDropdown === 'experience' ? null : 'experience')}
                className={`w-full h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'experience' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} rounded-xl px-4 py-3 hover:border-slate-300 dark:hover:border-slate-600 transition-all cursor-pointer text-left relative z-20 flex flex-col justify-center`}
              >
                <label className="block text-xs font-medium text-slate-500 dark:text-slate-400 mb-0.5">Experience level</label>
                <div className="flex items-center justify-between w-full">
                  <span className="text-slate-900 dark:text-white font-bold text-sm truncate pr-2">
                    {getSelectedExperienceLabel()}
                  </span>
                  <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 flex-shrink-0 ${activeDropdown === 'experience' ? 'rotate-180' : ''}`} />
                </div>
              </button>

              {activeDropdown === 'experience' && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                  <div className="absolute top-[calc(100%+8px)] right-0 w-full md:w-[280px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 py-2">
                    <button
                      onClick={() => {
                        onMinExperienceChange(undefined);
                        setActiveDropdown(null);
                      }}
                      className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium flex items-center justify-between ${
                        !minExperience ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-700 dark:text-slate-200'
                      }`}
                    >
                      <span>Any Experience</span>
                      {!minExperience && <Check size={16} className="text-emerald-500" />}
                    </button>
                    {EXPERIENCE_OPTIONS.map(option => (
                      <button
                        key={option.value}
                        onClick={() => {
                          onMinExperienceChange(option.value);
                          setActiveDropdown(null);
                        }}
                        className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium flex items-center justify-between ${
                          minExperience === option.value ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-700 dark:text-slate-200'
                        }`}
                      >
                        <span>{option.label}</span>
                        {minExperience === option.value && <Check size={16} className="text-emerald-500" />}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Row 2: Secondary Filters */}
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Sort Dropdown */}
            {/* <div className="relative">
              <button 
                onClick={() => setActiveDropdown(activeDropdown === 'sort' ? null : 'sort')}
                className={`h-full bg-white dark:bg-slate-900 border ${activeDropdown === 'sort' ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 dark:border-slate-700'} text-slate-700 dark:text-slate-300 font-medium px-4 py-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 whitespace-nowrap z-20 relative`}
              >
                Sort: {getSelectedSortLabel()} 
                <ChevronDown size={16} className={`text-slate-400 transition-transform duration-200 ${activeDropdown === 'sort' ? 'rotate-180' : ''}`} />
              </button>

              {activeDropdown === 'sort' && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setActiveDropdown(null)} />
                  <div className="absolute top-[calc(100%+8px)] left-0 w-[220px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl z-30 py-2">
                    {SORT_OPTIONS.map(option => (
                      <button
                        key={option.value}
                        onClick={() => {
                          onSortChange(option.value);
                          setActiveDropdown(null);
                        }}
                        className={`w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors text-sm font-medium flex items-center justify-between ${
                          sortBy === option.value ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-700 dark:text-slate-200'
                        }`}
                      >
                        <span>{option.label}</span>
                        {sortBy === option.value && <Check size={16} className="text-emerald-500" />}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div> */}

            {/* Clear Filters Button */}
            {activeFiltersCount > 0 && (
              <button 
                onClick={clearAllFilters}
                className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium px-4 py-3 rounded-xl hover:bg-red-50 hover:text-red-600 hover:border-red-200 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors flex items-center gap-2 whitespace-nowrap"
              >
                <X size={16} />
                Clear filters ({activeFiltersCount})
              </button>
            )}

            {/* Keyword Search */}
            <div className="flex-1 relative group">
              <input 
                type="text"
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                placeholder="Search by name or keyword"
                className="w-full h-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl py-3 pl-10 pr-4 text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500 dark:focus:border-emerald-500 transition-colors"
              />
              <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-emerald-600 dark:group-focus-within:text-emerald-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Filter Modal */}
      {isMobileFilterOpen && (
        <div className="fixed inset-0 z-50 bg-white dark:bg-slate-950 flex flex-col md:hidden">
          {/* Modal Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-slate-900">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Filters</h2>
            <button 
              onClick={() => setIsMobileFilterOpen(false)}
              className="p-2 bg-slate-100 dark:bg-slate-800 rounded-full text-slate-500 dark:text-slate-400"
            >
              <X size={20} />
            </button>
          </div>

          {/* Modal Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-8 pb-32">
            
            {/* Subject */}
            <div>
              <label className="block text-sm font-bold text-slate-900 dark:text-white mb-2">Subject</label>
              <select 
                value={selectedSubject || ""}
                onChange={(e) => onSubjectChange(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full p-3 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white"
              >
                <option value="">All Subjects</option>
                {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>

            {/* Price */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <label className="text-sm font-bold text-slate-900 dark:text-white">Max Price</label>
                <span className="text-emerald-600 font-bold">${priceRange[1]}</span>
              </div>
              <input 
                type="range"
                min={PRICE_LIMITS.min}
                max={PRICE_LIMITS.max}
                step={PRICE_LIMITS.step}
                value={priceRange[1]}
                onChange={(e) => onPriceChange([priceRange[0], Number(e.target.value)])}
                className="w-full h-2 bg-slate-200 dark:bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
              />
            </div>

            {/* Rating */}
            <div>
              <label className="block text-sm font-bold text-slate-900 dark:text-white mb-2">Minimum Rating</label>
              <select 
                value={minRating || ""}
                onChange={(e) => onMinRatingChange(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full p-3 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white"
              >
                <option value="">Any Rating</option>
                {RATING_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>

            {/* Experience */}
            <div>
              <label className="block text-sm font-bold text-slate-900 dark:text-white mb-2">Experience Level</label>
              <select 
                value={minExperience || ""}
                onChange={(e) => onMinExperienceChange(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full p-3 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white"
              >
                <option value="">Any Experience</option>
                {EXPERIENCE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>

            {/* Sort */}
            <div>
              <label className="block text-sm font-bold text-slate-900 dark:text-white mb-2">Sort By</label>
              <select 
                value={sortBy}
                onChange={(e) => onSortChange(e.target.value)}
                className="w-full p-3 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-sm text-slate-900 dark:text-white"
              >
                {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
            </div>
          </div>

          {/* Modal Footer */}
          <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 absolute bottom-0 left-0 w-full flex gap-3">
            <button 
              onClick={clearAllFilters}
              className="flex-1 py-3 text-slate-600 dark:text-slate-300 font-bold border border-slate-200 dark:border-slate-700 rounded-xl"
            >
              Clear All
            </button>
            <button 
              onClick={() => setIsMobileFilterOpen(false)}
              className="flex-[2] py-3 bg-emerald-600 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/20"
            >
              Show {resultsCount} Tutors
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
