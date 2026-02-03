'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  Wallet,
  ArrowUpRight,
  Clock,
  TrendingUp,
  ChevronRight,
  AlertCircle,
  CreditCard,
} from 'lucide-react';
import {
  useWalletBalance,
  useTransactions,
  usePaymentMethods,
  useRequestWithdrawal,
} from '@/lib/hooks/use-wallet';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  Button,
  Input,
  Skeleton,
} from '@/components/ui';
import { TransactionItem } from '@/components/wallet';
import { formatCurrency } from '@/lib/utils';

export default function WalletPage() {
  const [withdrawAmount, setWithdrawAmount] = useState('');
  const [showWithdrawForm, setShowWithdrawForm] = useState(false);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<number | null>(null);

  const { data: balance, isLoading: balanceLoading } = useWalletBalance();
  const { data: transactions, isLoading: transactionsLoading } = useTransactions({
    page_size: 5,
  });
  const { data: paymentMethods, isLoading: paymentMethodsLoading } = usePaymentMethods();

  const withdrawMutation = useRequestWithdrawal();

  const defaultPaymentMethod = paymentMethods?.find((pm) => pm.is_default);

  const handleWithdraw = async () => {
    const amount = parseFloat(withdrawAmount);
    const methodId = selectedPaymentMethod || defaultPaymentMethod?.id;

    if (!amount || amount <= 0 || !methodId) {
      return;
    }

    try {
      await withdrawMutation.mutateAsync({
        amount,
        payment_method_id: methodId,
      });
      setWithdrawAmount('');
      setShowWithdrawForm(false);
    } catch {
      // Error handling is done by react-query
    }
  };

  const canWithdraw =
    balance &&
    balance.available > 0 &&
    paymentMethods &&
    paymentMethods.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Wallet
          </h1>
          <p className="text-slate-500">Manage your earnings and withdrawals</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-12 w-12 rounded-full bg-green-100 dark:bg-green-900/30">
                <Wallet className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Available Balance
                </p>
                {balanceLoading ? (
                  <Skeleton className="h-8 w-24" />
                ) : (
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {formatCurrency(balance?.available ?? 0, balance?.currency)}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-12 w-12 rounded-full bg-amber-100 dark:bg-amber-900/30">
                <Clock className="h-6 w-6 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Pending
                </p>
                {balanceLoading ? (
                  <Skeleton className="h-8 w-24" />
                ) : (
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {formatCurrency(balance?.pending ?? 0, balance?.currency)}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900/30">
                <TrendingUp className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Total Earned
                </p>
                {balanceLoading ? (
                  <Skeleton className="h-8 w-24" />
                ) : (
                  <p className="text-2xl font-bold text-slate-900 dark:text-white">
                    {formatCurrency(balance?.total ?? 0, balance?.currency)}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              {transactionsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-slate-800">
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
                <div className="text-center py-8">
                  <Wallet className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No transactions yet</p>
                  <p className="text-sm text-slate-400">
                    Complete sessions to start earning
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {transactions?.items.map((transaction) => (
                    <TransactionItem key={transaction.id} transaction={transaction} />
                  ))}
                </div>
              )}
            </CardContent>
            {transactions && transactions.items.length > 0 && (
              <CardFooter className="justify-center">
                <Button asChild variant="ghost" size="sm">
                  <Link href="/wallet/transactions">
                    View All Transactions
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Link>
                </Button>
              </CardFooter>
            )}
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Withdraw Funds</CardTitle>
            </CardHeader>
            <CardContent>
              {!canWithdraw ? (
                <div className="text-center py-4">
                  <AlertCircle className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                  {!paymentMethods || paymentMethods.length === 0 ? (
                    <>
                      <p className="text-slate-500 mb-2">No payment method</p>
                      <p className="text-sm text-slate-400">
                        Add a payment method to withdraw funds
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="text-slate-500 mb-2">No funds available</p>
                      <p className="text-sm text-slate-400">
                        Complete sessions to earn money
                      </p>
                    </>
                  )}
                </div>
              ) : showWithdrawForm ? (
                <div className="space-y-4">
                  <Input
                    type="number"
                    label="Amount"
                    value={withdrawAmount}
                    onChange={(e) => setWithdrawAmount(e.target.value)}
                    placeholder="0.00"
                    min="0"
                    max={balance?.available}
                    step="0.01"
                  />

                  <div>
                    <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2 block">
                      Withdraw to
                    </label>
                    <div className="space-y-2">
                      {paymentMethods?.map((method) => (
                        <button
                          key={method.id}
                          type="button"
                          onClick={() => setSelectedPaymentMethod(method.id)}
                          className={`w-full flex items-center gap-3 p-3 rounded-xl border-2 transition-colors ${
                            (selectedPaymentMethod || defaultPaymentMethod?.id) === method.id
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                              : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'
                          }`}
                        >
                          <CreditCard className="h-5 w-5 text-slate-400" />
                          <div className="text-left">
                            <p className="text-sm font-medium text-slate-900 dark:text-white">
                              {method.name}
                            </p>
                            {method.last_four && (
                              <p className="text-xs text-slate-500">
                                ****{method.last_four}
                              </p>
                            )}
                          </div>
                          {method.is_default && (
                            <span className="ml-auto text-xs text-primary-600">Default</span>
                          )}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => setShowWithdrawForm(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      className="flex-1"
                      onClick={handleWithdraw}
                      loading={withdrawMutation.isPending}
                      disabled={!withdrawAmount || parseFloat(withdrawAmount) <= 0}
                    >
                      Withdraw
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                    <span className="text-sm text-slate-600 dark:text-slate-400">
                      Available to withdraw
                    </span>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {formatCurrency(balance?.available ?? 0, balance?.currency)}
                    </span>
                  </div>

                  {defaultPaymentMethod && (
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <CreditCard className="h-4 w-4" />
                      <span>
                        To {defaultPaymentMethod.name}
                        {defaultPaymentMethod.last_four && ` (****${defaultPaymentMethod.last_four})`}
                      </span>
                    </div>
                  )}

                  <Button
                    className="w-full"
                    onClick={() => setShowWithdrawForm(true)}
                  >
                    <ArrowUpRight className="h-4 w-4 mr-2" />
                    Withdraw Funds
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Payment Methods</CardTitle>
            </CardHeader>
            <CardContent>
              {paymentMethodsLoading ? (
                <div className="space-y-3">
                  {[1, 2].map((i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800">
                      <Skeleton className="h-8 w-8 rounded" />
                      <div className="flex-1 space-y-1">
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-3 w-16" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : !paymentMethods || paymentMethods.length === 0 ? (
                <div className="text-center py-4">
                  <CreditCard className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 mb-2">No payment methods</p>
                  <p className="text-sm text-slate-400 mb-4">
                    Add a bank account or PayPal
                  </p>
                  <Button variant="outline" size="sm">
                    Add Payment Method
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {paymentMethods.map((method) => (
                    <div
                      key={method.id}
                      className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-slate-800"
                    >
                      <CreditCard className="h-5 w-5 text-slate-400" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                          {method.name}
                        </p>
                        {method.last_four && (
                          <p className="text-xs text-slate-500">****{method.last_four}</p>
                        )}
                      </div>
                      {method.is_default && (
                        <span className="text-xs text-primary-600 font-medium">Default</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
