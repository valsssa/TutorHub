'use client';

import Link from 'next/link';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';
import { Button, Card, CardContent } from '@/components/ui';

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
      <Card className="max-w-md w-full text-center">
        <CardContent>
          <div className="rounded-full bg-primary-100 p-6 dark:bg-primary-900/20 inline-flex mb-6">
            <FileQuestion className="h-16 w-16 text-primary-500" />
          </div>

          <h1 className="text-4xl font-bold text-slate-900 dark:text-white">
            Page not found
          </h1>

          <p className="mt-4 text-lg text-slate-600 dark:text-slate-400">
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

            <Button variant="outline" size="lg" onClick={() => window.history.back()}>
              <ArrowLeft className="mr-2 h-5 w-5" />
              Go back
            </Button>
          </div>

          <p className="mt-12 text-sm text-slate-500 dark:text-slate-500">
            Error code: 404
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
