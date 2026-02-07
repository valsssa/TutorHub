'use client';

import { useState, useMemo, useCallback, useRef } from 'react';
import Link from 'next/link';
import {
  Heart,
  Search,
  ChevronLeft,
  ChevronRight,
  UserX,
  X,
} from 'lucide-react';
import { Card, CardContent, Button, Input } from '@/components/ui';
import { TutorCard, TutorCardSkeleton } from '@/components/tutors/tutor-card';
import { useFavorites, useRemoveFavorite } from '@/lib/hooks';
import { useToast } from '@/lib/stores/ui-store';

const PAGE_SIZE = 12;

export default function FavoritesPage() {
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [confirmingRemoveId, setConfirmingRemoveId] = useState<number | null>(null);
  const undoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { data: favorites, isLoading, error, refetch, pagination } = useFavorites({
    page,
    page_size: PAGE_SIZE,
  });
  const removeFavorite = useRemoveFavorite();
  const toast = useToast();

  // M52: Filter out favorites where tutor is null
  const validFavorites = useMemo(() => {
    if (!favorites) return [];
    return favorites.filter((f) => f.tutor !== null && f.tutor !== undefined);
  }, [favorites]);

  // Count of null-tutor favorites for display
  const unavailableCount = useMemo(() => {
    if (!favorites) return 0;
    return favorites.filter((f) => !f.tutor).length;
  }, [favorites]);

  // L34: Client-side search filter by tutor name
  const filteredFavorites = useMemo(() => {
    if (!searchQuery.trim()) return validFavorites;
    const query = searchQuery.toLowerCase().trim();
    return validFavorites.filter((f) => {
      const tutor = f.tutor;
      if (!tutor) return false;
      const displayName = tutor.display_name?.toLowerCase() ?? '';
      const firstName = tutor.first_name?.toLowerCase() ?? '';
      const lastName = tutor.last_name?.toLowerCase() ?? '';
      const fullName = `${firstName} ${lastName}`.trim();
      const headline = tutor.headline?.toLowerCase() ?? '';
      return (
        displayName.includes(query) ||
        fullName.includes(query) ||
        firstName.includes(query) ||
        lastName.includes(query) ||
        headline.includes(query)
      );
    });
  }, [validFavorites, searchQuery]);

  // M50: Confirmation + undo flow for removing favorites
  const handleRemoveClick = useCallback(
    (tutorProfileId: number) => {
      if (confirmingRemoveId === tutorProfileId) {
        // Second click confirms removal
        setConfirmingRemoveId(null);
        if (undoTimerRef.current) {
          clearTimeout(undoTimerRef.current);
          undoTimerRef.current = null;
        }
        removeFavorite.mutate(tutorProfileId, {
          onSuccess: () => {
            toast.success('Tutor removed from favorites');
          },
          onError: () => {
            toast.error('Failed to remove favorite. Please try again.');
          },
        });
      } else {
        // First click: enter confirmation state
        setConfirmingRemoveId(tutorProfileId);
        // Auto-cancel confirmation after 3 seconds
        if (undoTimerRef.current) {
          clearTimeout(undoTimerRef.current);
        }
        undoTimerRef.current = setTimeout(() => {
          setConfirmingRemoveId(null);
          undoTimerRef.current = null;
        }, 3000);
      }
    },
    [confirmingRemoveId, removeFavorite, toast]
  );

  const cancelConfirmation = useCallback(() => {
    setConfirmingRemoveId(null);
    if (undoTimerRef.current) {
      clearTimeout(undoTimerRef.current);
      undoTimerRef.current = null;
    }
  }, []);

  const totalPages = pagination?.total_pages ?? 0;
  const totalCount = pagination?.total ?? 0;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              My Favorite Tutors
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Tutors you have saved for quick access
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <TutorCardSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  // M51: Use refetch() instead of window.location.reload()
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Favorite Tutors
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Tutors you have saved for quick access
          </p>
        </div>

        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-red-500">Failed to load favorites. Please try again.</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => refetch()}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!favorites || (favorites.length === 0 && page === 1 && !searchQuery)) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Favorite Tutors
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Tutors you have saved for quick access
          </p>
        </div>

        <Card>
          <CardContent className="py-12 text-center">
            <div className="mx-auto w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
              <Heart className="h-6 w-6 sm:h-8 sm:w-8 text-slate-400" />
            </div>
            <h3 className="text-base sm:text-lg font-semibold text-slate-900 dark:text-white mb-2">
              No favorites yet
            </h3>
            <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-6 px-4">
              Start exploring tutors and click the heart icon to save your favorites for quick access.
            </p>
            <Button asChild>
              <Link href="/tutors">
                <Search className="mr-2 h-4 w-4" />
                Browse Tutors
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Favorite Tutors
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            {totalCount} {totalCount === 1 ? 'tutor' : 'tutors'} saved
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/tutors">
            <Search className="mr-2 h-4 w-4" />
            Find More Tutors
          </Link>
        </Button>
      </div>

      {/* L34: Search input for filtering favorites by tutor name */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          type="text"
          placeholder="Search favorites by name or headline..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 pr-10"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
            aria-label="Clear search"
          >
            <X className="h-4 w-4 text-slate-400" />
          </button>
        )}
      </div>

      {/* M52: Show notice if there are unavailable tutors */}
      {unavailableCount > 0 && (
        <div className="flex items-center gap-2 px-4 py-3 bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400 rounded-lg text-sm">
          <UserX className="h-4 w-4 shrink-0" />
          <span>
            {unavailableCount} {unavailableCount === 1 ? 'tutor is' : 'tutors are'} no longer available and {unavailableCount === 1 ? 'has' : 'have'} been hidden from your list.
          </span>
        </div>
      )}

      {filteredFavorites.length === 0 && searchQuery ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="h-10 w-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
            <p className="text-slate-600 dark:text-slate-400 font-medium mb-1">
              No favorites match your search
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-500">
              Try a different search term or{' '}
              <button
                onClick={() => setSearchQuery('')}
                className="text-primary-600 hover:underline"
              >
                clear the search
              </button>
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {filteredFavorites.map((favorite) => (
              <div key={favorite.id} className="relative overflow-hidden">
                {favorite.tutor && (
                  <TutorCard tutor={favorite.tutor} showFavorite={false} />
                )}
                {/* M50: Remove button with confirmation */}
                {confirmingRemoveId === favorite.tutor_profile_id ? (
                  <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-white dark:bg-slate-800 shadow-lg rounded-full px-2 py-1 border border-red-200 dark:border-red-800">
                    <button
                      onClick={() => handleRemoveClick(favorite.tutor_profile_id)}
                      disabled={removeFavorite.isPending}
                      className="text-xs font-medium text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 disabled:opacity-50 whitespace-nowrap"
                    >
                      Remove?
                    </button>
                    <button
                      onClick={cancelConfirmation}
                      className="p-0.5 rounded-full hover:bg-slate-100 dark:hover:bg-slate-700"
                      aria-label="Cancel removal"
                    >
                      <X className="h-3.5 w-3.5 text-slate-400" />
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => handleRemoveClick(favorite.tutor_profile_id)}
                    disabled={removeFavorite.isPending}
                    className="absolute top-4 right-4 p-2 rounded-full bg-white dark:bg-slate-800 shadow-md hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
                    aria-label="Remove from favorites"
                  >
                    <Heart
                      className={`h-5 w-5 ${
                        removeFavorite.isPending
                          ? 'text-slate-400 animate-pulse'
                          : 'fill-red-500 text-red-500'
                      }`}
                    />
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* M49: Pagination controls */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-500 order-2 sm:order-1">
                Page {page} of {totalPages} ({totalCount} {totalCount === 1 ? 'tutor' : 'tutors'})
              </p>
              <div className="flex items-center gap-2 order-1 sm:order-2 w-full sm:w-auto">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="flex-1 sm:flex-initial"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="flex-1 sm:flex-initial"
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
