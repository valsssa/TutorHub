/**
 * Filter type definitions
 */

export interface TutorFilters {
  searchTerm: string;
  subjectId?: number;
  priceRange: [number, number];
  minRating?: number;
  minExperience?: number;
  languages?: string[];
  availability?: string;
}

export interface FilterOption<T = unknown> {
  value: T;
  label: string;
  icon?: React.ReactNode;
}

export const SORT_OPTIONS: FilterOption<string>[] = [
  { value: "rating", label: "Best Match" },
  { value: "rate_asc", label: "Price: Low to High" },
  { value: "rate_desc", label: "Price: High to Low" },
  { value: "experience", label: "Most Experienced" },
  { value: "sessions", label: "Most Popular" },
];

export const RATING_OPTIONS: FilterOption<number>[] = [
  { value: 5, label: "5 Stars" },
  { value: 4.5, label: "4.5+ Stars" },
  { value: 4, label: "4+ Stars" },
  { value: 3.5, label: "3.5+ Stars" },
];

export const EXPERIENCE_OPTIONS: FilterOption<number>[] = [
  { value: 1, label: "1+ Years" },
  { value: 3, label: "3+ Years" },
  { value: 5, label: "5+ Years" },
  { value: 10, label: "10+ Years" },
];

export const DEFAULT_FILTERS: TutorFilters = {
  searchTerm: "",
  priceRange: [5, 200],
  minRating: undefined,
  minExperience: undefined,
  languages: [],
  availability: undefined,
};

export const PRICE_LIMITS = {
  min: 5,
  max: 200,
  step: 5,
} as const;
