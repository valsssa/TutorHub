"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { X, Save, CreditCard, Building2, MapPin } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import AppShell from "@/components/AppShell";
import { auth } from "@/lib/api";
import { User } from "@/types";
import LoadingSpinner from "@/components/LoadingSpinner";
import { useToast } from "@/components/ToastContainer";

export default function EditPayoutMethodsPage() {
  return (
    <ProtectedRoute requiredRole="tutor" showNavbar={false}>
      <EditPayoutMethodsContent />
    </ProtectedRoute>
  );
}

function EditPayoutMethodsContent() {
  const router = useRouter();
  const { showSuccess, showError } = useToast();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [payoutForm, setPayoutForm] = useState({
    method: "bank" as "bank" | "paypal" | "stripe",
    accountName: "",
    accountNumber: "",
    routingNumber: "",
    bankName: "",
    address: "",
    city: "",
    state: "",
    zipCode: "",
    country: "US",
    paypalEmail: "",
    stripeAccountId: "",
  });

  useEffect(() => {
    const loadUser = async () => {
      try {
        const currentUser = await auth.getCurrentUser();
        setUser(currentUser);

        // TODO: Load existing payout methods from API
        // For now, use example data
        setPayoutForm((prev) => ({
          ...prev,
          accountName: "John Doe",
          bankName: "Example Bank",
          accountNumber: "****4242",
        }));
      } catch (error) {
        console.error("Failed to load user:", error);
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    };
    loadUser();
  }, [router]);

  const handleSave = async () => {
    setSaving(true);
    try {
      // TODO: Save payout methods via API
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate API call
      
      showSuccess("Payout method updated successfully");
      router.back();
    } catch (error) {
      console.error("Failed to save payout method:", error);
      showError("Failed to save payout method");
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    router.back();
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <AppShell user={user}>
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Edit Payout Method
            </h1>
            <p className="text-slate-500 dark:text-slate-400">
              Manage how you receive your earnings
            </p>
          </div>
          <button
            onClick={handleCancel}
            className="p-2 text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Edit Form */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm p-6 space-y-6">
          {/* Payout Method Selection */}
          <div>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-3">
              Payout Method
            </label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { value: "bank", label: "Bank Account", icon: Building2 },
                { value: "paypal", label: "PayPal", icon: CreditCard },
                { value: "stripe", label: "Stripe", icon: CreditCard },
              ].map((method) => (
                <button
                  key={method.value}
                  onClick={() => setPayoutForm({ ...payoutForm, method: method.value as any })}
                  className={`p-4 border-2 rounded-xl transition-all ${
                    payoutForm.method === method.value
                      ? "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20"
                      : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                  }`}
                >
                  <method.icon
                    size={24}
                    className={`mx-auto mb-2 ${
                      payoutForm.method === method.value
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-slate-400"
                    }`}
                  />
                  <div
                    className={`text-sm font-medium ${
                      payoutForm.method === method.value
                        ? "text-emerald-600 dark:text-emerald-400"
                        : "text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {method.label}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Bank Account Fields */}
          {payoutForm.method === "bank" && (
            <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Account Holder Name
                  </label>
                  <input
                    type="text"
                    value={payoutForm.accountName}
                    onChange={(e) =>
                      setPayoutForm({ ...payoutForm, accountName: e.target.value })
                    }
                    className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="John Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Bank Name
                  </label>
                  <input
                    type="text"
                    value={payoutForm.bankName}
                    onChange={(e) =>
                      setPayoutForm({ ...payoutForm, bankName: e.target.value })
                    }
                    className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="Example Bank"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Account Number
                  </label>
                  <input
                    type="text"
                    value={payoutForm.accountNumber}
                    onChange={(e) =>
                      setPayoutForm({ ...payoutForm, accountNumber: e.target.value })
                    }
                    className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="1234567890"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Routing Number
                  </label>
                  <input
                    type="text"
                    value={payoutForm.routingNumber}
                    onChange={(e) =>
                      setPayoutForm({ ...payoutForm, routingNumber: e.target.value })
                    }
                    className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="123456789"
                  />
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    City
                  </label>
                  <input
                    type="text"
                    value={payoutForm.city}
                    onChange={(e) => setPayoutForm({ ...payoutForm, city: e.target.value })}
                    className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="New York"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    State
                  </label>
                  <input
                    type="text"
                    value={payoutForm.state}
                    onChange={(e) => setPayoutForm({ ...payoutForm, state: e.target.value })}
                    className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="NY"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    ZIP Code
                  </label>
                  <input
                    type="text"
                    value={payoutForm.zipCode}
                    onChange={(e) => setPayoutForm({ ...payoutForm, zipCode: e.target.value })}
                    className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    placeholder="10001"
                  />
                </div>
              </div>
            </div>
          )}

          {/* PayPal Fields */}
          {payoutForm.method === "paypal" && (
            <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                PayPal Email
              </label>
              <input
                type="email"
                value={payoutForm.paypalEmail}
                onChange={(e) =>
                  setPayoutForm({ ...payoutForm, paypalEmail: e.target.value })
                }
                className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="your.email@example.com"
              />
            </div>
          )}

          {/* Stripe Fields */}
          {payoutForm.method === "stripe" && (
            <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Stripe Account ID
              </label>
              <input
                type="text"
                value={payoutForm.stripeAccountId}
                onChange={(e) =>
                  setPayoutForm({ ...payoutForm, stripeAccountId: e.target.value })
                }
                className="w-full p-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="acct_1234567890"
              />
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                Connect your Stripe account to enable instant payouts
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
            <button
              onClick={handleCancel}
              className="flex-1 px-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg shadow-lg shadow-emerald-500/20 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save size={18} />
                  Save Changes
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
