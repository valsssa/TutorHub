'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Wallet,
  Filter,
  ChevronLeft,
  ChevronRight,
  X,
  RefreshCw,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Input,
  Skeleton,
} from '@/components/ui';
import { TransactionItem } from '@/components/wallet';
import { useTransactions } from '@/lib/hooks';
import type { TransactionFilters, TransactionType, TransactionStatus } from '@/types/wallet';

type FilterType = TransactionType | 'all';
type FilterStatus = TransactionStatus | 'all';

const typeOptions: { value: FilterType; label: string }[] = [
  { value: 'all', label: 'All Types' },
  { value: 'deposit', label: 'Deposits' },
  { value: 'withdrawal', label: 'Withdrawals' },
  { value: 'payment', label: 'Payments' },
  { value: 'refund', label: 'Refunds' },
  { value: 'payout', label: 'Payouts' },
  { value: 'fee', label: 'Fees' },
  { value: 'transfer', label: 'Transfers' },
];

const statusOptions: { value: FilterStatus; label: string }[] = [
  { value: 'all', label: 'All Statuses' },
  { value: 'completed', label: 'Completed' },
  { value: 'pending', label: 'Pending' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const PAGE_SIZE = 20;

export default function TransactionsPage() {
  const [typeFilter, setTypeFilter] = useState<FilterType>('all');
  const [statusFilter, setStatusFilter] = useState<FilterStatus>('all');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [page, setPage] = useState(1);

  // Build filters object for API
  const filters: TransactionFilters = useMemo(() => {
    const f: TransactionFilters = {
      page,
      page_size: PAGE_SIZE,
    };

    if (typeFilter !== 'all') {
      // Backend expects uppercase type
      f.type = typeFilter.toUpperCase();
    }

    if (statusFilter !== 'all') {
      f.status = statusFilter.toUpperCase();
    }

    if (fromDate) {
      f.from_date = fromDate;
    }

    if (toDate) {
      f.to_date = toDate;
    }

    return f;
  }, [typeFilter, statusFilter, fromDate, toDate, page]);

  const { data, isLoading, error, refetch, isRefetching } = useTransactions(filters);

  const transactions = data?.items ?? [];
  const totalPages = data?.total_pages ?? 0;
  const totalCount = data?.total ?? 0;

  const hasActiveFilters = typeFilter !== 'all' || statusFilter !== 'all' || fromDate || toDate;

  const clearFilters = () => {
    setTypeFilter('all');
    setStatusFilter('all');
    setFromDate('');
    setToDate('');
    setPage(1);
  };

  // Reset to page 1 when filters change
  const handleFilterChange = <T,>(setter: (value: T) => void) => (value: T) => {
    setter(value);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="icon">
          <Link href="/wallet">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Transaction History
          </h1>
          <p className="text-slate-500">
            {totalCount > 0
              ? `${totalCount} transaction${totalCount !== 1 ? 's' : ''} found`
              : 'View all your wallet transactions'}
          </p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={() => refetch()}
          disabled={isRefetching}
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <span className="font-medium text-slate-900 dark:text-white">Filters</span>
            </div>
            {hasActiveFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearFilters}
                className="text-slate-500 hover:text-slate-700"
              >
                <X className="h-4 w-4 mr-1" />
                Clear
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Type Filter */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Type
              </label>
              <select
                value={typeFilter}
                onChange={(e) =>
                  handleFilterChange(setTypeFilter)(e.target.value as FilterType)
                }
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {typeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) =>
                  handleFilterChange(setStatusFilter)(e.target.value as FilterStatus)
                }
                className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {statusOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {/* From Date */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                From Date
              </label>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => handleFilterChange(setFromDate)(e.target.value)}
                className="w-full"
              />
            </div>

            {/* To Date */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
                To Date
              </label>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => handleFilterChange(setToDate)(e.target.value)}
                className="w-full"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transactions List */}
      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-red-50 dark:bg-red-900/20 mb-3">
                <Wallet className="h-6 w-6 text-red-500" />
              </div>
              <p className="text-red-600 dark:text-red-400 font-medium mb-2">
                Failed to load transactions
              </p>
              <p className="text-sm text-slate-500 mb-4">
                {error instanceof Error ? error.message : 'An error occurred'}
              </p>
              <Button variant="outline" onClick={() => refetch()}>
                Try Again
              </Button>
            </div>
          ) : isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50"
                >
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                  <div className="text-right space-y-2">
                    <Skeleton className="h-4 w-16 ml-auto" />
                    <Skeleton className="h-3 w-12 ml-auto" />
                  </div>
                </div>
              ))}
            </div>
          ) : transactions.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-slate-100 dark:bg-slate-800 mb-3">
                <Wallet className="h-6 w-6 text-slate-400" />
              </div>
              <p className="text-slate-600 dark:text-slate-400 font-medium mb-2">
                No transactions found
              </p>
              <p className="text-sm text-slate-500 mb-4">
                {hasActiveFilters
                  ? 'Try adjusting your filters to see more results'
                  : 'Your transaction history will appear here'}
              </p>
              {hasActiveFilters && (
                <Button variant="outline" onClick={clearFilters}>
                  Clear Filters
                </Button>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {transactions.map((transaction) => (
                <TransactionItem
                  key={transaction.id}
                  transaction={transaction}
                  showDetails
                />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
              <p className="text-sm text-slate-500">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1 || isLoading}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || isLoading}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
