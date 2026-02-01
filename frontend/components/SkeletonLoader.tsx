interface SkeletonLoaderProps {
  className?: string;
  variant?: 'text' | 'circle' | 'rectangular';
  width?: string;
  height?: string;
  lines?: number;
}

export default function SkeletonLoader({
  className = '',
  variant = 'rectangular',
  width = '100%',
  height = '20px',
  lines = 1,
}: SkeletonLoaderProps) {
  const baseClass = 'animate-pulse bg-gradient-to-r from-slate-200 dark:from-slate-700 via-slate-300 dark:via-slate-600 to-slate-200 dark:to-slate-700 bg-[length:200%_100%]';
  
  const variantClass = {
    text: 'rounded',
    circle: 'rounded-full',
    rectangular: 'rounded-lg',
  }[variant];

  if (lines > 1) {
    return (
      <div className={`space-y-3 ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`${baseClass} ${variantClass}`}
            style={{
              width: i === lines - 1 ? '80%' : width,
              height,
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${baseClass} ${variantClass} ${className}`}
      style={{ width, height }}
    />
  );
}

export function TutorCardSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-soft border border-slate-100 dark:border-slate-800 p-6 animate-pulse">
      <div className="mb-4">
        <SkeletonLoader height="24px" width="70%" className="mb-2" />
        <SkeletonLoader height="16px" width="90%" lines={2} />
      </div>

      <div className="flex items-center gap-2 mb-4">
        <SkeletonLoader variant="circle" width="20px" height="20px" />
        <SkeletonLoader height="20px" width="100px" />
      </div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-2">
            <SkeletonLoader variant="rectangular" width="40px" height="40px" />
            <div className="flex-1">
              <SkeletonLoader height="12px" width="60%" className="mb-1" />
              <SkeletonLoader height="16px" width="80%" />
            </div>
          </div>
        ))}
      </div>

      <div className="mb-4">
        <SkeletonLoader height="14px" width="80px" className="mb-2" />
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3].map((i) => (
            <SkeletonLoader
              key={i}
              height="28px"
              width="80px"
              className="rounded-full"
            />
          ))}
        </div>
      </div>

      <SkeletonLoader height="40px" width="100%" />
    </div>
  );
}

export function BookingCardSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 animate-pulse">
      <div className="flex items-start gap-4">
        <SkeletonLoader variant="circle" width="48px" height="48px" />
        <div className="flex-1">
          <SkeletonLoader height="18px" width="60%" className="mb-2" />
          <div className="flex items-center gap-3 mb-2">
            <SkeletonLoader height="14px" width="80px" />
            <SkeletonLoader height="14px" width="60px" />
          </div>
          <SkeletonLoader height="24px" width="80px" className="rounded-full" />
        </div>
        <SkeletonLoader height="36px" width="100px" className="rounded-lg" />
      </div>
    </div>
  );
}

export function BookingListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <BookingCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function MessageThreadSkeleton() {
  return (
    <div className="flex items-start gap-3 p-4 animate-pulse">
      <SkeletonLoader variant="circle" width="40px" height="40px" />
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-baseline mb-1">
          <SkeletonLoader height="16px" width="120px" />
          <SkeletonLoader height="12px" width="40px" />
        </div>
        <SkeletonLoader height="14px" width="80%" />
      </div>
    </div>
  );
}

export function MessageListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-800">
      {Array.from({ length: count }).map((_, i) => (
        <MessageThreadSkeleton key={i} />
      ))}
    </div>
  );
}

export function DashboardStatsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
      {[1, 2, 3, 4].map((i) => (
        <div
          key={i}
          className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4"
        >
          <SkeletonLoader height="14px" width="60%" className="mb-2" />
          <SkeletonLoader height="28px" width="50%" className="mb-1" />
          <SkeletonLoader height="12px" width="80%" />
        </div>
      ))}
    </div>
  );
}

export function NotificationSkeleton() {
  return (
    <div className="flex items-start gap-4 p-4 animate-pulse">
      <SkeletonLoader variant="circle" width="40px" height="40px" />
      <div className="flex-1">
        <div className="flex justify-between items-start mb-1">
          <SkeletonLoader height="16px" width="70%" />
          <SkeletonLoader height="12px" width="50px" />
        </div>
        <SkeletonLoader height="14px" width="90%" />
      </div>
    </div>
  );
}

export function NotificationListSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-800">
      {Array.from({ length: count }).map((_, i) => (
        <NotificationSkeleton key={i} />
      ))}
    </div>
  );
}

export function CalendarSkeleton() {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 animate-pulse">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <SkeletonLoader height="24px" width="150px" />
        <div className="flex gap-2">
          <SkeletonLoader height="32px" width="32px" className="rounded" />
          <SkeletonLoader height="32px" width="32px" className="rounded" />
        </div>
      </div>
      {/* Days header */}
      <div className="grid grid-cols-7 gap-2 mb-2">
        {[1, 2, 3, 4, 5, 6, 7].map((i) => (
          <SkeletonLoader key={i} height="14px" width="30px" className="mx-auto" />
        ))}
      </div>
      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-2">
        {Array.from({ length: 35 }).map((_, i) => (
          <SkeletonLoader key={i} height="40px" width="100%" className="rounded" />
        ))}
      </div>
    </div>
  );
}

export function TutorProfileSkeleton() {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-24 md:pb-8">
      {/* Breadcrumb */}
      <div className="container mx-auto px-4 py-6 max-w-7xl">
        <SkeletonLoader height="20px" width="180px" />
      </div>

      <div className="container mx-auto px-4 max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column */}
        <div className="lg:col-span-8 space-y-8">
          {/* Hero Header */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-6 sm:p-8 border border-slate-200 dark:border-slate-800">
            <div className="flex flex-col sm:flex-row gap-6 items-start">
              <SkeletonLoader variant="rectangular" width="128px" height="128px" className="rounded-2xl" />
              <div className="flex-1">
                <SkeletonLoader height="32px" width="60%" className="mb-2" />
                <SkeletonLoader height="20px" width="80%" className="mb-4" />
                <div className="flex flex-wrap gap-4 sm:gap-8 pt-4 border-t border-slate-100 dark:border-slate-800">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex items-center gap-2">
                      <SkeletonLoader variant="circle" width="36px" height="36px" />
                      <div>
                        <SkeletonLoader height="18px" width="40px" className="mb-1" />
                        <SkeletonLoader height="12px" width="50px" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Video Placeholder */}
          <div className="bg-slate-900 dark:bg-slate-800 rounded-3xl overflow-hidden aspect-video">
            <SkeletonLoader height="100%" width="100%" className="h-full" />
          </div>

          {/* About Section */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800">
            <SkeletonLoader height="28px" width="120px" className="mb-4" />
            <SkeletonLoader height="16px" lines={5} />
          </div>

          {/* Subjects Section */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800">
            <SkeletonLoader height="28px" width="100px" className="mb-4" />
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3, 4].map((i) => (
                <SkeletonLoader key={i} height="36px" width="100px" className="rounded-lg" />
              ))}
            </div>
          </div>

          {/* Schedule Section */}
          <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800">
            <SkeletonLoader height="32px" width="120px" className="mb-6" />
            <div className="grid grid-cols-7 gap-2">
              {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                <div key={i} className="flex flex-col items-center gap-2">
                  <SkeletonLoader height="14px" width="30px" className="mb-1" />
                  <SkeletonLoader height="20px" width="24px" />
                  <div className="mt-3 space-y-2">
                    {[1, 2, 3].map((j) => (
                      <SkeletonLoader key={j} height="20px" width="40px" />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Sidebar */}
        <div className="lg:col-span-4">
          <div className="sticky top-24">
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xl">
              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-4 mb-6 pb-6 border-b border-slate-100 dark:border-slate-800">
                {[1, 2, 3].map((i) => (
                  <div key={i}>
                    <SkeletonLoader height="24px" width="50px" className="mb-1" />
                    <SkeletonLoader height="14px" width="60px" />
                  </div>
                ))}
              </div>

              {/* CTA Buttons */}
              <div className="space-y-3">
                <SkeletonLoader height="48px" width="100%" className="rounded-lg" />
                <SkeletonLoader height="48px" width="100%" className="rounded-lg" />
                <SkeletonLoader height="48px" width="100%" className="rounded-lg" />
              </div>

              {/* Promo Box */}
              <div className="mt-6">
                <SkeletonLoader height="80px" width="100%" className="rounded-xl" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
