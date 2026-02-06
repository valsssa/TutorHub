'use client';

import * as React from 'react';
import { Card } from '@/components/ui/card';
import { Avatar } from '@/components/ui/avatar';
import { StarRating } from './star-rating';
import { formatRelativeTime } from '@/lib/utils';
import type { Review } from '@/types/review';

interface ReviewCardProps {
  review: Review;
  className?: string;
}

export function ReviewCard({ review, className }: ReviewCardProps) {
  return (
    <Card className={className}>
      <div className="flex items-start gap-4">
        <Avatar name="Student" size="md" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="font-medium text-slate-900 dark:text-white truncate">
              Student
            </span>
            <span className="text-sm text-slate-500 dark:text-slate-400 shrink-0">
              {formatRelativeTime(review.created_at)}
            </span>
          </div>
          <StarRating value={review.rating} readonly size="sm" className="mb-2" />
          {review.comment && (
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
              {review.comment}
            </p>
          )}
        </div>
      </div>
    </Card>
  );
}
