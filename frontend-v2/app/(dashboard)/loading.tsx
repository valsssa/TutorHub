import { GraduationCap } from 'lucide-react';
import { Skeleton, SkeletonCard } from '@/components/ui';

export default function DashboardLoading() {
  return (
    <div className="space-y-4 sm:space-y-6 p-3 sm:p-6">
      {/* Branding */}
      <div className="flex items-center justify-center gap-2 py-4">
        <GraduationCap className="h-6 w-6 text-primary-600 animate-pulse" />
        <span className="text-lg font-bold text-slate-900 dark:text-white">EduStream</span>
      </div>

      {/* Page header skeleton */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-0">
        <div className="space-y-2">
          <Skeleton className="h-7 sm:h-8 w-36 sm:w-48" />
          <Skeleton className="h-4 w-48 sm:w-64" />
        </div>
        <Skeleton className="h-10 w-full sm:w-32" />
      </div>

      {/* Stats row skeleton */}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl sm:rounded-2xl bg-white p-4 sm:p-6 shadow-soft dark:bg-slate-900"
          >
            <div className="flex items-center justify-between">
              <Skeleton className="h-8 w-8 sm:h-10 sm:w-10 rounded-lg" />
              <Skeleton className="h-4 w-12 sm:w-16" />
            </div>
            <div className="mt-3 sm:mt-4 space-y-2">
              <Skeleton className="h-6 sm:h-8 w-16 sm:w-20" />
              <Skeleton className="h-3 w-20 sm:w-32" />
            </div>
          </div>
        ))}
      </div>

      {/* Content cards skeleton */}
      <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-2">
        <SkeletonCard />
        <SkeletonCard />
      </div>

      {/* Table/list skeleton */}
      <div className="rounded-xl sm:rounded-2xl bg-white p-4 sm:p-6 shadow-soft dark:bg-slate-900">
        <Skeleton className="mb-4 h-6 w-40" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 sm:gap-4">
              <Skeleton className="h-8 w-8 sm:h-10 sm:w-10 rounded-full shrink-0" />
              <div className="flex-1 space-y-2 min-w-0">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-3 w-1/2" />
              </div>
              <Skeleton className="h-8 w-16 sm:w-20 shrink-0" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
