'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Wallet,
  CreditCard,
  Plus,
  History,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import {
  useWalletBalance,
  useCreateWalletCheckout,
} from '@/lib/hooks/use-wallet';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Input,
  Skeleton,
} from '@/components/ui';
import { formatCurrency } from '@/lib/utils';

export default function WalletPage() {
  const [topUpAmount, setTopUpAmount] = useState('');
  const [showTopUpForm, setShowTopUpForm] = useState(false);

  const { data: balance, isLoading: balanceLoading, error: balanceError, refetch } = useWalletBalance();
  const createCheckout = useCreateWalletCheckout();

  const handleTopUp = async () => {
    const amount = parseFloat(topUpAmount);
    if (!amount || amount <= 0) {
      return;
    }

    try {
      const result = await createCheckout.mutateAsync({
        amount_cents: Math.round(amount * 100),
        currency: balance?.currency || 'USD',
      });
      // Redirect to Stripe checkout
      if (result.checkout_url) {
        window.location.href = result.checkout_url;
      }
    } catch {
      // Error handling is done by react-query
    }
  };

  // Balance from backend is in cents
  const balanceAmount = balance?.balance_cents ? balance.balance_cents / 100 : 0;

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">
            Wallet
          </h1>
          <p className="text-sm sm:text-base text-slate-500">Manage your wallet balance</p>
        </div>
      </div>

      {balanceError ? (
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-red-50 dark:bg-red-900/20 mb-3">
                <AlertCircle className="h-6 w-6 text-red-500" />
              </div>
              <p className="text-red-600 dark:text-red-400 font-medium mb-2">
                Failed to load wallet balance
              </p>
              <p className="text-sm text-slate-500 mb-4">
                {balanceError instanceof Error ? balanceError.message : 'An error occurred'}
              </p>
              <Button variant="outline" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
          <Card>
            <CardContent className="pt-4 sm:pt-6">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-green-100 dark:bg-green-900/30 flex-shrink-0">
                  <Wallet className="h-5 w-5 sm:h-6 sm:w-6 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Balance
                  </p>
                  {balanceLoading ? (
                    <Skeleton className="h-8 w-24" />
                  ) : (
                    <p
                      className="text-2xl font-bold text-slate-900 dark:text-white"
                      data-testid="balance"
                    >
                      {formatCurrency(balanceAmount, balance?.currency)}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4 sm:pt-6">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-blue-100 dark:bg-blue-900/30 flex-shrink-0">
                  <CreditCard className="h-5 w-5 sm:h-6 sm:w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    Currency
                  </p>
                  {balanceLoading ? (
                    <Skeleton className="h-8 w-24" />
                  ) : (
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">
                      {balance?.currency || 'USD'}
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Top Up Wallet</CardTitle>
        </CardHeader>
        <CardContent>
          {showTopUpForm ? (
            <div className="space-y-4">
              <Input
                type="number"
                label="Amount"
                value={topUpAmount}
                onChange={(e) => setTopUpAmount(e.target.value)}
                placeholder="0.00"
                min="1"
                step="0.01"
              />

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowTopUpForm(false)}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleTopUp}
                  loading={createCheckout.isPending}
                  disabled={!topUpAmount || parseFloat(topUpAmount) <= 0}
                >
                  Continue to Payment
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-slate-500">
                Add funds to your wallet to book sessions.
              </p>
              <Button
                className="w-full"
                onClick={() => setShowTopUpForm(true)}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Funds
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-500 mb-4">
            View your complete transaction history including deposits, withdrawals, and payments.
          </p>
          <Button asChild variant="outline" className="w-full">
            <Link href="/wallet/transactions">
              <History className="h-4 w-4 mr-2" />
              View Transaction History
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
