'use client';

import Link from 'next/link';
import { Star } from 'lucide-react';
import { Card, CardContent, Avatar, Badge, Button } from '@/components/ui';
import { FavoriteButton } from '@/components/favorites';
import { formatCurrency } from '@/lib/utils';
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
        <div className="p-4 flex items-start gap-4">
          <Avatar
            src={tutor.avatar_url}
            name={tutor.display_name}
            size="lg"
          />
          <div className="flex-1 min-w-0">
            <Link
              href={`/tutors/${tutor.id}`}
              className="text-lg font-semibold text-slate-900 dark:text-white hover:text-primary-600 transition-colors line-clamp-1"
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

        <div className="px-4 pb-3 flex items-center gap-2">
          <div className="flex items-center gap-1">
            <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
            <span className="text-sm font-medium text-slate-900 dark:text-white">
              {tutor.average_rating.toFixed(1)}
            </span>
          </div>
          <span className="text-slate-400">|</span>
          <span className="text-sm text-slate-500">
            {tutor.review_count} {tutor.review_count === 1 ? 'review' : 'reviews'}
          </span>
        </div>

        <div className="px-4 pb-3 flex flex-wrap gap-1.5">
          {tutor.subjects.slice(0, 3).map((subject) => (
            <Badge key={subject.id} variant="default">
              {subject.name}
            </Badge>
          ))}
          {tutor.subjects.length > 3 && (
            <Badge variant="default">+{tutor.subjects.length - 3}</Badge>
          )}
        </div>

        <div className="mt-auto px-4 pb-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-lg font-bold text-slate-900 dark:text-white">
              {formatCurrency(tutor.hourly_rate, tutor.currency)}
            </span>
            <span className="text-sm text-slate-500">/hr</span>
          </div>
          <Button asChild size="sm">
            <Link href={`/tutors/${tutor.id}`}>View Profile</Link>
          </Button>
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
