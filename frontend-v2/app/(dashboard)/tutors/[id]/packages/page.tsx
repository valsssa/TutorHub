'use client';

import { use, useState, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Package, AlertCircle, Check, Clock } from 'lucide-react';
import { useTutor, usePurchasePackage } from '@/lib/hooks';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Avatar,
  Skeleton,
} from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import type { PricingOption } from '@/types';

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

// Component to display a pricing option card
interface PricingOptionCardProps {
  option: PricingOption;
  currency: string;
  onPurchase?: (option: PricingOption) => void;
  isPurchasing?: boolean;
}

function PricingOptionCard({ option, currency, onPurchase, isPurchasing }: PricingOptionCardProps) {
  return (
    <Card className="h-full flex flex-col">
      <CardContent className="p-6 flex-1 flex flex-col">
        <div className="flex items-start justify-between gap-2 mb-4">
          <div>
            <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
              {option.title}
            </h3>
            <p className="text-sm text-slate-500">
              {option.duration_minutes} minute session
            </p>
          </div>
        </div>

        {option.description && (
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            {option.description}
          </p>
        )}

        <div className="space-y-3 mb-6 flex-1">
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-slate-400" />
            <span className="text-slate-600 dark:text-slate-400">
              {option.duration_minutes} minutes per session
            </span>
          </div>
          {option.validity_days && (
            <div className="flex items-center gap-2 text-sm">
              <Package className="h-4 w-4 text-slate-400" />
              <span className="text-slate-600 dark:text-slate-400">
                Valid for {option.validity_days} days after purchase
              </span>
            </div>
          )}
          {option.extend_on_use && (
            <div className="flex items-center gap-2 text-sm">
              <Check className="h-4 w-4 text-green-500" />
              <span className="text-green-600 dark:text-green-400">
                Validity extends on each use
              </span>
            </div>
          )}
        </div>

        <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-end justify-between mb-4">
            <div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                {formatCurrency(option.price, currency)}
              </div>
              <div className="text-sm text-slate-500">per session</div>
            </div>
          </div>

          {onPurchase && (
            <Button
              className="w-full"
              onClick={() => onPurchase(option)}
              loading={isPurchasing}
              disabled={isPurchasing}
            >
              Purchase Session
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default function TutorPackagesPage({ params }: TutorPackagesPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const tutorId = parseInt(id, 10);

  const [purchasingId, setPurchasingId] = useState<number | null>(null);
  const [purchaseSuccess, setPurchaseSuccess] = useState<number | null>(null);

  const { data: tutor, isLoading: tutorLoading } = useTutor(tutorId);
  const purchaseMutation = usePurchasePackage();

  // Extract pricing options from tutor profile
  const pricingOptions = useMemo(() => {
    return tutor?.pricing_options ?? [];
  }, [tutor]);

  const currency = tutor?.currency ?? 'USD';
  const tutorDisplayName = tutor?.display_name ?? tutor?.name ?? 'Tutor';

  const handlePurchase = async (option: PricingOption) => {
    setPurchasingId(option.id);
    try {
      await purchaseMutation.mutateAsync({
        tutor_profile_id: tutorId,
        pricing_option_id: option.id,
      });
      setPurchaseSuccess(option.id);
      setTimeout(() => {
        router.push('/packages');
      }, 2000);
    } catch {
      // Error is handled by mutation
    } finally {
      setPurchasingId(null);
    }
  };

  const isLoading = tutorLoading;

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
          <Avatar src={tutor.avatar_url ?? tutor.profile_photo_url} name={tutorDisplayName} size="md" />
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">
              Session Packages
            </h1>
            <p className="text-sm text-slate-500">by {tutorDisplayName}</p>
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
            Available Session Options
          </CardTitle>
        </CardHeader>
        <CardContent>
          {pricingOptions.length === 0 ? (
            <div className="py-12 text-center">
              <Package className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
                No session options available
              </h3>
              <p className="text-slate-500 mb-4">
                This tutor has not set up any session packages yet. You can still book individual sessions at their hourly rate.
              </p>
              <Button asChild variant="outline">
                <Link href={`/tutors/${tutorId}`}>View Tutor Profile</Link>
              </Button>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pricingOptions.map((option: PricingOption) => (
                <PricingOptionCard
                  key={option.id}
                  option={option}
                  currency={currency}
                  onPurchase={purchaseSuccess ? undefined : handlePurchase}
                  isPurchasing={purchasingId === option.id}
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
