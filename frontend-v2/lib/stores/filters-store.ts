import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { TutorFilters, BookingFilters } from '@/types';

interface FiltersState {
  tutorFilters: TutorFilters;
  setTutorFilters: (filters: Partial<TutorFilters>) => void;
  resetTutorFilters: () => void;

  bookingFilters: BookingFilters;
  setBookingFilters: (filters: Partial<BookingFilters>) => void;
  resetBookingFilters: () => void;

  _hasHydrated: boolean;
  setHasHydrated: (state: boolean) => void;
}

const defaultTutorFilters: TutorFilters = {
  sort_by: 'rating',
  page: 1,
  page_size: 12,
};

const defaultBookingFilters: BookingFilters = {
  page: 1,
  page_size: 10,
};

export const useFiltersStore = create<FiltersState>()(
  persist(
    (set) => ({
      tutorFilters: defaultTutorFilters,
      setTutorFilters: (filters) =>
        set((s) => ({
          tutorFilters: { ...s.tutorFilters, ...filters, page: filters.page ?? 1 },
        })),
      resetTutorFilters: () => set({ tutorFilters: defaultTutorFilters }),

      bookingFilters: defaultBookingFilters,
      setBookingFilters: (filters) =>
        set((s) => ({
          bookingFilters: { ...s.bookingFilters, ...filters },
        })),
      resetBookingFilters: () => set({ bookingFilters: defaultBookingFilters }),

      _hasHydrated: false,
      setHasHydrated: (state) => set({ _hasHydrated: state }),
    }),
    {
      name: 'edustream-filters',
      storage: createJSONStorage(() => {
        // Return a no-op storage during SSR
        if (typeof window === 'undefined') {
          return {
            getItem: () => null,
            setItem: () => {},
            removeItem: () => {},
          };
        }
        return localStorage;
      }),
      partialize: (state) => ({
        tutorFilters: state.tutorFilters,
      }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    }
  )
);
