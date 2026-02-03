'use client';

import { use, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Package, AlertCircle, Check } from 'lucide-react';
import { useTutor, useTutorPackages, usePurchasePackage } from '@/lib/hooks';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Avatar,
  Skeleton,
} from '@/components/ui';
import { PackageCard } from '@/components/packages/package-card';
import type { Package as PackageType } from '@/types';

interface TutorPackagesPageProps {
  params: Promise<{ id: string }>;
}

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
            <div className="space-y-3 mb-6">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-4 w-32" />
            </div>
            <div className="pt-4 border-t border-slate-100">
              <div className="flex justify-between items-end mb-4">
                <div className="space-y-1">
                  <Skeleton className="h-8 w-24" />
                  <Skeleton className="h-4 w-16" />
                </div>
                <Skeleton className="h-4 w-20" />
              </div>
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function TutorPackagesPage({ params }: TutorPackagesPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const tutorId = parseInt(id, 10);

  const [purchasingId, setPurchasingId] = useState<number | null>(null);
  const [purchaseSuccess, setPurchaseSuccess] = useState<number | null>(null);

  const { data: tutor, isLoading: tutorLoading } = useTutor(tutorId);
  const { data: packagesData, isLoading: packagesLoading } = useTutorPackages(tutorId);
  const purchaseMutation = usePurchasePackage();

  const handlePurchase = async (pkg: PackageType) => {
    setPurchasingId(pkg.id);
    try {
      await purchaseMutation.mutateAsync({ package_id: pkg.id });
      setPurchaseSuccess(pkg.id);
      setTimeout(() => {
        router.push('/packages');
      }, 2000);
    } catch {
      // Error is handled by mutation
    } finally {
      setPurchasingId(null);
    }
  };

  const isLoading = tutorLoading || packagesLoading;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10 rounded-xl" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <PackagesSkeleton />
      </div>
    );
  }

  if (!tutor) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Card>
          <CardContent className="py-12 text-center">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
              Tutor not found
            </h3>
            <p className="text-slate-500 mb-4">
              The tutor you are looking for does not exist or has been removed.
            </p>
            <Button asChild>
              <Link href="/tutors">Browse Tutors</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex items-center gap-3">
          <Avatar src={tutor.avatar_url} name={tutor.display_name} size="md" />
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">
              Session Packages
            </h1>
            <p className="text-sm text-slate-500">by {tutor.display_name}</p>
          </div>
        </div>
      </div>

      {purchaseSuccess && (
        <Card className="border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center">
                <Check className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 className="font-medium text-green-800 dark:text-green-200">
                  Purchase Successful!
                </h3>
                <p className="text-sm text-green-700 dark:text-green-300">
                  Redirecting to your packages...
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {purchaseMutation.isError && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
              <div>
                <h3 className="font-medium text-red-800 dark:text-red-200">
                  Purchase Failed
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  There was an error processing your purchase. Please try again.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Available Packages
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!packagesData?.items.length ? (
            <div className="py-12 text-center">
              <Package className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                No packages available
              </h3>
              <p className="text-slate-500 mb-4">
                This tutor does not have any session packages available at the moment.
              </p>
              <Button asChild variant="outline">
                <Link href={`/tutors/${tutorId}`}>View Tutor Profile</Link>
              </Button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {packagesData.items.map((pkg) => (
                <PackageCard
                  key={pkg.id}
                  pkg={pkg}
                  onPurchase={purchaseSuccess ? undefined : handlePurchase}
                  isPurchasing={purchasingId === pkg.id}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-center gap-4">
        <Button asChild variant="outline">
          <Link href={`/tutors/${tutorId}`}>View Profile</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href={`/bookings/new?tutor_id=${tutorId}`}>Book Single Session</Link>
        </Button>
      </div>
    </div>
  );
}
