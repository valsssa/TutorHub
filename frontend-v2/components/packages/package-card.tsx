'use client';

import { Package as PackageIcon, Clock, Percent, AlertCircle } from 'lucide-react';
import { Card, CardContent, Button, Badge } from '@/components/ui';
import { formatCurrency, formatDate } from '@/lib/utils';
import type { Package, PurchasedPackage } from '@/types';

interface PackageCardProps {
  pkg: Package;
  onPurchase?: (pkg: Package) => void;
  isPurchasing?: boolean;
}

export function PackageCard({ pkg, onPurchase, isPurchasing }: PackageCardProps) {
  const originalPrice = pkg.price / (1 - pkg.discount_percent / 100);
  const pricePerSession = pkg.price / pkg.sessions_count;

  return (
    <Card className="h-full flex flex-col">
      <CardContent className="p-6 flex-1 flex flex-col">
        <div className="flex items-start justify-between gap-2 mb-4">
          <div>
            <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
              {pkg.name}
            </h3>
            {pkg.tutor && (
              <p className="text-sm text-slate-500">by {pkg.tutor.display_name}</p>
            )}
          </div>
          {pkg.discount_percent > 0 && (
            <Badge variant="success">
              <Percent className="h-3 w-3 mr-1" />
              {pkg.discount_percent}% off
            </Badge>
          )}
        </div>

        {pkg.description && (
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
            {pkg.description}
          </p>
        )}

        <div className="space-y-3 mb-6 flex-1">
          <div className="flex items-center gap-2 text-sm">
            <PackageIcon className="h-4 w-4 text-slate-400" />
            <span className="text-slate-600 dark:text-slate-400">
              {pkg.sessions_count} sessions
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-slate-400" />
            <span className="text-slate-600 dark:text-slate-400">
              Valid for {pkg.validity_days} days
            </span>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-end justify-between mb-4">
            <div>
              <div className="text-2xl font-bold text-slate-900 dark:text-white">
                {formatCurrency(pkg.price, pkg.currency)}
              </div>
              {pkg.discount_percent > 0 && (
                <div className="text-sm text-slate-500 line-through">
                  {formatCurrency(originalPrice, pkg.currency)}
                </div>
              )}
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-500">
                {formatCurrency(pricePerSession, pkg.currency)}/session
              </div>
            </div>
          </div>

          {onPurchase && (
            <Button
              className="w-full"
              onClick={() => onPurchase(pkg)}
              loading={isPurchasing}
              disabled={isPurchasing}
            >
              Purchase Package
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface PurchasedPackageCardProps {
  purchasedPackage: PurchasedPackage;
  onUse?: (pkg: PurchasedPackage) => void;
}

export function PurchasedPackageCard({
  purchasedPackage,
  onUse,
}: PurchasedPackageCardProps) {
  const pkg = purchasedPackage.package;
  const totalSessions = purchasedPackage.sessions_remaining + purchasedPackage.sessions_used;
  const usagePercent = (purchasedPackage.sessions_used / totalSessions) * 100;

  const expiresAt = new Date(purchasedPackage.expires_at);
  const now = new Date();
  const daysUntilExpiry = Math.ceil(
    (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
  );
  const isExpiringSoon = daysUntilExpiry <= 7 && daysUntilExpiry > 0;
  const isExpired = purchasedPackage.status === 'expired' || daysUntilExpiry <= 0;
  const isExhausted = purchasedPackage.status === 'exhausted';

  const getStatusBadge = () => {
    switch (purchasedPackage.status) {
      case 'active':
        return <Badge variant="success">Active</Badge>;
      case 'expired':
        return <Badge variant="danger">Expired</Badge>;
      case 'exhausted':
        return <Badge variant="default">All sessions used</Badge>;
      case 'cancelled':
        return <Badge variant="warning">Cancelled</Badge>;
      default:
        return null;
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardContent className="p-6 flex-1 flex flex-col">
        <div className="flex items-start justify-between gap-2 mb-4">
          <div>
            <h3 className="font-semibold text-lg text-slate-900 dark:text-white">
              {pkg?.name ?? 'Session Package'}
            </h3>
            {pkg?.tutor && (
              <p className="text-sm text-slate-500">by {pkg.tutor.display_name}</p>
            )}
          </div>
          {getStatusBadge()}
        </div>

        <div className="space-y-4 flex-1">
          <div>
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-600 dark:text-slate-400">Sessions used</span>
              <span className="font-medium text-slate-900 dark:text-white">
                {purchasedPackage.sessions_used} / {totalSessions}
              </span>
            </div>
            <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 rounded-full transition-all"
                style={{ width: `${usagePercent}%` }}
              />
            </div>
          </div>

          <div className="flex items-center gap-2 text-sm">
            <PackageIcon className="h-4 w-4 text-slate-400" />
            <span className="text-slate-600 dark:text-slate-400">
              {purchasedPackage.sessions_remaining} sessions remaining
            </span>
          </div>

          <div className="flex items-center gap-2 text-sm">
            <Clock className="h-4 w-4 text-slate-400" />
            <span
              className={
                isExpired
                  ? 'text-red-600 dark:text-red-400'
                  : isExpiringSoon
                    ? 'text-amber-600 dark:text-amber-400'
                    : 'text-slate-600 dark:text-slate-400'
              }
            >
              {isExpired
                ? 'Expired'
                : `Expires ${formatDate(purchasedPackage.expires_at)}`}
            </span>
          </div>

          {isExpiringSoon && !isExpired && (
            <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              <span className="text-sm text-amber-700 dark:text-amber-400">
                Expires in {daysUntilExpiry} day{daysUntilExpiry === 1 ? '' : 's'}
              </span>
            </div>
          )}
        </div>

        {onUse && purchasedPackage.status === 'active' && (
          <div className="pt-4 mt-4 border-t border-slate-100 dark:border-slate-800">
            <Button className="w-full" onClick={() => onUse(purchasedPackage)}>
              Book a Session
            </Button>
          </div>
        )}

        <div className="pt-4 mt-auto text-xs text-slate-500">
          Purchased {formatDate(purchasedPackage.purchased_at)}
        </div>
      </CardContent>
    </Card>
  );
}
