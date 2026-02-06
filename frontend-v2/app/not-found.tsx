import Link from 'next/link';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <div className="rounded-full bg-primary-100 p-6 dark:bg-primary-900/20">
        <FileQuestion className="h-16 w-16 text-primary-500" />
      </div>

      <h1 className="mt-8 text-4xl font-bold text-slate-900 dark:text-white">
        Page not found
      </h1>

      <p className="mt-4 max-w-md text-center text-lg text-slate-600 dark:text-slate-400">
        Sorry, we couldn&apos;t find the page you&apos;re looking for. It might have been
        moved or deleted.
      </p>

      <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
        <Button asChild variant="primary" size="lg">
          <Link href="/">
            <Home className="mr-2 h-5 w-5" />
            Go home
          </Link>
        </Button>

        <Button asChild variant="outline" size="lg">
          <Link href="javascript:history.back()">
            <ArrowLeft className="mr-2 h-5 w-5" />
            Go back
          </Link>
        </Button>
      </div>

      <p className="mt-12 text-sm text-slate-500 dark:text-slate-500">
        Error code: 404
      </p>
    </div>
  );
}
