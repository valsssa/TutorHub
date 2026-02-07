import Link from 'next/link';
import { ThemeToggle } from '@/components/ui';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-3 py-6 sm:p-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-primary-600">
            <Link href="/" className="hover:opacity-80 transition-opacity">
              EduStream
            </Link>
          </h1>
          <p className="text-sm sm:text-base text-slate-500 mt-1.5 sm:mt-2">Learn from the best tutors</p>
        </div>
        {children}
      </div>
    </div>
  );
}
