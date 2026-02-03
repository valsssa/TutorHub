'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Package, Search, Filter, AlertCircle } from 'lucide-react';
import { useMyPackages } from '@/lib/hooks';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Badge,
  Skeleton,
} from '@/components/ui';
import { PurchasedPackageCard } from '@/components/packages/package-card';
import type { PurchasedPackageStatus, PurchasedPackage } from '@/types';

const STATUS_OPTIONS: { value: PurchasedPackageStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All Packages' },
  { value: 'active', label: 'Active' },
  { value: 'expired', label: 'Expired' },
  { value: 'exhausted', label: 'Used Up' },
];

function PackagesSkeleton() {
  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-24" />
              </div>
              <Skeleton className="h-6 w-16 rounded-full" />
            </div>
            <div className="space-y-4">
              <div>
                <Skeleton className="h-2 w-full rounded-full" />
              </div>
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-32" />
            </div>
            <Skeleton className="h-10 w-full mt-4" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function MyPackagesPage() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState<PurchasedPackageStatus | 'all'>('all');

  const filters = statusFilter === 'all' ? {} : { status: statusFilter };
  const { data, isLoading, error } = useMyPackages(filters);

  const handleUsePackage = (pkg: PurchasedPackage) => {
    router.push(`/bookings/new?package_id=${pkg.id}`);
  };

  const activePackages = data?.items.filter((pkg) => pkg.status === 'active') ?? [];
  const expiringSoonPackages = activePackages.filter((pkg) => {
    const expiresAt = new Date(pkg.expires_at);
    const now = new Date();
    const daysUntilExpiry = Math.ceil(
      (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
    );
    return daysUntilExpiry <= 7 && daysUntilExpiry > 0;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            My Packages
          </h1>
          <p className="text-slate-500 mt-1">
            Manage your purchased session packages
          </p>
        </div>
        <Button asChild>
          <Link href="/tutors">
            <Search className="h-4 w-4 mr-2" />
            Find Tutors
          </Link>
        </Button>
      </div>

      {expiringSoonPackages.length > 0 && (
        <Card className="border-amber-200 bg-amber-50 dark:bg-amber-900/20 dark:border-amber-800">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5" />
              <div>
                <h3 className="font-medium text-amber-800 dark:text-amber-200">
                  Packages Expiring Soon
                </h3>
                <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                  You have {expiringSoonPackages.length} package
                  {expiringSoonPackages.length === 1 ? '' : 's'} expiring within the next
                  7 days. Use them before they expire!
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Session Packages
            </CardTitle>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  size="sm"
                  variant={statusFilter === option.value ? 'primary' : 'ghost'}
                  onClick={() => setStatusFilter(option.value)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <PackagesSkeleton />
          ) : error ? (
            <div className="py-12 text-center">
              <AlertCircle className="h-12 w-12 text-red-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                Failed to load packages
              </h3>
              <p className="text-slate-500 mb-4">
                There was an error loading your packages. Please try again.
              </p>
              <Button onClick={() => window.location.reload()}>Retry</Button>
            </div>
          ) : !data?.items.length ? (
            <div className="py-12 text-center">
              <Package className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                No packages yet
              </h3>
              <p className="text-slate-500 mb-4">
                You have not purchased any session packages yet. Browse tutors to find
                available packages.
              </p>
              <Button asChild>
                <Link href="/tutors">Browse Tutors</Link>
              </Button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.items.map((purchasedPackage) => (
                <PurchasedPackageCard
                  key={purchasedPackage.id}
                  purchasedPackage={purchasedPackage}
                  onUse={handleUsePackage}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {data && data.total > data.page_size && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={data.page === 1}
            onClick={() => {
              // TODO: Implement pagination
            }}
          >
            Previous
          </Button>
          <span className="text-sm text-slate-500">
            Page {data.page} of {data.total_pages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={data.page === data.total_pages}
            onClick={() => {
              // TODO: Implement pagination
            }}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
