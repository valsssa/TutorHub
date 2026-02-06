'use client';

import Link from 'next/link';
import { Heart, Search } from 'lucide-react';
import { Card, CardContent, Button } from '@/components/ui';
import { TutorCard, TutorCardSkeleton } from '@/components/tutors/tutor-card';
import { useFavorites, useRemoveFavorite } from '@/lib/hooks';

export default function FavoritesPage() {
  const { data: favorites, isLoading, error } = useFavorites();
  const removeFavorite = useRemoveFavorite();

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
              onClick={() => window.location.reload()}
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!favorites || favorites.length === 0) {
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
            {favorites.length} {favorites.length === 1 ? 'tutor' : 'tutors'} saved
          </p>
        </div>
        <Button asChild variant="outline">
          <Link href="/tutors">
            <Search className="mr-2 h-4 w-4" />
            Find More Tutors
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
        {favorites.map((favorite) => (
          <div key={favorite.id} className="relative overflow-hidden">
            {favorite.tutor && (
              <TutorCard tutor={favorite.tutor} showFavorite={false} />
            )}
            <button
              onClick={() => removeFavorite.mutate(favorite.tutor_profile_id)}
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
          </div>
        ))}
      </div>
    </div>
  );
}
