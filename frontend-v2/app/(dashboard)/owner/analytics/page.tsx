import { Construction } from 'lucide-react';
import { Card, CardContent } from '@/components/ui';

export default function OwnerAnalyticsPage() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Card className="max-w-md w-full">
        <CardContent className="flex flex-col items-center text-center py-12 px-6">
          <div className="p-4 rounded-full bg-amber-100 dark:bg-amber-900/30 mb-6">
            <Construction className="h-10 w-10 text-amber-600 dark:text-amber-400" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Analytics
          </h1>
          <p className="text-lg font-medium text-slate-500 mt-2">
            Coming Soon
          </p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-3">
            This feature is currently under development.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
