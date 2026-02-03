export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600">EduStream</h1>
          <p className="text-slate-500 mt-2">Learn from the best tutors</p>
        </div>
        {children}
      </div>
    </div>
  );
}
