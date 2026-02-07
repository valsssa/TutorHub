'use client';

import * as React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/button';
import { StarRating } from './star-rating';
import { createReviewSchema, type CreateReviewFormData } from '@/lib/validators/review';
import { cn } from '@/lib/utils';

interface ReviewFormProps {
  onSubmit: (data: CreateReviewFormData) => void;
  isLoading?: boolean;
  className?: string;
}

export function ReviewForm({ onSubmit, isLoading, className }: ReviewFormProps) {
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateReviewFormData>({
    resolver: zodResolver(createReviewSchema),
    defaultValues: {
      rating: 0,
      comment: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={cn('space-y-4', className)}>
      <div>
        <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-2">
          Rating
        </label>
        <Controller
          control={control}
          name="rating"
          render={({ field }) => (
            <div className={cn(
              'inline-block rounded-lg p-1 -m-1 transition-colors',
              errors.rating && 'ring-2 ring-red-500/40 bg-red-50 dark:bg-red-900/10'
            )}>
              <StarRating
                value={field.value}
                onChange={field.onChange}
                size="lg"
              />
            </div>
          )}
        />
        {errors.rating && (
          <p className="mt-1 text-sm text-red-500" role="alert">{errors.rating.message}</p>
        )}
      </div>

      <div>
        <label
          htmlFor="comment"
          className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-2"
        >
          Comment (optional)
        </label>
        <textarea
          id="comment"
          {...register('comment')}
          rows={4}
          placeholder="Share your experience with this tutor..."
          className={cn(
            'w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 sm:px-4 sm:py-3',
            'text-sm sm:text-base text-slate-900 placeholder:text-slate-400',
            'focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20',
            'dark:border-slate-700 dark:bg-slate-800 dark:text-white',
            'resize-y transition-colors',
            errors.comment && 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
          )}
        />
        {errors.comment && (
          <p className="mt-1 text-sm text-red-500">{errors.comment.message}</p>
        )}
      </div>

      <Button type="submit" loading={isLoading} className="w-full">
        Submit Review
      </Button>
    </form>
  );
}
