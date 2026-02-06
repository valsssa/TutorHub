'use client';

import { Heart, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToggleFavorite } from '@/lib/hooks';

interface FavoriteButtonProps {
  tutorId: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
};

const iconSizes = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
};

export function FavoriteButton({ tutorId, className, size = 'md' }: FavoriteButtonProps) {
  const { isFavorite, isLoading, toggle } = useToggleFavorite(tutorId);

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggle();
      }}
      disabled={isLoading}
      className={cn(
        'inline-flex items-center justify-center rounded-full',
        'bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm',
        'shadow-md hover:shadow-lg transition-all duration-200',
        'hover:scale-105 active:scale-95',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100',
        'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
        sizeClasses[size],
        className
      )}
      aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
      aria-pressed={isFavorite}
    >
      {isLoading ? (
        <Loader2 className={cn(iconSizes[size], 'animate-spin text-slate-400')} />
      ) : (
        <Heart
          className={cn(
            iconSizes[size],
            'transition-colors duration-200',
            isFavorite
              ? 'fill-red-500 text-red-500'
              : 'text-slate-400 hover:text-red-400'
          )}
        />
      )}
    </button>
  );
}
