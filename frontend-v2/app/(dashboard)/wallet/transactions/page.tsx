'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Filter, Wallet } from 'lucide-react';
import { useTransactions } from '@/lib/hooks/use-wallet';
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
import type { TransactionType, TransactionFilters } from '@/types/wallet';

const transactionTypes: { value: TransactionType | ''; label: string }[] = [
  { value: '', label: 'All Types' },
  { value: 'earning', label: 'Earnings' },
  { value: 'withdrawal', label: 'Withdrawals' },
  { value: 'refund', label: 'Refunds' },
  { value: 'bonus', label: 'Bonuses' },
  { value: 'fee', label: 'Fees' },
];

export default function TransactionsPage() {
  const [filters, setFilters] = useState<TransactionFilters>({
    page: 1,
    page_size: 20,
  });

  const { data: transactions, isLoading } = useTransactions(filters);

  const handleTypeChange = (type: TransactionType | '') => {
    setFilters((prev) => ({
      ...prev,
      type: type || undefined,
      page: 1,
    }));
  };

  const handleDateChange = (field: 'from_date' | 'to_date', value: string) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value || undefined,
      page: 1,
    }));
  };

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button asChild variant="ghost" size="icon">
          <Link href="/wallet">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Transaction History
          </h1>
          <p className="text-slate-500">View all your wallet transactions</p>
        </div>
      </div>

      <Card>
        <CardHeader className="flex-col sm:flex-row gap-4">
          <CardTitle className="flex-shrink-0">Transactions</CardTitle>

          <div className="flex flex-wrap items-center gap-3 ml-auto">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={filters.type || ''}
                onChange={(e) => handleTypeChange(e.target.value as TransactionType | '')}
                className="h-10 px-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {transactionTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <Input
                type="date"
                value={filters.from_date || ''}
                onChange={(e) => handleDateChange('from_date', e.target.value)}
                className="w-36"
              />
              <span className="text-slate-400">-</span>
              <Input
                type="date"
                value={filters.to_date || ''}
                onChange={(e) => handleDateChange('to_date', e.target.value)}
                className="w-36"
              />
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800"
                >
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-3 w-48" />
                  </div>
                  <Skeleton className="h-5 w-16" />
                </div>
              ))}
            </div>
          ) : transactions?.items.length === 0 ? (
            <div className="text-center py-12">
              <Wallet className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500 mb-2">No transactions found</p>
              <p className="text-sm text-slate-400">
                {filters.type || filters.from_date || filters.to_date
                  ? 'Try adjusting your filters'
                  : 'Transactions will appear here after your first session'}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {transactions?.items.map((transaction) => (
                <TransactionItem
                  key={transaction.id}
                  transaction={transaction}
                  showDetails
                />
              ))}
            </div>
          )}

          {transactions && transactions.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(transactions.page - 1)}
                disabled={transactions.page <= 1}
              >
                Previous
              </Button>

              <span className="text-sm text-slate-500 px-4">
                Page {transactions.page} of {transactions.total_pages}
              </span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(transactions.page + 1)}
                disabled={transactions.page >= transactions.total_pages}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
