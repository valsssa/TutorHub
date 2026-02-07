import { Loader2, GraduationCap } from 'lucide-react';

export default function Loading() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 dark:bg-slate-950">
      <div className="flex items-center gap-2 mb-6">
        <GraduationCap className="h-8 w-8 text-primary-600" />
        <span className="text-xl font-bold text-slate-900 dark:text-white">
          EduStream
        </span>
      </div>
      <Loader2 className="h-12 w-12 animate-spin text-primary-500" />
      <p className="mt-4 text-slate-600 dark:text-slate-400">Loading...</p>
    </div>
  );
}
