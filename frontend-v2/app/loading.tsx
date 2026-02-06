import { Loader2 } from 'lucide-react';

export default function Loading() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 dark:bg-slate-950">
      <Loader2 className="h-12 w-12 animate-spin text-primary-500" />
      <p className="mt-4 text-slate-600 dark:text-slate-400">Loading...</p>
    </div>
  );
}
