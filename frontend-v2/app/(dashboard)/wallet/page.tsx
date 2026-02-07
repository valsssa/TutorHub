'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  Wallet,
  CreditCard,
  Plus,
  History,
  AlertCircle,
  RefreshCw,
  CheckCircle2,
  ExternalLink,
  TrendingUp,
  DollarSign,
  Clock,
  ArrowDownToLine,
} from 'lucide-react';
import {
  useWalletBalance,
  useCreateWalletCheckout,
  useConnectStatus,
  usePayoutBalance,
  usePayoutHistory,
  useEarningsSummary,
  useCreateConnectAccount,
  useGetDashboardLink,
  walletKeys,
} from '@/lib/hooks/use-wallet';
import { useAuth } from '@/lib/hooks/use-auth';
import { useToast } from '@/lib/stores/ui-store';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Input,
  Skeleton,
  Badge,
} from '@/components/ui';
import { formatCurrency } from '@/lib/utils';
import { useQueryClient } from '@tanstack/react-query';

export default function WalletPage() {
  const [topUpAmount, setTopUpAmount] = useState('');
  const [showTopUpForm, setShowTopUpForm] = useState(false);

  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const toast = useToast();
  const { user } = useAuth();
  const isTutor = user?.role === 'tutor';

  // M45 + M46: Handle Stripe redirect params
  const hasHandledRedirect = useRef(false);

  useEffect(() => {
    if (hasHandledRedirect.current) return;

    const paymentStatus = searchParams.get('payment');
    if (!paymentStatus) return;

    hasHandledRedirect.current = true;

    if (paymentStatus === 'success') {
      toast.success('Payment successful! Your wallet balance has been updated.');
      queryClient.invalidateQueries({ queryKey: walletKeys.balance() });
      queryClient.invalidateQueries({ queryKey: walletKeys.transactions() });
    } else if (paymentStatus === 'cancelled') {
      toast.info('Payment was cancelled. No charges were made.');
    }

    // Clear URL params without a full page reload
    router.replace('/wallet', { scroll: false });
  }, [searchParams, toast, queryClient, router]);

  const { data: balance, isLoading: balanceLoading, error: balanceError, refetch } = useWalletBalance(!isTutor);
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
          <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400">
            {isTutor ? 'Manage your earnings and payouts' : 'Manage your wallet balance'}
          </p>
        </div>
      </div>

      {/* H22: Tutor earnings and payout section */}
      {isTutor && <TutorPayoutSection />}

      {/* Student wallet section (balance + top-up) */}
      {!isTutor && (
        <>
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
                  <div className="flex flex-wrap gap-2">
                    {[10, 25, 50, 100].map((preset) => (
                      <Button
                        key={preset}
                        variant={topUpAmount === String(preset) ? 'primary' : 'outline'}
                        size="sm"
                        onClick={() => setTopUpAmount(String(preset))}
                      >
                        ${preset}
                      </Button>
                    ))}
                  </div>
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
                  <p className="text-slate-500 dark:text-slate-400">
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
        </>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Transaction History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-500 dark:text-slate-400 mb-4">
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

// ---------------------------------------------------------------------------
// H22: Tutor Payout Section
// ---------------------------------------------------------------------------

function TutorPayoutSection() {
  const toast = useToast();
  const {
    data: connectStatus,
    isLoading: statusLoading,
    error: statusError,
  } = useConnectStatus(true);

  const isReady = connectStatus?.is_ready ?? false;

  const {
    data: payoutBalance,
    isLoading: balanceLoading,
  } = usePayoutBalance(isReady);

  const {
    data: earnings,
    isLoading: earningsLoading,
  } = useEarningsSummary(true);

  const {
    data: payoutHistory,
    isLoading: historyLoading,
  } = usePayoutHistory(isReady);

  const createConnect = useCreateConnectAccount();
  const getDashboardLink = useGetDashboardLink();

  const handleSetupConnect = async () => {
    try {
      const result = await createConnect.mutateAsync(undefined);
      if (result.url) {
        window.location.href = result.url;
      }
    } catch {
      toast.error('Failed to start payout setup. Please try again.');
    }
  };

  const handleOpenDashboard = async () => {
    try {
      const result = await getDashboardLink.mutateAsync();
      if (result.url) {
        window.open(result.url, '_blank', 'noopener,noreferrer');
      }
    } catch {
      toast.error(
        'Could not open payout dashboard. Make sure your account setup is complete.'
      );
    }
  };

  // Loading state
  if (statusLoading) {
    return (
      <div className="space-y-4">
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-72" />
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (statusError) {
    return (
      <Card>
        <CardContent className="py-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-red-50 dark:bg-red-900/20 mb-3">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <p className="text-red-600 dark:text-red-400 font-medium mb-2">
              Failed to load payout information
            </p>
            <p className="text-sm text-slate-500">
              {statusError instanceof Error ? statusError.message : 'An error occurred'}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // No Connect account - show setup prompt
  if (!connectStatus?.has_account) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowDownToLine className="h-5 w-5" />
            Set Up Payouts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-slate-500">
              To receive earnings from your tutoring sessions, you need to set up your
              payout account. This is a one-time setup through Stripe.
            </p>
            <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-2">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                Secure identity verification
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                Connect your bank account for direct deposits
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                Automatic payouts after sessions complete
              </li>
            </ul>
            <Button
              className="w-full"
              onClick={handleSetupConnect}
              loading={createConnect.isPending}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Set Up Payout Account
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Account exists but not fully verified
  if (!isReady) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-amber-500" />
            Complete Payout Setup
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
              <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                  Account setup incomplete
                </p>
                <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                  {connectStatus.status_message}
                </p>
              </div>
            </div>
            <Button
              className="w-full"
              onClick={handleSetupConnect}
              loading={createConnect.isPending}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Continue Setup
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Fully set up - show earnings, balance, and payout history
  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Earnings overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card>
          <CardContent className="pt-4 sm:pt-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-green-100 dark:bg-green-900/30 flex-shrink-0">
                <DollarSign className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div className="min-w-0">
                <p className="text-sm text-slate-500 dark:text-slate-400">Available</p>
                {balanceLoading ? (
                  <Skeleton className="h-7 w-20" />
                ) : (
                  <p className="text-xl font-bold text-slate-900 dark:text-white">
                    {formatCurrency(
                      (payoutBalance?.available_cents ?? 0) / 100,
                      payoutBalance?.currency
                    )}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 sm:pt-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-amber-100 dark:bg-amber-900/30 flex-shrink-0">
                <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="min-w-0">
                <p className="text-sm text-slate-500 dark:text-slate-400">Pending</p>
                {balanceLoading ? (
                  <Skeleton className="h-7 w-20" />
                ) : (
                  <p className="text-xl font-bold text-slate-900 dark:text-white">
                    {formatCurrency(
                      (payoutBalance?.pending_cents ?? 0) / 100,
                      payoutBalance?.currency
                    )}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 sm:pt-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex-shrink-0">
                <TrendingUp className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="min-w-0">
                <p className="text-sm text-slate-500 dark:text-slate-400">Net Earnings</p>
                {earningsLoading ? (
                  <Skeleton className="h-7 w-20" />
                ) : (
                  <p className="text-xl font-bold text-slate-900 dark:text-white">
                    {formatCurrency(
                      (earnings?.net_earnings_cents ?? 0) / 100,
                      earnings?.currency
                    )}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4 sm:pt-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-10 w-10 rounded-full bg-purple-100 dark:bg-purple-900/30 flex-shrink-0">
                <Wallet className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="min-w-0">
                <p className="text-sm text-slate-500 dark:text-slate-400">Sessions</p>
                {earningsLoading ? (
                  <Skeleton className="h-7 w-12" />
                ) : (
                  <p className="text-xl font-bold text-slate-900 dark:text-white">
                    {earnings?.total_sessions ?? 0}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Earnings details + manage */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 sm:gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Earnings Summary</CardTitle>
          </CardHeader>
          <CardContent>
            {earningsLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
              </div>
            ) : earnings ? (
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Gross Earnings</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(earnings.gross_earnings_cents / 100, earnings.currency)}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Platform Fees</span>
                  <span className="font-medium text-red-600 dark:text-red-400">
                    -{formatCurrency(earnings.platform_fees_cents / 100, earnings.currency)}
                  </span>
                </div>
                <div className="border-t border-slate-200 dark:border-slate-700 pt-3">
                  <div className="flex justify-between">
                    <span className="font-medium text-slate-700 dark:text-slate-300">
                      Net Earnings
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white">
                      {formatCurrency(earnings.net_earnings_cents / 100, earnings.currency)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="info">{earnings.commission_tier}</Badge>
                  <span className="text-xs text-slate-500">
                    {earnings.current_fee_percentage}% platform fee
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-slate-500 text-sm">No earnings data available.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Manage Payouts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Your earnings are automatically paid out to your bank account. Use the
                Stripe dashboard to manage your payout schedule, bank details, and tax
                information.
              </p>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-800 dark:text-green-300">
                    Payout account active
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-400 mt-0.5">
                    {connectStatus?.payouts_enabled
                      ? 'Payouts are enabled'
                      : 'Charges enabled, payouts processing'}
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                className="w-full"
                onClick={handleOpenDashboard}
                loading={getDashboardLink.isPending}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Open Stripe Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent payouts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Payouts</CardTitle>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center justify-between py-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-20" />
                </div>
              ))}
            </div>
          ) : payoutHistory && payoutHistory.payouts.length > 0 ? (
            <div className="space-y-0 divide-y divide-slate-100 dark:divide-slate-800">
              {payoutHistory.payouts.map((payout) => (
                <div
                  key={payout.id}
                  className="flex items-center justify-between py-3 first:pt-0 last:pb-0"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center h-8 w-8 rounded-full bg-green-100 dark:bg-green-900/30 flex-shrink-0">
                      <ArrowDownToLine className="h-4 w-4 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900 dark:text-white">
                        {formatCurrency(
                          payout.amount_cents / 100,
                          payout.currency?.toUpperCase()
                        )}
                      </p>
                      <p className="text-xs text-slate-500">
                        {payout.arrival_date
                          ? `Arrives ${new Date(payout.arrival_date).toLocaleDateString()}`
                          : new Date(payout.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <PayoutStatusBadge status={payout.status} />
                </div>
              ))}
              {payoutHistory.total_paid_cents > 0 && (
                <div className="pt-3 flex justify-between text-sm">
                  <span className="text-slate-500 dark:text-slate-400">Total Paid Out</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {formatCurrency(
                      payoutHistory.total_paid_cents / 100,
                      payoutHistory.payouts[0]?.currency?.toUpperCase()
                    )}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-slate-500 text-sm">
              No payouts yet. Complete sessions to start earning.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PayoutStatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  if (normalized === 'paid') {
    return <Badge variant="success">Paid</Badge>;
  }
  if (normalized === 'pending') {
    return <Badge variant="warning">Pending</Badge>;
  }
  if (normalized === 'in_transit') {
    return <Badge variant="info">In Transit</Badge>;
  }
  if (normalized === 'failed') {
    return <Badge variant="danger">Failed</Badge>;
  }
  if (normalized === 'canceled') {
    return <Badge variant="default">Cancelled</Badge>;
  }

  return <Badge variant="default">{status}</Badge>;
}
