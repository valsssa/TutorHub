'use client';

import { useState } from 'react';
import { Search, SlidersHorizontal, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { useTutors, useSubjects } from '@/lib/hooks';
import { useFiltersStore } from '@/lib/stores';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Badge,
} from '@/components/ui';
import { TutorCard, TutorCardSkeleton } from '@/components/tutors';

const PRICE_RANGES = [
  { label: 'Any', min: undefined, max: undefined },
  { label: 'Under $25', min: undefined, max: 25 },
  { label: '$25 - $50', min: 25, max: 50 },
  { label: '$50 - $100', min: 50, max: 100 },
  { label: 'Over $100', min: 100, max: undefined },
];

const SORT_OPTIONS = [
  { value: 'rating', label: 'Top Rated' },
  { value: 'rate_asc', label: 'Lowest Price' },
  { value: 'experience', label: 'Most Experience' },
] as const;

export default function TutorsPage() {
  const { tutorFilters, setTutorFilters, resetTutorFilters } = useFiltersStore();
  const { data: tutorsData, isLoading } = useTutors(tutorFilters);
  const { data: subjects } = useSubjects();

  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedPriceRange, setSelectedPriceRange] = useState(0);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setTutorFilters({ subject: searchQuery || undefined, page: 1 });
  };

  const handleSubjectClick = (subjectName: string) => {
    setSearchQuery(subjectName);
    setTutorFilters({ subject: subjectName, page: 1 });
  };

  const handlePriceRangeChange = (index: number) => {
    setSelectedPriceRange(index);
    const range = PRICE_RANGES[index];
    setTutorFilters({
      price_min: range.min,
      price_max: range.max,
      page: 1,
    });
  };

  const handleSortChange = (sortBy: 'rating' | 'rate_asc' | 'rate_desc' | 'experience') => {
    setTutorFilters({ sort_by: sortBy, page: 1 });
  };

  const handlePageChange = (newPage: number) => {
    setTutorFilters({ page: newPage });
  };

  const clearFilters = () => {
    resetTutorFilters();
    setSearchQuery('');
    setSelectedPriceRange(0);
  };

  const hasActiveFilters =
    tutorFilters.subject ||
    tutorFilters.price_min !== undefined ||
    tutorFilters.price_max !== undefined;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Find a Tutor
          </h1>
          <p className="text-slate-500">
            Browse our network of qualified tutors
          </p>
        </div>
        <Button
          variant="outline"
          className="lg:hidden"
          onClick={() => setShowFilters(!showFilters)}
        >
          <SlidersHorizontal className="h-4 w-4 mr-2" />
          Filters
        </Button>
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        <aside
          className={`lg:w-72 shrink-0 space-y-4 ${
            showFilters ? 'block' : 'hidden lg:block'
          }`}
        >
          {showFilters && (
            <div className="flex items-center justify-between lg:hidden">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Filters</h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFilters(false)}
              >
                <X className="h-4 w-4 mr-1" />
                Close
              </Button>
            </div>
          )}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Search</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSearch}>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    type="text"
                    placeholder="Search by subject..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Popular Subjects</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {subjects?.slice(0, 8).map((subject) => (
                  <Badge
                    key={subject.id}
                    variant={tutorFilters.subject === subject.name ? 'primary' : 'default'}
                    className="cursor-pointer hover:bg-primary-100 dark:hover:bg-primary-900/30 transition-colors"
                    onClick={() => handleSubjectClick(subject.name)}
                  >
                    {subject.name}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Price Range</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {PRICE_RANGES.map((range, index) => (
                  <label
                    key={range.label}
                    className="flex items-center gap-3 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name="price-range"
                      checked={selectedPriceRange === index}
                      onChange={() => handlePriceRangeChange(index)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">
                      {range.label}
                    </span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Sort By</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {SORT_OPTIONS.map((option) => (
                  <label
                    key={option.value}
                    className="flex items-center gap-3 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name="sort-by"
                      checked={tutorFilters.sort_by === option.value}
                      onChange={() => handleSortChange(option.value)}
                      className="h-4 w-4 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-slate-700 dark:text-slate-300">
                      {option.label}
                    </span>
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          {hasActiveFilters && (
            <Button variant="ghost" className="w-full" onClick={clearFilters}>
              <X className="h-4 w-4 mr-2" />
              Clear Filters
            </Button>
          )}
        </aside>

        <main className="flex-1">
          {hasActiveFilters && (
            <div className="mb-4 flex items-center gap-2 flex-wrap">
              <span className="text-sm text-slate-500">Active filters:</span>
              {tutorFilters.subject && (
                <Badge variant="primary">
                  Subject: {tutorFilters.subject}
                </Badge>
              )}
              {(tutorFilters.price_min !== undefined ||
                tutorFilters.price_max !== undefined) && (
                <Badge variant="primary">
                  {PRICE_RANGES[selectedPriceRange].label}
                </Badge>
              )}
            </div>
          )}

          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <TutorCardSkeleton key={i} />
              ))}
            </div>
          ) : tutorsData?.items.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Search className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                  No tutors found
                </h3>
                <p className="text-slate-500 mb-4">
                  Try adjusting your search or filters
                </p>
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              </CardContent>
            </Card>
          ) : (
            <>
              <div className="mb-4 text-sm text-slate-500">
                Showing {tutorsData?.items.length} of {tutorsData?.total} tutors
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {tutorsData?.items.map((tutor) => (
                  <TutorCard key={tutor.id} tutor={tutor} />
                ))}
              </div>

              {tutorsData && tutorsData.total_pages > 1 && (
                <div className="mt-8 flex items-center justify-center gap-2 flex-wrap">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={tutorsData.page === 1}
                    onClick={() => handlePageChange(tutorsData.page - 1)}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <div className="flex items-center gap-1 flex-wrap">
                    {Array.from({ length: tutorsData.total_pages }).map((_, i) => {
                      const page = i + 1;
                      const isCurrentPage = page === tutorsData.page;
                      const showPage =
                        page === 1 ||
                        page === tutorsData.total_pages ||
                        Math.abs(page - tutorsData.page) <= 1;

                      if (!showPage) {
                        if (page === 2 || page === tutorsData.total_pages - 1) {
                          return (
                            <span
                              key={page}
                              className="px-2 text-slate-400"
                            >
                              ...
                            </span>
                          );
                        }
                        return null;
                      }

                      return (
                        <Button
                          key={page}
                          variant={isCurrentPage ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => handlePageChange(page)}
                          className="min-w-[36px]"
                        >
                          {page}
                        </Button>
                      );
                    })}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={tutorsData.page === tutorsData.total_pages}
                    onClick={() => handlePageChange(tutorsData.page + 1)}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
