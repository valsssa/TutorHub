'use client';

import * as React from 'react';
import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  readonly?: boolean;
  size?: 'sm' | 'md' | 'lg';
  showValue?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: 'h-5 w-5 sm:h-4 sm:w-4',
  md: 'h-6 w-6 sm:h-5 sm:w-5',
  lg: 'h-8 w-8 sm:h-6 sm:w-6',
};

const gapClasses = {
  sm: 'gap-1 sm:gap-0.5',
  md: 'gap-1.5 sm:gap-1',
  lg: 'gap-2 sm:gap-1.5',
};

export function StarRating({
  value,
  onChange,
  readonly = false,
  size = 'md',
  showValue = false,
  className,
}: StarRatingProps) {
  const [hoverValue, setHoverValue] = React.useState<number | null>(null);

  const displayValue = hoverValue ?? value;
  const isInteractive = !readonly && onChange;

  const handleClick = (starValue: number) => {
    if (isInteractive) {
      onChange(starValue);
    }
  };

  const handleMouseEnter = (starValue: number) => {
    if (isInteractive) {
      setHoverValue(starValue);
    }
  };

  const handleMouseLeave = () => {
    if (isInteractive) {
      setHoverValue(null);
    }
  };

  const renderStar = (starIndex: number) => {
    const starValue = starIndex + 1;
    const filled = displayValue >= starValue;
    const halfFilled = !filled && displayValue >= starValue - 0.5;

    return (
      <button
        key={starIndex}
        type="button"
        onClick={() => handleClick(starValue)}
        onMouseEnter={() => handleMouseEnter(starValue)}
        onMouseLeave={handleMouseLeave}
        disabled={readonly}
        className={cn(
          'relative focus:outline-none p-1 -m-1 sm:p-0 sm:m-0',
          isInteractive && 'cursor-pointer transition-transform hover:scale-110 active:scale-95',
          readonly && 'cursor-default'
        )}
        aria-label={`${starValue} star${starValue !== 1 ? 's' : ''}`}
      >
        <Star
          className={cn(
            sizeClasses[size],
            'transition-colors',
            filled
              ? 'fill-amber-400 text-amber-400'
              : 'fill-transparent text-slate-300 dark:text-slate-600'
          )}
        />
        {halfFilled && (
          <Star
            className={cn(
              sizeClasses[size],
              'absolute inset-0 fill-amber-400 text-amber-400'
            )}
            style={{ clipPath: 'inset(0 50% 0 0)' }}
          />
        )}
      </button>
    );
  };

  return (
    <div className={cn('flex items-center', gapClasses[size], className)}>
      <div
        className={cn('flex', gapClasses[size])}
        role={isInteractive ? 'radiogroup' : 'img'}
        aria-label={`Rating: ${value} out of 5 stars`}
      >
        {[0, 1, 2, 3, 4].map(renderStar)}
      </div>
      {showValue && (
        <span className="ml-2 text-sm font-medium text-slate-600 dark:text-slate-400">
          {Number(value || 0).toFixed(1)}
        </span>
      )}
    </div>
  );
}
