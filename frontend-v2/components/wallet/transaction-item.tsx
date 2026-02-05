'use client';

import {
  ArrowDownLeft,
  ArrowUpRight,
  RotateCcw,
  Minus,
  CreditCard,
  Banknote,
  ArrowLeftRight,
} from 'lucide-react';
import { Badge } from '@/components/ui';
import { formatCurrency, formatDate, formatTime } from '@/lib/utils';
import type { Transaction, TransactionType, TransactionStatus } from '@/types/wallet';

const typeConfig: Record<
  TransactionType,
  { icon: typeof ArrowDownLeft; label: string; colorClass: string }
> = {
  deposit: {
    icon: ArrowDownLeft,
    label: 'Deposit',
    colorClass: 'text-green-600 bg-green-50 dark:bg-green-900/20',
  },
  withdrawal: {
    icon: ArrowUpRight,
    label: 'Withdrawal',
    colorClass: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20',
  },
  refund: {
    icon: RotateCcw,
    label: 'Refund',
    colorClass: 'text-amber-600 bg-amber-50 dark:bg-amber-900/20',
  },
  payout: {
    icon: Banknote,
    label: 'Payout',
    colorClass: 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20',
  },
  payment: {
    icon: CreditCard,
    label: 'Payment',
    colorClass: 'text-slate-600 bg-slate-100 dark:bg-slate-700/50',
  },
  fee: {
    icon: Minus,
    label: 'Fee',
    colorClass: 'text-red-600 bg-red-50 dark:bg-red-900/20',
  },
  transfer: {
    icon: ArrowLeftRight,
    label: 'Transfer',
    colorClass: 'text-purple-600 bg-purple-50 dark:bg-purple-900/20',
  },
};

const statusVariant: Record<TransactionStatus, 'default' | 'success' | 'warning' | 'danger'> = {
  pending: 'warning',
  completed: 'success',
  failed: 'danger',
  cancelled: 'default',
};

interface TransactionItemProps {
  transaction: Transaction;
  showDetails?: boolean;
}

export function TransactionItem({ transaction, showDetails = false }: TransactionItemProps) {
  const config = typeConfig[transaction.type] || typeConfig.payment;
  const Icon = config.icon;

  // Deposits, refunds, and payouts add to balance (positive)
  // Withdrawals, payments, fees subtract from balance (negative)
  const isPositive = ['deposit', 'refund', 'payout'].includes(transaction.type);
  const amountPrefix = isPositive ? '+' : '-';
  const amountColorClass = isPositive
    ? 'text-green-600 dark:text-green-400'
    : 'text-slate-900 dark:text-white';

  return (
    <div className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
      <div
        className={`flex items-center justify-center h-10 w-10 rounded-full ${config.colorClass}`}
      >
        <Icon className="h-5 w-5" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-900 dark:text-white">
            {config.label}
          </span>
          <Badge variant={statusVariant[transaction.status]} className="text-xs">
            {transaction.status}
          </Badge>
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400 truncate">
          {transaction.description}
        </p>
        {showDetails && (
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            {formatDate(transaction.created_at)} at {formatTime(transaction.created_at)}
          </p>
        )}
      </div>

      <div className="text-right">
        <p className={`font-semibold ${amountColorClass}`}>
          {amountPrefix}{formatCurrency(Math.abs(transaction.amount), transaction.currency)}
        </p>
        {!showDetails && (
          <p className="text-xs text-slate-400 dark:text-slate-500">
            {formatDate(transaction.created_at, { month: 'short', day: 'numeric' })}
          </p>
        )}
      </div>
    </div>
  );
}
