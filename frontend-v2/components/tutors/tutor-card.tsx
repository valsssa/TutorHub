'use client';

import Link from 'next/link';
import { Star } from 'lucide-react';
import { Card, CardContent, Avatar, Badge, buttonVariants } from '@/components/ui';
import { FavoriteButton } from '@/components/favorites';
import { cn, formatCurrency } from '@/lib/utils';
import type { TutorProfile } from '@/types';

interface TutorCardProps {
  tutor: TutorProfile;
  showFavorite?: boolean;
}

export function TutorCard({ tutor, showFavorite = true }: TutorCardProps) {
  return (
    <Card hover className="flex flex-col h-full relative">
      <CardContent className="flex flex-col h-full p-0">
        {showFavorite && (
          <div className="absolute top-3 right-3 z-10">
            <FavoriteButton tutorId={tutor.id} size="sm" />
          </div>
        )}
        <div className="p-4 flex items-start gap-3 sm:gap-4">
          <Avatar
            src={tutor.avatar_url}
            name={tutor.display_name}
            size="lg"
            className="shrink-0"
          />
          <div className="flex-1 min-w-0">
            <Link
              href={`/tutors/${tutor.id}`}
              className="text-base sm:text-lg font-semibold text-slate-900 dark:text-white hover:text-primary-600 transition-colors truncate block"
            >
              {tutor.display_name}
            </Link>
            {tutor.headline && (
              <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 mt-1">
                {tutor.headline}
              </p>
            )}
          </div>
        </div>

        <div className="px-4 pb-3 flex items-center gap-2 overflow-hidden">
          <div className="flex items-center gap-1 shrink-0">
            <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
            <span className="text-sm font-medium text-slate-900 dark:text-white">
              {Number(tutor.average_rating || 0).toFixed(1)}
            </span>
          </div>
          <span className="text-slate-400 shrink-0">|</span>
          <span className="text-sm text-slate-500 truncate">
            {tutor.total_reviews ?? 0} {(tutor.total_reviews ?? 0) === 1 ? 'review' : 'reviews'}
          </span>
        </div>

        <div className="px-4 pb-3 flex flex-wrap gap-1.5">
          {tutor.subjects.slice(0, 3).map((subject) => (
            <Badge key={subject.id} variant="default" className="truncate max-w-[120px]">
              {subject.name}
            </Badge>
          ))}
          {tutor.subjects.length > 3 && (
            <Badge variant="default">+{tutor.subjects.length - 3}</Badge>
          )}
        </div>

        <div className="mt-auto px-4 pb-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
          <div className="shrink-0">
            <span className="text-base sm:text-lg font-bold text-slate-900 dark:text-white">
              {formatCurrency(tutor.hourly_rate, tutor.currency)}
            </span>
            <span className="text-xs sm:text-sm text-slate-500">/hr</span>
          </div>
          <Link
            href={`/tutors/${tutor.id}`}
            className={cn(buttonVariants({ variant: 'primary', size: 'sm' }), 'shrink-0')}
          >
            View Profile
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}

export function TutorCardSkeleton() {
  return (
    <Card className="flex flex-col h-full animate-pulse">
      <CardContent className="flex flex-col h-full p-0">
        <div className="p-4 flex items-start gap-4">
          <div className="h-12 w-12 rounded-full bg-slate-200 dark:bg-slate-700" />
          <div className="flex-1 space-y-2">
            <div className="h-5 w-32 bg-slate-200 dark:bg-slate-700 rounded" />
            <div className="h-4 w-48 bg-slate-200 dark:bg-slate-700 rounded" />
          </div>
        </div>
        <div className="px-4 pb-3">
          <div className="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded" />
        </div>
        <div className="px-4 pb-3 flex gap-1.5">
          <div className="h-5 w-16 bg-slate-200 dark:bg-slate-700 rounded-full" />
          <div className="h-5 w-20 bg-slate-200 dark:bg-slate-700 rounded-full" />
        </div>
        <div className="mt-auto px-4 pb-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div className="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded" />
          <div className="h-8 w-24 bg-slate-200 dark:bg-slate-700 rounded-xl" />
        </div>
      </CardContent>
    </Card>
  );
}
