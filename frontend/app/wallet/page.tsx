"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { 
  FiDollarSign, 
  FiCreditCard, 
  FiCheck, 
  FiClock, 
  FiArrowRight,
  FiInfo,
  FiShield,
  FiTrendingUp
} from "react-icons/fi";
import ProtectedRoute from "@/components/ProtectedRoute";
import { auth, students, wallet } from "@/lib/api";
import { User, StudentProfile } from "@/types";
import { useToast } from "@/components/ToastContainer";
import LoadingSpinner from "@/components/LoadingSpinner";
import Button from "@/components/Button";
import AppShell from "@/components/AppShell";

export default function WalletPage() {
  return (
    <ProtectedRoute showNavbar={false}>
      <WalletContent />
    </ProtectedRoute>
  );
}

function WalletContent() {
  const router = useRouter();
  const { showSuccess, showError, showInfo } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [studentProfile, setStudentProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customAmount, setCustomAmount] = useState<string>("");
  const [processing, setProcessing] = useState(false);

  // Predefined top-up amounts
  const topUpOptions = [10, 25, 50, 100, 200, 500];

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    try {
      const [currentUser, profile, balanceData] = await Promise.all([
        auth.getCurrentUser(),
        students.getProfile(),
        wallet.getBalance().catch(() => null), // Balance is optional, don't fail if unavailable
      ]);

      setUser(currentUser);
      setStudentProfile(profile);

      // Update balance from wallet API if available
      if (balanceData && profile) {
        profile.credit_balance_cents = balanceData.balance_cents;
        setStudentProfile({ ...profile });
      }
    } catch (error) {
      showError("Failed to load wallet data");
    } finally {
      setLoading(false);
    }
  };

  const handleAmountSelect = (amount: number) => {
    setSelectedAmount(amount);
    setCustomAmount("");
  };

  const handleCustomAmountChange = (value: string) => {
    // Only allow numbers and decimal point
    const filtered = value.replace(/[^0-9.]/g, '');
    
    // Prevent multiple decimal points
    const parts = filtered.split('.');
    if (parts.length > 2) return;
    
    // Limit to 2 decimal places
    if (parts[1] && parts[1].length > 2) return;
    
    setCustomAmount(filtered);
    
    // Update selected amount if valid
    const numValue = parseFloat(filtered);
    if (!isNaN(numValue) && numValue > 0) {
      setSelectedAmount(numValue);
    } else {
      setSelectedAmount(null);
    }
  };

  const handleTopUp = async () => {
    if (!selectedAmount || selectedAmount <= 0) {
      showError("Please select or enter a valid amount");
      return;
    }

    if (selectedAmount < 5) {
      showError("Minimum top-up amount is $5");
      return;
    }

    if (selectedAmount > 10000) {
      showError("Maximum top-up amount is $10,000");
      return;
    }

    setProcessing(true);

    try {
      // Create Stripe checkout session using typed API
      const response = await wallet.checkout(
        Math.round(selectedAmount * 100),
        user?.currency || 'USD'
      );

      // Redirect to Stripe Checkout
      if (response.checkout_url) {
        window.location.href = response.checkout_url;
      } else {
        throw new Error('No checkout URL received');
      }

    } catch (error: any) {
      showError(error.response?.data?.detail || "Payment processing failed");
      setProcessing(false);
    }
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner />
      </div>
    );
  }

  const balance = studentProfile?.credit_balance_cents 
    ? (studentProfile.credit_balance_cents / 100).toFixed(2) 
    : "0.00";

  return (
    <AppShell user={user}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-emerald-600 via-teal-500 to-green-600 rounded-2xl shadow-lg p-6 md:p-8 text-white"
        >
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">
                Wallet 💰
              </h1>
              <p className="text-white/90">
                Manage your credits and top up your balance
              </p>
            </div>
            <div className="bg-white/20 backdrop-blur-sm rounded-xl px-6 py-4 text-center">
              <p className="text-white/80 text-sm mb-1">Current Balance</p>
              <p className="text-3xl font-bold">${balance}</p>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top Up Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 bg-white rounded-2xl shadow-lg p-6 space-y-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
                <FiDollarSign className="w-6 h-6 text-emerald-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-900">Top Up Balance</h2>
            </div>

            {/* Quick Amount Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Amount
              </label>
              <div className="grid grid-cols-3 gap-3">
                {topUpOptions.map((amount) => (
                  <button
                    key={amount}
                    onClick={() => handleAmountSelect(amount)}
                    className={`p-4 rounded-xl border-2 transition-all font-semibold ${
                      selectedAmount === amount && !customAmount
                        ? "border-emerald-500 bg-emerald-50 text-emerald-700 shadow-md"
                        : "border-gray-200 hover:border-emerald-300 text-gray-700 hover:bg-emerald-50"
                    }`}
                  >
                    ${amount}
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Amount */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Or Enter Custom Amount
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-lg font-semibold">
                  $
                </span>
                <input
                  type="text"
                  value={customAmount}
                  onChange={(e) => handleCustomAmountChange(e.target.value)}
                  placeholder="0.00"
                  className="w-full pl-10 pr-4 py-3 text-lg border-2 border-gray-200 rounded-xl focus:border-emerald-500 focus:outline-none transition-colors"
                />
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Minimum: $5.00 • Maximum: $10,000.00
              </p>
            </div>

            {/* Payment Method Placeholder */}
            <div className="bg-gradient-to-br from-slate-50 to-gray-50 rounded-xl p-4 border border-gray-200">
              <div className="flex items-start gap-3">
                <FiCreditCard className="w-5 h-5 text-gray-600 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold text-gray-900 mb-1">Payment Method</p>
                  <p className="text-sm text-gray-600">
                    Secure payment processing with Stripe (coming soon)
                  </p>
                </div>
                <FiShield className="w-5 h-5 text-emerald-600" />
              </div>
            </div>

            {/* Action Button */}
            <Button
              variant="primary"
              size="lg"
              onClick={handleTopUp}
              disabled={!selectedAmount || selectedAmount <= 0 || processing}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 disabled:from-gray-300 disabled:to-gray-400 shadow-lg text-lg"
            >
              {processing ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Processing...
                </span>
              ) : selectedAmount ? (
                <span className="flex items-center justify-center gap-2">
                  Add ${selectedAmount.toFixed(2)} <FiArrowRight />
                </span>
              ) : (
                "Select Amount to Continue"
              )}
            </Button>
          </motion.div>

          {/* Info Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* Benefits */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
                  <FiTrendingUp className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">Why Top Up?</h3>
              </div>
              <ul className="space-y-3">
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <FiCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Instant booking without payment delays</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <FiCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Never miss a session due to payment issues</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <FiCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Track your learning budget in one place</span>
                </li>
                <li className="flex items-start gap-2 text-sm text-gray-700">
                  <FiCheck className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Secure and encrypted payments</span>
                </li>
              </ul>
            </div>

            {/* Security Note */}
            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl shadow-sm p-6 border border-emerald-200">
              <div className="flex items-start gap-3">
                <FiShield className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="font-bold text-emerald-900 mb-2">Secure & Safe</h4>
                  <p className="text-sm text-emerald-800">
                    All transactions are encrypted and processed securely. 
                    We never store your full payment details.
                  </p>
                </div>
              </div>
            </div>

            {/* Transaction History Placeholder */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
                  <FiClock className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">Recent Activity</h3>
              </div>
              <div className="text-center py-8">
                <FiInfo className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-sm text-gray-500">
                  Transaction history will appear here
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </AppShell>
  );
}
